from datetime import datetime

from pydantic import BaseModel


class CommunityCreate(BaseModel):
    name: str
    description: str | None = None
    category: str = "general"
    campus_id: int | None = None


class CommunityOut(BaseModel):
    id: int
    name: str
    description: str | None
    category: str
    member_count: int
    is_member: bool = False


class RoomCreate(BaseModel):
    title: str
    topic: str = "general"
    campus_id: int | None = None


class RoomOut(BaseModel):
    id: int
    title: str
    topic: str
    member_count: int
    is_active: bool
    created_at: datetime


class RoomMessageCreate(BaseModel):
    text: str
    is_anonymous: bool = False


class RoomMessageOut(BaseModel):
    id: int
    author_display: str
    text: str
    created_at: datetime


class MatchCandidateOut(BaseModel):
    match_id: int
    user_id: int
    username: str
    full_name: str
    bio: str | None
    avatar_url: str | None
    score_percent: int
    score_breakdown: dict


class MatchDecision(BaseModel):
    decision: str  # connect | skip | report | block


class ConnectionOut(BaseModel):
    id: int
    requester_id: int
    addressee_id: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    text: str | None = None
    image_url: str | None = None


class MessageOut(BaseModel):
    id: int
    sender_id: int
    text: str | None
    image_url: str | None
    created_at: datetime
    is_read: bool

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: int
    is_group: bool
    title: str | None
    other_participant_id: int | None = None
    other_participant_username: str | None = None
    last_message: str | None = None
    updated_at: datetime | None = None
