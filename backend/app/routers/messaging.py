from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.database import get_db
from app.auth.deps import get_current_user
from app.models.user import User, Block
from app.models.social import Conversation, ConversationParticipant, Message
from app.schemas.social import MessageCreate, MessageOut, ConversationOut
from app.security.sanitize import sanitize_text

router = APIRouter(prefix="/api/messages", tags=["messaging"])


def _get_or_create_dm(db: Session, user_a: int, user_b: int) -> Conversation:
    existing = (
        db.query(Conversation)
        .join(ConversationParticipant)
        .filter(Conversation.is_group == False, ConversationParticipant.user_id.in_([user_a, user_b]))  # noqa: E712
        .group_by(Conversation.id)
        .having(func.count(ConversationParticipant.id) == 2)
        .all()
    )
    for conv in existing:
        participant_ids = {p.user_id for p in conv.participants}
        if participant_ids == {user_a, user_b}:
            return conv

    conv = Conversation(is_group=False)
    db.add(conv)
    db.flush()
    db.add(ConversationParticipant(conversation_id=conv.id, user_id=user_a))
    db.add(ConversationParticipant(conversation_id=conv.id, user_id=user_b))
    db.commit()
    db.refresh(conv)
    return conv


@router.post("/dm/{other_user_id}", response_model=MessageOut, status_code=201)
def send_direct_message(other_user_id: int, payload: MessageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if other_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot message yourself")
    other = db.get(User, other_user_id)
    if not other:
        raise HTTPException(status_code=404, detail="User not found")

    blocked = db.query(Block).filter(
        or_(
            and_(Block.blocker_id == current_user.id, Block.blocked_id == other_user_id),
            and_(Block.blocker_id == other_user_id, Block.blocked_id == current_user.id),
        )
    ).first()
    if blocked:
        raise HTTPException(status_code=403, detail="Messaging is blocked between these users")

    if not payload.text and not payload.image_url:
        raise HTTPException(status_code=400, detail="Message must contain text or an image")

    conv = _get_or_create_dm(db, current_user.id, other_user_id)
    message = Message(
        conversation_id=conv.id, sender_id=current_user.id,
        text=sanitize_text(payload.text) if payload.text else None,
        image_url=payload.image_url,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return MessageOut.model_validate(message)


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    my_conv_ids = [p.conversation_id for p in db.query(ConversationParticipant).filter_by(user_id=current_user.id).all()]
    conversations = db.query(Conversation).filter(Conversation.id.in_(my_conv_ids)).all()

    out = []
    for conv in conversations:
        other_username = None
        other_id = None
        if not conv.is_group:
            others = [p.user_id for p in conv.participants if p.user_id != current_user.id]
            if others:
                other_user = db.get(User, others[0])
                other_username = other_user.username if other_user else None
                other_id = others[0]
        last_msg = db.query(Message).filter_by(conversation_id=conv.id).order_by(Message.created_at.desc()).first()
        out.append(ConversationOut(
            id=conv.id, is_group=conv.is_group, title=conv.title,
            other_participant_id=other_id,
            other_participant_username=other_username,
            last_message=last_msg.text if last_msg else None,
            updated_at=last_msg.created_at if last_msg else conv.created_at,
        ))
    return out


@router.get("/conversations/{conversation_id}", response_model=list[MessageOut])
def get_conversation_messages(conversation_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    is_participant = db.query(ConversationParticipant).filter_by(conversation_id=conversation_id, user_id=current_user.id).first()
    if not is_participant:
        raise HTTPException(status_code=403, detail="Not a participant of this conversation")
    messages = db.query(Message).filter_by(conversation_id=conversation_id).order_by(Message.created_at.asc()).all()
    return [MessageOut.model_validate(m) for m in messages]


@router.post("/conversations/{conversation_id}", response_model=MessageOut, status_code=201)
def reply_in_conversation(conversation_id: int, payload: MessageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    is_participant = db.query(ConversationParticipant).filter_by(conversation_id=conversation_id, user_id=current_user.id).first()
    if not is_participant:
        raise HTTPException(status_code=403, detail="Not a participant of this conversation")
    if not payload.text and not payload.image_url:
        raise HTTPException(status_code=400, detail="Message must contain text or an image")

    message = Message(
        conversation_id=conversation_id, sender_id=current_user.id,
        text=sanitize_text(payload.text) if payload.text else None,
        image_url=payload.image_url,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return MessageOut.model_validate(message)


@router.get("/lookup/{username}")
def lookup_user_by_username(username: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Minimal public lookup so the Messages UI can start a chat by username."""
    user = db.query(User).filter_by(username=username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "username": user.username, "full_name": user.full_name}
