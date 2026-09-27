"""
Core content: posts (normal + anonymous "tea"), comments, reactions, polls,
reels and stories.
"""
import enum
from datetime import datetime, timezone, timedelta

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TeaCategory(str, enum.Enum):
    TRENDING = "trending"
    FUNNY = "funny"
    CONFESSION = "confession"
    RELATIONSHIPS = "relationships"
    ACADEMIC = "academic"
    CAMPUS = "campus"
    EVENTS = "events"
    FOOD = "food"
    SPORTS = "sports"
    QUESTIONS = "questions"


class Post(Base):
    """A normal (attributed) post or an anonymous 'tea' post."""
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    campus_id: Mapped[int | None] = mapped_column(ForeignKey("campuses.id"), nullable=True)

    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    category: Mapped[TeaCategory | None] = mapped_column(Enum(TeaCategory), nullable=True)

    text: Mapped[str] = mapped_column(String(2000), nullable=False)

    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    is_removed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    author: Mapped["User"] = relationship()
    media: Mapped[list["PostMedia"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    poll: Mapped["Poll"] = relationship(back_populates="post", uselist=False, cascade="all, delete-orphan")

    # Reactions use a generic (target_type, target_id) polymorphic association
    # (see Reaction below) rather than a direct FK relationship, so they are
    # queried explicitly in the routers instead of via `.reactions`.


class PostMedia(Base):
    __tablename__ = "post_media"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    media_type: Mapped[str] = mapped_column(String(20), default="image")  # image | video

    post: Mapped["Post"] = relationship(back_populates="media")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int | None] = mapped_column(ForeignKey("posts.id"), nullable=True)
    reel_id: Mapped[int | None] = mapped_column(ForeignKey("reels.id"), nullable=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("comments.id"), nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    text: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_removed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    author: Mapped["User"] = relationship()
    post: Mapped["Post"] = relationship(back_populates="comments")
    replies: Mapped[list["Comment"]] = relationship()


class Reaction(Base):
    """Generic reaction, reusable across posts, comments and reels via target_type/target_id."""
    __tablename__ = "reactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)  # post | comment | reel | story
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    reaction_type: Mapped[str] = mapped_column(String(20), default="like")  # like, laugh, love, fire, sad
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Poll(Base):
    __tablename__ = "polls"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), unique=True, nullable=False)
    question: Mapped[str] = mapped_column(String(300), nullable=False)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=True)

    post: Mapped["Post"] = relationship(back_populates="poll")
    options: Mapped[list["PollOption"]] = relationship(back_populates="poll", cascade="all, delete-orphan")


class PollOption(Base):
    __tablename__ = "poll_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    poll_id: Mapped[int] = mapped_column(ForeignKey("polls.id"), nullable=False)
    text: Mapped[str] = mapped_column(String(150), nullable=False)

    poll: Mapped["Poll"] = relationship(back_populates="options")
    votes: Mapped[list["PollVote"]] = relationship(back_populates="option", cascade="all, delete-orphan")


class PollVote(Base):
    __tablename__ = "poll_votes"

    id: Mapped[int] = mapped_column(primary_key=True)
    option_id: Mapped[int] = mapped_column(ForeignKey("poll_options.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    option: Mapped["PollOption"] = relationship(back_populates="votes")


class Reel(Base):
    """
    Short-video metadata. Video storage/serving is intentionally simple
    (upload -> static file -> <video> tag) rather than a full transcoding
    pipeline, which would be disproportionate for a B.Tech project.
    """
    __tablename__ = "reels"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    campus_id: Mapped[int | None] = mapped_column(ForeignKey("campuses.id"), nullable=True)
    video_url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    caption: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    hashtags: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    is_removed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    author: Mapped["User"] = relationship()


class Story(Base):
    __tablename__ = "stories"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    media_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    story_type: Mapped[str] = mapped_column(String(20), default="image")  # image | video | text | poll
    text_content: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc) + timedelta(hours=24)
    )

    author: Mapped["User"] = relationship()
    views: Mapped[list["StoryView"]] = relationship(back_populates="story", cascade="all, delete-orphan")


class StoryView(Base):
    __tablename__ = "story_views"

    id: Mapped[int] = mapped_column(primary_key=True)
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id"), nullable=False)
    viewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    viewed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    story: Mapped["Story"] = relationship(back_populates="views")
