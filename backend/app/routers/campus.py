"""
A dedicated campus page: institution info + campus-scoped stats. The actual
feed/reels/tea/events/communities for a campus are fetched by calling the
existing endpoints with ?campus_id=..., so this router only adds the
aggregate "campus home" view.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.geo import Campus, Institution, City, Region
from app.models.user import User
from app.models.content import Post, Reel
from app.models.social import Community

router = APIRouter(prefix="/api/campus", tags=["campus"])


@router.get("/{campus_id}")
def campus_home(campus_id: int, db: Session = Depends(get_db)):
    campus = (
        db.query(Campus)
        .options(joinedload(Campus.institution).joinedload(Institution.city).joinedload(City.region).joinedload(Region.country))
        .filter(Campus.id == campus_id)
        .first()
    )
    if not campus:
        raise HTTPException(status_code=404, detail="Campus not found")

    inst = campus.institution
    return {
        "campus_id": campus.id,
        "campus_name": campus.name,
        "institution_name": inst.name,
        "city": inst.city.name,
        "country": inst.city.region.country.name,
        "website": inst.website,
        "description": inst.description,
        "is_verified": inst.is_verified,
        "member_count": db.query(User).filter_by(campus_id=campus.id).count(),
        "post_count": db.query(Post).filter_by(campus_id=campus.id).count(),
        "reel_count": db.query(Reel).filter_by(campus_id=campus.id).count(),
        "community_count": db.query(Community).filter_by(campus_id=campus.id).count(),
    }
