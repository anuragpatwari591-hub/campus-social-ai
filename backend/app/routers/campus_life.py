"""Events, opportunities and the campus marketplace."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.deps import get_current_user
from app.models.user import User
from app.models.campus_life import Event, EventRegistration, Opportunity, MarketplaceListing
from app.schemas.misc import (
    EventCreate, EventOut, OpportunityCreate, OpportunityOut,
    MarketplaceListingCreate, MarketplaceListingOut,
)
from app.security.sanitize import sanitize_text

router = APIRouter(prefix="/api", tags=["campus-life"])


# --- Events ---

def _event_out(e: Event, db: Session, user_id: int) -> EventOut:
    return EventOut(
        id=e.id, title=e.title, description=e.description, category=e.category,
        location=e.location, starts_at=e.starts_at, ends_at=e.ends_at,
        registration_count=db.query(EventRegistration).filter_by(event_id=e.id).count(),
        is_registered=db.query(EventRegistration).filter_by(event_id=e.id, user_id=user_id).first() is not None,
    )


@router.post("/events", response_model=EventOut, status_code=201)
def create_event(payload: EventCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = Event(
        campus_id=payload.campus_id or current_user.campus_id, created_by=current_user.id,
        title=sanitize_text(payload.title), description=sanitize_text(payload.description) if payload.description else None,
        category=payload.category, location=payload.location, starts_at=payload.starts_at, ends_at=payload.ends_at,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return _event_out(event, db, current_user.id)


@router.get("/events", response_model=list[EventOut])
def list_events(campus_id: int | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Event)
    if campus_id:
        query = query.filter(Event.campus_id == campus_id)
    events = query.order_by(Event.starts_at.asc()).all()
    return [_event_out(e, db, current_user.id) for e in events]


@router.post("/events/{event_id}/register", status_code=201)
def register_event(event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not db.get(Event, event_id):
        raise HTTPException(status_code=404, detail="Event not found")
    if not db.query(EventRegistration).filter_by(event_id=event_id, user_id=current_user.id).first():
        db.add(EventRegistration(event_id=event_id, user_id=current_user.id))
        db.commit()
    return {"registered": True}


# --- Opportunities ---

@router.post("/opportunities", response_model=OpportunityOut, status_code=201)
def create_opportunity(payload: OpportunityCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    opp = Opportunity(
        posted_by=current_user.id, title=sanitize_text(payload.title),
        description=sanitize_text(payload.description) if payload.description else None,
        opportunity_type=payload.opportunity_type, organization=payload.organization,
        location=payload.location, apply_url=payload.apply_url, deadline=payload.deadline,
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return OpportunityOut.model_validate(opp)


@router.get("/opportunities", response_model=list[OpportunityOut])
def list_opportunities(opportunity_type: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Opportunity)
    if opportunity_type:
        query = query.filter(Opportunity.opportunity_type == opportunity_type)
    return [OpportunityOut.model_validate(o) for o in query.order_by(Opportunity.created_at.desc()).all()]


# --- Marketplace ---

@router.post("/marketplace", response_model=MarketplaceListingOut, status_code=201)
def create_listing(payload: MarketplaceListingCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.price < 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative")
    listing = MarketplaceListing(
        seller_id=current_user.id, campus_id=payload.campus_id or current_user.campus_id,
        title=sanitize_text(payload.title), description=sanitize_text(payload.description) if payload.description else None,
        category=payload.category, price=payload.price, image_url=payload.image_url,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return MarketplaceListingOut(
        id=listing.id, seller_username=current_user.username, title=listing.title,
        description=listing.description, category=listing.category, price=listing.price,
        image_url=listing.image_url, is_sold=listing.is_sold, created_at=listing.created_at,
    )


@router.get("/marketplace", response_model=list[MarketplaceListingOut])
def list_listings(category: str | None = None, campus_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(MarketplaceListing).filter(MarketplaceListing.is_sold == False)  # noqa: E712
    if category:
        query = query.filter(MarketplaceListing.category == category)
    if campus_id:
        query = query.filter(MarketplaceListing.campus_id == campus_id)
    listings = query.order_by(MarketplaceListing.created_at.desc()).all()
    out = []
    for listing in listings:
        seller = db.get(User, listing.seller_id)
        out.append(MarketplaceListingOut(
            id=listing.id, seller_username=seller.username if seller else "unknown", title=listing.title,
            description=listing.description, category=listing.category, price=listing.price,
            image_url=listing.image_url, is_sold=listing.is_sold, created_at=listing.created_at,
        ))
    return out


@router.post("/marketplace/{listing_id}/mark-sold")
def mark_sold(listing_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    listing = db.get(MarketplaceListing, listing_id)
    if not listing or listing.seller_id != current_user.id:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing.is_sold = True
    db.commit()
    return {"is_sold": True}
