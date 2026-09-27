from datetime import datetime

from pydantic import BaseModel, field_validator


class PollOptionCreate(BaseModel):
    text: str


class PollCreate(BaseModel):
    question: str
    options: list[str]

    @field_validator("options")
    @classmethod
    def min_options(cls, v: list[str]) -> list[str]:
        if len(v) < 2:
            raise ValueError("A poll needs at least 2 options")
        return v


class PostCreate(BaseModel):
    text: str
    is_anonymous: bool = False
    category: str | None = None
    campus_id: int | None = None
    media_urls: list[str] = []
    poll: PollCreate | None = None

    @field_validator("text")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Post text cannot be empty")
        if len(v) > 2000:
            raise ValueError("Post text too long (max 2000 characters)")
        return v


class AuthorOut(BaseModel):
    display_name: str
    avatar_url: str | None = None
    is_anonymous: bool


class PollOptionResult(BaseModel):
    id: int
    text: str
    votes: int


class PollResult(BaseModel):
    id: int
    question: str
    options: list[PollOptionResult]
    total_votes: int
    user_voted_option_id: int | None = None


class PostOut(BaseModel):
    id: int
    author: AuthorOut
    text: str
    category: str | None
    campus_id: int | None
    media_urls: list[str]
    reaction_count: int
    comment_count: int
    created_at: datetime
    poll: PollResult | None = None
    is_flagged: bool = False


class CommentCreate(BaseModel):
    text: str
    is_anonymous: bool = False
    parent_id: int | None = None

    @field_validator("text")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Comment cannot be empty")
        return v


class CommentOut(BaseModel):
    id: int
    author: AuthorOut
    text: str
    parent_id: int | None
    created_at: datetime


class ReactionCreate(BaseModel):
    target_type: str
    target_id: int
    reaction_type: str = "like"


class ReelCreate(BaseModel):
    video_url: str
    caption: str | None = None
    category: str | None = None
    hashtags: str | None = None
    campus_id: int | None = None


class ReelOut(BaseModel):
    id: int
    author: AuthorOut
    video_url: str
    thumbnail_url: str | None
    caption: str | None
    category: str | None
    hashtags: str | None
    reaction_count: int
    comment_count: int
    created_at: datetime


class StoryCreate(BaseModel):
    story_type: str = "image"
    media_url: str | None = None
    text_content: str | None = None


class StoryOut(BaseModel):
    id: int
    author_username: str
    story_type: str
    media_url: str | None
    text_content: str | None
    created_at: datetime
    expires_at: datetime
    view_count: int
    viewed_by_me: bool = False
