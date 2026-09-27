"""
User identity.

Anonymous identity design (see docs/SECURITY.md for the full explanation):

    User (real account, private)
        -> AnonymousProfile (one persistent persona per user, e.g. "Anonymous Fox #4821")
            -> used as the author of anonymous Posts

Only the internal `user_id` foreign key ties the persona back to the real
account. That link is never sent to the frontend for anonymous content; it
is only readable through the moderator "reveal identity" endpoint, which is
itself written to IdentityAccessLog for audit purposes.
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    STUDENT = "student"
    MODERATOR = "moderator"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.STUDENT)

    campus_id: Mapped[int | None] = mapped_column(ForeignKey("campuses.id"), nullable=True)
    branch: Mapped[str | None] = mapped_column(String(100), nullable=True)
    year_of_study: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bio: Mapped[str | None] = mapped_column(String(300), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    is_discoverable: Mapped[bool] = mapped_column(Boolean, default=True)  # matching opt-out
    is_adult_verified: Mapped[bool] = mapped_column(Boolean, default=False)  # gate for dating mode

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    campus: Mapped["Campus"] = relationship()
    anonymous_profile: Mapped["AnonymousProfile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    interests: Mapped[list["UserInterest"]] = relationship(back_populates="user", cascade="all, delete-orphan")


ANIMALS = [
    "Fox", "Owl", "Panda", "Falcon", "Otter", "Tiger", "Raven", "Koala",
    "Wolf", "Hawk", "Lynx", "Dolphin", "Badger", "Heron", "Cobra", "Stag",
]


class AnonymousProfile(Base):
    """A stable, human-readable pseudonym generated once per user."""
    __tablename__ = "anonymous_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # "Anonymous Fox #4821"
    emoji: Mapped[str] = mapped_column(String(8), default="\U0001F98A")  # fox by default

    user: Mapped["User"] = relationship(back_populates="anonymous_profile")


class UserInterest(Base):
    __tablename__ = "user_interests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    interest: Mapped[str] = mapped_column(String(50), nullable=False)

    user: Mapped["User"] = relationship(back_populates="interests")


class Block(Base):
    __tablename__ = "blocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    blocker_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    blocked_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # comment, reaction, match, message, moderation
    message: Mapped[str] = mapped_column(String(300), nullable=False)
    link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
