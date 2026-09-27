"""
Reports, moderation actions and the audit log for anonymous-identity reveals.
"""
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)  # post | comment | reel | story | user | message
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(50), nullable=False)  # spam | harassment | nudity | hate_speech | other
    details: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | reviewed | dismissed | actioned
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class ModerationAction(Base):
    __tablename__ = "moderation_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    moderator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    report_id: Mapped[int | None] = mapped_column(ForeignKey("reports.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # remove_content | suspend_user | dismiss | warn
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class IdentityAccessLog(Base):
    """
    Audit trail every time a moderator/admin resolves an anonymous persona
    back to a real account. Required by the spec so this sensitive action is
    always traceable, even though it is technically possible in the schema.
    """
    __tablename__ = "identity_access_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    accessed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    anonymous_profile_id: Mapped[int] = mapped_column(ForeignKey("anonymous_profiles.id"), nullable=False)
    reason: Mapped[str] = mapped_column(String(300), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
