from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.deps import get_current_user
from app.models.user import User
from app.models.social import Community, CommunityMember
from app.schemas.social import CommunityCreate, CommunityOut
from app.security.sanitize import sanitize_text

router = APIRouter(prefix="/api/communities", tags=["communities"])


def _out(c: Community, db: Session, user_id: int) -> CommunityOut:
    return CommunityOut(
        id=c.id, name=c.name, description=c.description, category=c.category,
        member_count=db.query(CommunityMember).filter_by(community_id=c.id).count(),
        is_member=db.query(CommunityMember).filter_by(community_id=c.id, user_id=user_id).first() is not None,
    )


@router.post("", response_model=CommunityOut, status_code=201)
def create_community(payload: CommunityCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    community = Community(
        name=sanitize_text(payload.name), description=sanitize_text(payload.description) if payload.description else None,
        category=payload.category, campus_id=payload.campus_id or current_user.campus_id, created_by=current_user.id,
    )
    db.add(community)
    db.flush()
    db.add(CommunityMember(community_id=community.id, user_id=current_user.id, role="owner"))
    db.commit()
    db.refresh(community)
    return _out(community, db, current_user.id)


@router.get("", response_model=list[CommunityOut])
def list_communities(category: str | None = None, campus_id: int | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Community)
    if category:
        query = query.filter(Community.category == category)
    if campus_id:
        query = query.filter(Community.campus_id == campus_id)
    return [_out(c, db, current_user.id) for c in query.all()]


@router.post("/{community_id}/join", status_code=201)
def join_community(community_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    community = db.get(Community, community_id)
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    if db.query(CommunityMember).filter_by(community_id=community_id, user_id=current_user.id).first():
        return {"joined": True}
    db.add(CommunityMember(community_id=community_id, user_id=current_user.id))
    db.commit()
    return {"joined": True}


@router.post("/{community_id}/leave", status_code=200)
def leave_community(community_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    member = db.query(CommunityMember).filter_by(community_id=community_id, user_id=current_user.id).first()
    if member:
        db.delete(member)
        db.commit()
    return {"left": True}
