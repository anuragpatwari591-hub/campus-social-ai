"""
AI usage tracking, kept separate from user content per the spec so prompts
are not retained forever and usage can be rate-limited/audited independently.
"""
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AIRequest(Base):
    __tablename__ = "ai_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    request_type: Mapped[str] = mapped_column(String(30), nullable=False)  # text | image | sticker | meme | moderation
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_excerpt: Mapped[str | None] = mapped_column(String(300), nullable=True)  # truncated, not the full prompt
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class AIFeedback(Base):
    __tablename__ = "ai_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    ai_request_id: Mapped[int] = mapped_column(ForeignKey("ai_requests.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    was_used: Mapped[bool] = mapped_column(Boolean, default=False)  # did the user actually publish it
    rating: Mapped[int | None] = mapped_column(nullable=True)  # 1-5, optional
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class RecommendationWeight(Base):
    """
    A single, explainable, per-mode weight profile used by the matching
    algorithm (see app/services/recommendation.py). Kept as its own table
    (instead of a hard-coded constant) so the admin dashboard can display it
    and so accept/skip feedback can nudge it over time -- a simple, auditable
    stand-in for a full learning-to-rank system.
    """
    __tablename__ = "recommendation_weights"

    id: Mapped[int] = mapped_column(primary_key=True)
    mode: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    w_interests: Mapped[float] = mapped_column(default=0.4)
    w_college: Mapped[float] = mapped_column(default=0.2)
    w_community: Mapped[float] = mapped_column(default=0.2)
    w_activity: Mapped[float] = mapped_column(default=0.2)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
