from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.deps import get_current_user
from app.models.user import User
from app.models.content import Reel, Comment, Reaction
from app.schemas.content import ReelCreate, ReelOut, AuthorOut, CommentCreate, CommentOut
from app.security.sanitize import sanitize_text

router = APIRouter(prefix="/api/reels", tags=["reels"])


def _reel_out(reel: Reel, db: Session) -> ReelOut:
    return ReelOut(
        id=reel.id,
        author=AuthorOut(display_name=reel.author.username, avatar_url=reel.author.avatar_url, is_anonymous=False),
        video_url=reel.video_url,
        thumbnail_url=reel.thumbnail_url,
        caption=reel.caption,
        category=reel.category,
        hashtags=reel.hashtags,
        reaction_count=db.query(Reaction).filter_by(target_type="reel", target_id=reel.id).count(),
        comment_count=db.query(Comment).filter_by(reel_id=reel.id, is_removed=False).count(),
        created_at=reel.created_at,
    )


@router.post("", response_model=ReelOut, status_code=201)
def create_reel(payload: ReelCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reel = Reel(
        author_id=current_user.id,
        campus_id=payload.campus_id or current_user.campus_id,
        video_url=payload.video_url,
        caption=sanitize_text(payload.caption) if payload.caption else None,
        category=payload.category,
        hashtags=payload.hashtags,
    )
    db.add(reel)
    db.commit()
    db.refresh(reel)
    return _reel_out(reel, db)


@router.get("", response_model=list[ReelOut])
def list_reels(category: str | None = None, campus_id: int | None = None, limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    query = db.query(Reel).filter(Reel.is_removed == False)  # noqa: E712
    if category:
        query = query.filter(Reel.category == category)
    if campus_id:
        query = query.filter(Reel.campus_id == campus_id)
    reels = query.order_by(Reel.created_at.desc()).offset(offset).limit(limit).all()
    return [_reel_out(r, db) for r in reels]


@router.delete("/{reel_id}", status_code=204)
def delete_reel(reel_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reel = db.get(Reel, reel_id)
    if not reel:
        raise HTTPException(status_code=404, detail="Reel not found")
    if reel.author_id != current_user.id and current_user.role.value not in ("moderator", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    reel.is_removed = True
    db.commit()
    return None


def _comment_out(comment: Comment) -> CommentOut:
    author = comment.author
    author_out = AuthorOut(display_name=author.username, avatar_url=author.avatar_url, is_anonymous=False)
    if comment.is_anonymous:
        profile = author.anonymous_profile
        author_out = AuthorOut(display_name=profile.display_name, avatar_url=None, is_anonymous=True)
    return CommentOut(id=comment.id, author=author_out, text=comment.text, parent_id=comment.parent_id, created_at=comment.created_at)


@router.post("/{reel_id}/comments", response_model=CommentOut, status_code=201)
def add_reel_comment(reel_id: int, payload: CommentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reel = db.get(Reel, reel_id)
    if not reel or reel.is_removed:
        raise HTTPException(status_code=404, detail="Reel not found")
    comment = Comment(reel_id=reel_id, author_id=current_user.id, parent_id=payload.parent_id, is_anonymous=payload.is_anonymous, text=sanitize_text(payload.text))
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return _comment_out(comment)


@router.get("/{reel_id}/comments", response_model=list[CommentOut])
def list_reel_comments(reel_id: int, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter_by(reel_id=reel_id, is_removed=False).order_by(Comment.created_at.asc()).all()
    return [_comment_out(c) for c in comments]
