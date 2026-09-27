"""
Posts (normal + anonymous "tea"), comments, reactions and polls.

Anonymous posts store `author_id` internally (so the real owner can edit/
delete their own post and moderators can escalate through the identity-
reveal flow) but the API response only ever exposes the AnonymousProfile's
display name for anonymous content -- never the real username.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.database import get_db
from app.auth.deps import get_current_user
from app.models.user import User
from app.models.content import Post, PostMedia, Comment, Reaction, Poll, PollOption, PollVote, TeaCategory
from app.schemas.content import PostCreate, PostOut, AuthorOut, CommentCreate, CommentOut, ReactionCreate, PollResult, PollOptionResult
from app.security.sanitize import sanitize_text
from app.services.moderation import evaluate_text

router = APIRouter(prefix="/api/posts", tags=["posts"])


def _author_out(post_or_comment, db: Session) -> AuthorOut:
    if post_or_comment.is_anonymous:
        profile = post_or_comment.author.anonymous_profile
        return AuthorOut(display_name=profile.display_name, avatar_url=None, is_anonymous=True)
    author = post_or_comment.author
    return AuthorOut(display_name=author.username, avatar_url=author.avatar_url, is_anonymous=False)


def _poll_result(poll: Poll, db: Session, user_id: int) -> PollResult:
    options = []
    total = 0
    user_voted = None
    for opt in poll.options:
        count = db.query(PollVote).filter_by(option_id=opt.id).count()
        total += count
        if db.query(PollVote).filter_by(option_id=opt.id, user_id=user_id).first():
            user_voted = opt.id
        options.append(PollOptionResult(id=opt.id, text=opt.text, votes=count))
    return PollResult(id=poll.id, question=poll.question, options=options, total_votes=total, user_voted_option_id=user_voted)


def _post_out(post: Post, db: Session, user_id: int) -> PostOut:
    reaction_count = db.query(Reaction).filter_by(target_type="post", target_id=post.id).count()
    comment_count = db.query(Comment).filter_by(post_id=post.id, is_removed=False).count()
    return PostOut(
        id=post.id,
        author=_author_out(post, db),
        text=post.text,
        category=post.category.value if post.category else None,
        campus_id=post.campus_id,
        media_urls=[m.url for m in post.media],
        reaction_count=reaction_count,
        comment_count=comment_count,
        created_at=post.created_at,
        poll=_poll_result(post.poll, db, user_id) if post.poll else None,
        is_flagged=post.is_flagged,
    )


@router.post("", response_model=PostOut, status_code=201)
def create_post(payload: PostCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    category = None
    if payload.category:
        try:
            category = TeaCategory(payload.category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {payload.category}")

    moderation = evaluate_text(payload.text)

    post = Post(
        author_id=current_user.id,
        campus_id=payload.campus_id or current_user.campus_id,
        is_anonymous=payload.is_anonymous,
        category=category,
        text=sanitize_text(payload.text),
        is_flagged=moderation["flagged"],
    )
    db.add(post)
    db.flush()

    for url in payload.media_urls:
        db.add(PostMedia(post_id=post.id, url=url))

    if payload.poll:
        poll = Poll(post_id=post.id, question=sanitize_text(payload.poll.question))
        db.add(poll)
        db.flush()
        for opt_text in payload.poll.options:
            db.add(PollOption(poll_id=poll.id, text=sanitize_text(opt_text)))

    db.commit()
    db.refresh(post)
    return _post_out(post, db, current_user.id)


@router.get("", response_model=list[PostOut])
def list_posts(
    category: str | None = None,
    campus_id: int | None = None,
    tea_only: bool = False,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Post).options(joinedload(Post.media), joinedload(Post.poll).joinedload(Poll.options)).filter(Post.is_removed == False)  # noqa: E712
    if category:
        query = query.filter(Post.category == category)
    if campus_id:
        query = query.filter(Post.campus_id == campus_id)
    if tea_only:
        query = query.filter(Post.is_anonymous == True)  # noqa: E712

    posts = query.order_by(Post.created_at.desc()).offset(offset).limit(limit).all()
    return [_post_out(p, db, current_user.id) for p in posts]


@router.get("/{post_id}", response_model=PostOut)
def get_post(post_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post or post.is_removed:
        raise HTTPException(status_code=404, detail="Post not found")
    return _post_out(post, db, current_user.id)


@router.delete("/{post_id}", status_code=204)
def delete_post(post_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id and current_user.role.value not in ("moderator", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
    post.is_removed = True
    db.commit()
    return None


@router.post("/{post_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(post_id: int, payload: CommentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post or post.is_removed:
        raise HTTPException(status_code=404, detail="Post not found")

    comment = Comment(
        post_id=post_id,
        author_id=current_user.id,
        parent_id=payload.parent_id,
        is_anonymous=payload.is_anonymous,
        text=sanitize_text(payload.text),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return CommentOut(id=comment.id, author=_author_out(comment, db), text=comment.text, parent_id=comment.parent_id, created_at=comment.created_at)


@router.get("/{post_id}/comments", response_model=list[CommentOut])
def list_comments(post_id: int, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter_by(post_id=post_id, is_removed=False).order_by(Comment.created_at.asc()).all()
    return [CommentOut(id=c.id, author=_author_out(c, db), text=c.text, parent_id=c.parent_id, created_at=c.created_at) for c in comments]


@router.post("/reactions", status_code=201)
def add_reaction(payload: ReactionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.target_type not in ("post", "comment", "reel", "story"):
        raise HTTPException(status_code=400, detail="Invalid target_type")

    existing = db.query(Reaction).filter_by(
        user_id=current_user.id, target_type=payload.target_type, target_id=payload.target_id
    ).first()
    if existing:
        db.delete(existing)  # toggle off
        db.commit()
        return {"reacted": False}

    db.add(Reaction(user_id=current_user.id, target_type=payload.target_type, target_id=payload.target_id, reaction_type=payload.reaction_type))
    db.commit()
    return {"reacted": True}


@router.post("/polls/{option_id}/vote", status_code=201)
def vote_poll(option_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    option = db.get(PollOption, option_id)
    if not option:
        raise HTTPException(status_code=404, detail="Poll option not found")

    sibling_ids = [o.id for o in db.query(PollOption).filter_by(poll_id=option.poll_id).all()]
    existing = db.query(PollVote).filter(PollVote.option_id.in_(sibling_ids), PollVote.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already voted in this poll")

    db.add(PollVote(option_id=option_id, user_id=current_user.id))
    db.commit()
    return {"voted": True}
