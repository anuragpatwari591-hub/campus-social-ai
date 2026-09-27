"""
Global college directory + search.

Search strategy (kept simple and explainable for a viva):
  1. Exact/partial match on institution name or short_name (SQL ILIKE).
  2. Exact/partial match against InstitutionAlias ("IIT KGP" -> IIT Kharagpur).
  3. If nothing matched, fall back to difflib fuzzy matching (stdlib, no
     extra dependency) against name+aliases, so small typos still resolve.
"""
import difflib

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.database import get_db
from app.models.geo import Institution, InstitutionAlias, City, Region, Country
from app.schemas.college import InstitutionOut, InstitutionSearchResult, CampusOut

router = APIRouter(prefix="/api/colleges", tags=["colleges"])


def _to_institution_out(inst: Institution) -> InstitutionOut:
    return InstitutionOut(
        id=inst.id,
        name=inst.name,
        short_name=inst.short_name,
        institution_type=inst.institution_type,
        city=inst.city.name,
        region=inst.city.region.name,
        country=inst.city.region.country.name,
        is_verified=inst.is_verified,
        campuses=[CampusOut.model_validate(c) for c in inst.campuses],
    )


@router.get("/search", response_model=list[InstitutionSearchResult])
def search_institutions(q: str = Query(min_length=1), limit: int = 15, db: Session = Depends(get_db)):
    like = f"%{q}%"
    direct = (
        db.query(Institution)
        .options(joinedload(Institution.city).joinedload(City.region).joinedload(Region.country))
        .filter(or_(Institution.name.ilike(like), Institution.short_name.ilike(like)))
        .limit(limit)
        .all()
    )
    results = {inst.id: (inst, None) for inst in direct}

    if len(results) < limit:
        alias_matches = (
            db.query(InstitutionAlias)
            .options(joinedload(InstitutionAlias.institution).joinedload(Institution.city).joinedload(City.region).joinedload(Region.country))
            .filter(InstitutionAlias.alias.ilike(like))
            .limit(limit)
            .all()
        )
        for alias in alias_matches:
            if alias.institution_id not in results:
                results[alias.institution_id] = (alias.institution, alias.alias)

    if not results:
        # Fuzzy fallback: compare against every institution name + alias.
        all_names = db.query(Institution.id, Institution.name).all()
        all_aliases = db.query(InstitutionAlias.institution_id, InstitutionAlias.alias).all()
        candidates = [(iid, name) for iid, name in all_names] + [(iid, alias) for iid, alias in all_aliases]
        scored = sorted(
            candidates,
            key=lambda c: difflib.SequenceMatcher(None, q.lower(), c[1].lower()).ratio(),
            reverse=True,
        )
        top_ids = []
        for iid, _ in scored:
            if iid not in top_ids:
                top_ids.append(iid)
            if len(top_ids) >= limit:
                break
        institutions = (
            db.query(Institution)
            .options(joinedload(Institution.city).joinedload(City.region).joinedload(Region.country))
            .filter(Institution.id.in_(top_ids))
            .all()
        )
        results = {inst.id: (inst, None) for inst in institutions}

    return [
        InstitutionSearchResult(
            id=inst.id, name=inst.name, short_name=inst.short_name,
            city=inst.city.name, country=inst.city.region.country.name, matched_alias=alias,
        )
        for inst, alias in list(results.values())[:limit]
    ]


@router.get("/{institution_id}", response_model=InstitutionOut)
def get_institution(institution_id: int, db: Session = Depends(get_db)):
    inst = (
        db.query(Institution)
        .options(joinedload(Institution.city).joinedload(City.region).joinedload(Region.country), joinedload(Institution.campuses))
        .filter(Institution.id == institution_id)
        .first()
    )
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    return _to_institution_out(inst)


@router.get("", response_model=list[InstitutionOut])
def list_institutions(country: str | None = None, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(Institution).options(
        joinedload(Institution.city).joinedload(City.region).joinedload(Region.country),
        joinedload(Institution.campuses),
    )
    if country:
        query = query.join(City).join(Region).join(Country).filter(Country.name.ilike(f"%{country}%"))
    institutions = query.limit(limit).all()
    return [_to_institution_out(i) for i in institutions]
