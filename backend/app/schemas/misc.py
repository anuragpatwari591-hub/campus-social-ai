from datetime import datetime

from pydantic import BaseModel, field_validator


class ReportCreate(BaseModel):
    target_type: str
    target_id: int
    reason: str
    details: str | None = None


class ModerationActionCreate(BaseModel):
    report_id: int | None = None
    action: str
    target_type: str
    target_id: int
    notes: str | None = None


class AITextRequest(BaseModel):
    prompt: str
    style: str = "casual"
    context: str = "caption"  # caption, bio, story, poll_question, event_description, hashtags

    @field_validator("prompt")
    @classmethod
    def prompt_bounds(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Prompt cannot be empty")
        if len(v) > 500:
            raise ValueError("Prompt too long (max 500 characters)")
        return v


class AITextResponse(BaseModel):
    text: str
    hashtags: list[str] = []


class AIImageRequest(BaseModel):
    prompt: str

    @field_validator("prompt")
    @classmethod
    def prompt_bounds(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Prompt cannot be empty")
        if len(v) > 500:
            raise ValueError("Prompt too long (max 500 characters)")
        return v


class AIImageResponse(BaseModel):
    image_url: str


class NotificationOut(BaseModel):
    id: int
    type: str
    message: str
    link: str | None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class EventCreate(BaseModel):
    title: str
    description: str | None = None
    category: str = "general"
    location: str | None = None
    starts_at: datetime
    ends_at: datetime | None = None
    campus_id: int | None = None


class EventOut(BaseModel):
    id: int
    title: str
    description: str | None
    category: str
    location: str | None
    starts_at: datetime
    ends_at: datetime | None
    registration_count: int
    is_registered: bool = False


class OpportunityCreate(BaseModel):
    title: str
    description: str | None = None
    opportunity_type: str = "internship"
    organization: str | None = None
    location: str | None = None
    apply_url: str | None = None
    deadline: datetime | None = None


class OpportunityOut(BaseModel):
    id: int
    title: str
    description: str | None
    opportunity_type: str
    organization: str | None
    location: str | None
    apply_url: str | None
    deadline: datetime | None

    model_config = {"from_attributes": True}


class MarketplaceListingCreate(BaseModel):
    title: str
    description: str | None = None
    category: str = "other"
    price: float = 0
    image_url: str | None = None
    campus_id: int | None = None


class MarketplaceListingOut(BaseModel):
    id: int
    seller_username: str
    title: str
    description: str | None
    category: str
    price: float
    image_url: str | None
    is_sold: bool
    created_at: datetime


class SponsorCreate(BaseModel):
    name: str
    website: str | None = None
    logo_url: str | None = None


class SponsorOut(BaseModel):
    id: int
    name: str
    website: str | None
    logo_url: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class CampaignCreate(BaseModel):
    sponsor_id: int
    title: str
    placement: str = "feed"
    creative_url: str | None = None
    caption: str | None = None
    budget_demo: float = 0


class CampaignOut(BaseModel):
    id: int
    sponsor_id: int
    title: str
    placement: str
    creative_url: str | None
    caption: str | None
    budget_demo: float
    impressions: int
    is_active: bool

    model_config = {"from_attributes": True}
