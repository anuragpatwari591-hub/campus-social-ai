"""
Future-revenue scaffolding: sponsors and ad campaigns. These are represented
as real database tables and an admin CRUD surface, with a simulated (not
real) billing flow, per the B.Tech scope in the spec.
"""
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Sponsor(Base):
    __tablename__ = "sponsors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    sponsor_id: Mapped[int] = mapped_column(ForeignKey("sponsors.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    placement: Mapped[str] = mapped_column(String(30), default="feed")  # feed, reel, story, event
    creative_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    caption: Mapped[str | None] = mapped_column(String(300), nullable=True)
    budget_demo: Mapped[float] = mapped_column(Float, default=0)  # simulated budget, no real payments
    starts_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    impressions: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
