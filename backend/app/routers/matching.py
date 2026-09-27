import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.deps import get_current_user
from app.models.user import User
from app.models.social import Match, MatchMode, Connection
from app.schemas.social import MatchCandidateOut, MatchDecision, ConnectionOut
from app.services.recommendation import find_candidates, record_match_feedback

router = APIRouter(prefix="/api/matching", tags=["matching"])


@router.get("/candidates", response_model=list[MatchCandidateOut])
def get_candidates(mode: str = "friendship", limit: int = 10, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        MatchMode(mode)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}")
    if mode == MatchMode.DATING.value and not current_user.is_adult_verified:
        raise HTTPException(status_code=403, detail="Dating mode requires adult verification")

    candidates = find_candidates(db, current_user, mode, limit)
    out = []
    for candidate, score, breakdown in candidates:
        match = Match(
            user_id=current_user.id, candidate_id=candidate.id, mode=MatchMode(mode),
            score=score, score_breakdown=json.dumps(breakdown),
        )
        db.add(match)
        db.flush()
        out.append(MatchCandidateOut(
            match_id=match.id, user_id=candidate.id, username=candidate.username,
            full_name=candidate.full_name, bio=candidate.bio, avatar_url=candidate.avatar_url,
            score_percent=round(score * 100), score_breakdown=breakdown,
        ))
    db.commit()
    return out


@router.post("/{match_id}/decision")
def decide_match(match_id: int, payload: MatchDecision, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    match = db.get(Match, match_id)
    if not match or match.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Match not found")
    if payload.decision not in ("connect", "skip", "report", "block"):
        raise HTTPException(status_code=400, detail="Invalid decision")

    record_match_feedback(db, match, payload.decision)

    if payload.decision == "connect":
        existing = db.query(Connection).filter_by(requester_id=current_user.id, addressee_id=match.candidate_id).first()
        if not existing:
            db.add(Connection(requester_id=current_user.id, addressee_id=match.candidate_id, status="pending"))
            db.commit()

    return {"decision": payload.decision}


@router.get("/connections", response_model=list[ConnectionOut])
def list_connections(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from sqlalchemy import or_
    connections = db.query(Connection).filter(
        or_(Connection.requester_id == current_user.id, Connection.addressee_id == current_user.id)
    ).all()
    return [ConnectionOut.model_validate(c) for c in connections]


@router.post("/connections/{connection_id}/respond")
def respond_connection(connection_id: int, accept: bool, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conn = db.get(Connection, connection_id)
    if not conn or conn.addressee_id != current_user.id:
        raise HTTPException(status_code=404, detail="Connection request not found")
    conn.status = "accepted" if accept else "declined"
    db.commit()
    return {"status": conn.status}
