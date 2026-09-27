"""
Admin dashboard: platform-wide management + analytics computed live from the
database (never fabricated placeholder numbers).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.auth.deps import require_admin
from app.models.user import User, UserRole
from app.models.content import Post, Reel, Story, Comment
from app.models.social import Community
from app.models.moderation import Report
from app.models.campus_life import Event, Opportunity, MarketplaceListing
from app.models.ai import AIRequest
from app.models.geo import Institution
from app.models.monetization import Sponsor, Campaign
from app.schemas.misc import SponsorCreate, SponsorOut, CampaignCreate, CampaignOut

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/analytics")
def analytics(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return {
        "registered_users": db.query(User).count(),
        "active_users": db.query(User).filter_by(is_active=True, is_suspended=False).count(),
        "suspended_users": db.query(User).filter_by(is_suspended=True).count(),
        "posts": db.query(Post).count(),
        "anonymous_posts": db.query(Post).filter_by(is_anonymous=True).count(),
        "reels": db.query(Reel).count(),
        "stories": db.query(Story).count(),
        "comments": db.query(Comment).count(),
        "communities": db.query(Community).count(),
        "institutions": db.query(Institution).count(),
        "pending_reports": db.query(Report).filter_by(status="pending").count(),
        "events": db.query(Event).count(),
        "opportunities": db.query(Opportunity).count(),
        "marketplace_listings": db.query(MarketplaceListing).count(),
        "ai_requests_total": db.query(AIRequest).count(),
        "flagged_posts": db.query(Post).filter_by(is_flagged=True).count(),
    }


@router.get("/users")
def list_users(limit: int = 50, offset: int = 0, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    return [
        {"id": u.id, "username": u.username, "email": u.email, "role": u.role.value,
         "is_active": u.is_active, "is_suspended": u.is_suspended, "campus_id": u.campus_id}
        for u in users
    ]


@router.post("/users/{user_id}/role")
def set_role(user_id: int, role: str, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        new_role = UserRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = new_role
    db.commit()
    return {"id": user.id, "role": user.role.value}


@router.post("/users/{user_id}/suspend")
def suspend_user(user_id: int, suspend: bool = True, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_suspended = suspend
    db.commit()
    return {"id": user.id, "is_suspended": user.is_suspended}


@router.post("/institutions/{institution_id}/verify")
def verify_institution(institution_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    inst = db.get(Institution, institution_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    inst.is_verified = True
    db.commit()
    return {"id": inst.id, "is_verified": True}


# --- Sponsors / campaigns (simulated monetization) ---

@router.post("/sponsors", response_model=SponsorOut, status_code=201)
def create_sponsor(payload: SponsorCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    sponsor = Sponsor(name=payload.name, website=payload.website, logo_url=payload.logo_url)
    db.add(sponsor)
    db.commit()
    db.refresh(sponsor)
    return SponsorOut.model_validate(sponsor)


@router.get("/sponsors", response_model=list[SponsorOut])
def list_sponsors(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return [SponsorOut.model_validate(s) for s in db.query(Sponsor).all()]


@router.post("/campaigns", response_model=CampaignOut, status_code=201)
def create_campaign(payload: CampaignCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    if not db.get(Sponsor, payload.sponsor_id):
        raise HTTPException(status_code=404, detail="Sponsor not found")
    campaign = Campaign(**payload.model_dump())
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return CampaignOut.model_validate(campaign)


@router.get("/campaigns", response_model=list[CampaignOut])
def list_campaigns(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return [CampaignOut.model_validate(c) for c in db.query(Campaign).all()]
