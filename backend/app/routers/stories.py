from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.deps import get_current_user
from app.models.user import User
from app.models.content import Story, StoryView
from app.schemas.content import StoryCreate, StoryOut

router = APIRouter(prefix="/api/stories", tags=["stories"])


def _story_out(story: Story, db: Session, viewer_id: int) -> StoryOut:
    return StoryOut(
        id=story.id,
        author_username=story.author.username,
        story_type=story.story_type,
        media_url=story.media_url,
        text_content=story.text_content,
        created_at=story.created_at,
        expires_at=story.expires_at,
        view_count=db.query(StoryView).filter_by(story_id=story.id).count(),
        viewed_by_me=db.query(StoryView).filter_by(story_id=story.id, viewer_id=viewer_id).first() is not None,
    )


@router.post("", response_model=StoryOut, status_code=201)
def create_story(payload: StoryCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    story = Story(
        author_id=current_user.id,
        story_type=payload.story_type,
        media_url=payload.media_url,
        text_content=payload.text_content,
    )
    db.add(story)
    db.commit()
    db.refresh(story)
    return _story_out(story, db, current_user.id)


@router.get("", response_model=list[StoryOut])
def list_active_stories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    stories = db.query(Story).filter(Story.expires_at > now).order_by(Story.created_at.desc()).all()
    return [_story_out(s, db, current_user.id) for s in stories]


@router.post("/{story_id}/view", status_code=201)
def view_story(story_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    story = db.get(Story, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    if not db.query(StoryView).filter_by(story_id=story_id, viewer_id=current_user.id).first():
        db.add(StoryView(story_id=story_id, viewer_id=current_user.id))
        db.commit()
    return {"viewed": True}
