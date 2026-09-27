"""
User-facing reporting + moderator/admin review queue.

Combines: Rules (moderation.evaluate_text at post time) + AI moderation
(same function, via the provider abstraction) + User reports (this file) +
Admin review (the /queue and /actions endpoints below), per the spec.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.deps import get_current_user, require_moderator
from app.models.user import User, Block
from app.models.content import Post, Comment, Reel
from app.models.moderation import Report, ModerationAction
from app.schemas.misc import ReportCreate, ModerationActionCreate

router = APIRouter(prefix="/api/moderation", tags=["moderation"])


@router.post("/reports", status_code=201)
def create_report(payload: ReportCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.target_type not in ("post", "comment", "reel", "story", "user", "message"):
        raise HTTPException(status_code=400, detail="Invalid target_type")
    report = Report(
        reporter_id=current_user.id, target_type=payload.target_type,
        target_id=payload.target_id, reason=payload.reason, details=payload.details,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"id": report.id, "status": report.status}


@router.get("/reports")
def list_reports(status_filter: str | None = None, _: User = Depends(require_moderator), db: Session = Depends(get_db)):
    query = db.query(Report)
    if status_filter:
        query = query.filter(Report.status == status_filter)
    reports = query.order_by(Report.created_at.desc()).all()
    return [
        {
            "id": r.id, "reporter_id": r.reporter_id, "target_type": r.target_type,
            "target_id": r.target_id, "reason": r.reason, "details": r.details,
            "status": r.status, "created_at": r.created_at,
        }
        for r in reports
    ]


TARGET_MODEL = {"post": Post, "comment": Comment, "reel": Reel}


@router.post("/actions", status_code=201)
def take_action(payload: ModerationActionCreate, moderator: User = Depends(require_moderator), db: Session = Depends(get_db)):
    if payload.action == "remove_content":
        model = TARGET_MODEL.get(payload.target_type)
        if not model:
            raise HTTPException(status_code=400, detail="Cannot remove this target type")
        obj = db.get(model, payload.target_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Target not found")
        obj.is_removed = True
    elif payload.action == "suspend_user":
        user = db.get(User, payload.target_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_suspended = True
    elif payload.action == "warn":
        pass  # recorded via ModerationAction below; a real system would also notify the user
    elif payload.action != "dismiss":
        raise HTTPException(status_code=400, detail="Invalid action")

    if payload.report_id:
        report = db.get(Report, payload.report_id)
        if report:
            report.status = "dismissed" if payload.action == "dismiss" else "actioned"

    action = ModerationAction(
        moderator_id=moderator.id, report_id=payload.report_id, action=payload.action,
        target_type=payload.target_type, target_id=payload.target_id, notes=payload.notes,
    )
    db.add(action)
    db.commit()
    return {"action": payload.action, "applied": True}


@router.post("/identity-reveal/{anonymous_profile_id}")
def reveal_identity_endpoint(anonymous_profile_id: int, reason: str, moderator: User = Depends(require_moderator), db: Session = Depends(get_db)):
    from app.services.anonymous_identity import reveal_identity
    if not reason or len(reason.strip()) < 5:
        raise HTTPException(status_code=400, detail="A documented reason is required to reveal an anonymous identity")
    user = reveal_identity(db, moderator, anonymous_profile_id, reason)
    if not user:
        raise HTTPException(status_code=404, detail="Anonymous profile not found")
    return {"user_id": user.id, "username": user.username, "email": user.email}
