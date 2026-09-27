"""
Temporary campus rooms (text-based). Architecture leaves room for audio/video
to be layered in later (see docs/FUTURE_SCOPE.md); for the B.Tech scope,
messages are plain polled/refetched text, no WebSocket server required.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.deps import get_current_user
from app.models.user import User
from app.models.social import Room, RoomMember, RoomMessage
from app.schemas.social import RoomCreate, RoomOut, RoomMessageCreate, RoomMessageOut
from app.security.sanitize import sanitize_text

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


def _room_out(room: Room, db: Session) -> RoomOut:
    return RoomOut(
        id=room.id, title=room.title, topic=room.topic,
        member_count=db.query(RoomMember).filter_by(room_id=room.id).count(),
        is_active=room.is_active, created_at=room.created_at,
    )


@router.post("", response_model=RoomOut, status_code=201)
def create_room(payload: RoomCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    room = Room(
        title=sanitize_text(payload.title), topic=payload.topic,
        campus_id=payload.campus_id or current_user.campus_id, created_by=current_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=6),
    )
    db.add(room)
    db.flush()
    db.add(RoomMember(room_id=room.id, user_id=current_user.id))
    db.commit()
    db.refresh(room)
    return _room_out(room, db)


@router.get("", response_model=list[RoomOut])
def list_rooms(campus_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Room).filter(Room.is_active == True)  # noqa: E712
    if campus_id:
        query = query.filter(Room.campus_id == campus_id)
    return [_room_out(r, db) for r in query.order_by(Room.created_at.desc()).all()]


@router.post("/{room_id}/join", status_code=201)
def join_room(room_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    room = db.get(Room, room_id)
    if not room or not room.is_active:
        raise HTTPException(status_code=404, detail="Room not found")
    if not db.query(RoomMember).filter_by(room_id=room_id, user_id=current_user.id).first():
        db.add(RoomMember(room_id=room_id, user_id=current_user.id))
        db.commit()
    return {"joined": True}


@router.post("/{room_id}/messages", response_model=RoomMessageOut, status_code=201)
def send_room_message(room_id: int, payload: RoomMessageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    room = db.get(Room, room_id)
    if not room or not room.is_active:
        raise HTTPException(status_code=404, detail="Room not found")
    msg = RoomMessage(room_id=room_id, user_id=current_user.id, is_anonymous=payload.is_anonymous, text=sanitize_text(payload.text))
    db.add(msg)
    db.commit()
    db.refresh(msg)
    display = current_user.username
    if payload.is_anonymous:
        display = current_user.anonymous_profile.display_name
    return RoomMessageOut(id=msg.id, author_display=display, text=msg.text, created_at=msg.created_at)


@router.get("/{room_id}/messages", response_model=list[RoomMessageOut])
def list_room_messages(room_id: int, db: Session = Depends(get_db)):
    messages = db.query(RoomMessage).filter_by(room_id=room_id).order_by(RoomMessage.created_at.asc()).all()
    out = []
    for m in messages:
        display = m.user.anonymous_profile.display_name if m.is_anonymous else m.user.username
        out.append(RoomMessageOut(id=m.id, author_display=display, text=m.text, created_at=m.created_at))
    return out
