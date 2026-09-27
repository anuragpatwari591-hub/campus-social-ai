"""
AI Creation Studio: text/caption generation, image/sticker generation, and
meme text -- all through the provider abstraction (app.ai). Every request is
rate-limited per user per day and logged to AIRequest (without storing the
full prompt) so usage is auditable from the admin dashboard.

The frontend always shows the generated result for the user to approve
before publishing (nothing here posts directly to the feed).
"""
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.deps import get_current_user
from app.models.user import User
from app.models.ai import AIRequest
from app.schemas.misc import AITextRequest, AITextResponse, AIImageRequest, AIImageResponse
from app.ai import get_ai_provider
from app.config import get_settings
from app.services.moderation import evaluate_text

router = APIRouter(prefix="/api/ai", tags=["ai"])
settings = get_settings()


def _check_and_log(db: Session, user: User, request_type: str, prompt: str) -> None:
    since = datetime.now(timezone.utc) - timedelta(days=1)
    count = db.query(AIRequest).filter(
        AIRequest.user_id == user.id, AIRequest.created_at >= since
    ).count()
    if count >= settings.AI_DAILY_REQUEST_LIMIT_PER_USER:
        raise HTTPException(status_code=429, detail="Daily AI usage limit reached. Try again tomorrow.")

    db.add(AIRequest(
        user_id=user.id, request_type=request_type, provider=settings.AI_PROVIDER,
        model=settings.AI_TEXT_MODEL if request_type == "text" else settings.AI_IMAGE_MODEL,
        prompt_excerpt=prompt[:120],
    ))
    db.commit()


@router.post("/text", response_model=AITextResponse)
def generate_text(payload: AITextRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _check_and_log(db, current_user, "text", payload.prompt)
    provider = get_ai_provider()
    text = provider.generate_text(payload.prompt, style=payload.style)

    moderation = evaluate_text(text)
    if moderation["flagged"]:
        raise HTTPException(status_code=422, detail="Generated content was flagged by moderation. Try a different prompt.")

    hashtags = []
    if hasattr(provider, "suggest_hashtags"):
        hashtags = provider.suggest_hashtags(payload.prompt)
    return AITextResponse(text=text, hashtags=hashtags)


@router.post("/image", response_model=AIImageResponse)
def generate_image(payload: AIImageRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _check_and_log(db, current_user, "image", payload.prompt)
    provider = get_ai_provider()
    try:
        url = provider.generate_image(payload.prompt)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI image provider error: {e}")
    return AIImageResponse(image_url=url)


@router.post("/sticker", response_model=AIImageResponse)
def generate_sticker(payload: AIImageRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _check_and_log(db, current_user, "sticker", payload.prompt)
    provider = get_ai_provider()
    try:
        url = provider.generate_sticker(payload.prompt)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI sticker provider error: {e}")
    return AIImageResponse(image_url=url)


@router.post("/meme", response_model=AITextResponse)
def generate_meme_text(payload: AITextRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _check_and_log(db, current_user, "meme", payload.prompt)
    provider = get_ai_provider()
    text = provider.generate_text(payload.prompt, style="funny", max_words=15)
    return AITextResponse(text=text)


@router.post("/assistant")
def campus_assistant(payload: AITextRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    A rule-based "campus assistant": it answers by querying real application
    data (events, communities, trending tea) rather than free-form generation,
    so it never presents an anonymous rumor as a verified fact. Every answer
    is labelled with its data source.
    """
    _check_and_log(db, current_user, "text", payload.prompt)
    question = payload.prompt.lower()

    from app.models.campus_life import Event
    from app.models.social import Community
    from app.models.content import Post
    from datetime import datetime, timezone, timedelta

    if "event" in question:
        now = datetime.now(timezone.utc)
        events = db.query(Event).filter(Event.starts_at >= now, Event.starts_at <= now + timedelta(days=7))
        if current_user.campus_id:
            events = events.filter(Event.campus_id == current_user.campus_id)
        events = events.order_by(Event.starts_at.asc()).limit(5).all()
        if not events:
            return {"answer": "No upcoming events found for your campus this week.", "source": "application_data:events"}
        listing = "; ".join(f"{e.title} ({e.starts_at.strftime('%d %b')})" for e in events)
        return {"answer": f"Upcoming events this week: {listing}", "source": "application_data:events"}

    if "communit" in question:
        communities = db.query(Community).limit(8).all()
        matched = [c for c in communities if any(k in c.name.lower() or k in (c.category or "").lower() for k in question.split())]
        chosen = matched or communities
        if not chosen:
            return {"answer": "No communities have been created yet.", "source": "application_data:communities"}
        listing = ", ".join(c.name for c in chosen[:5])
        return {"answer": f"Communities you might like: {listing}", "source": "application_data:communities"}

    if "trend" in question or "digest" in question:
        recent = db.query(Post).filter(Post.is_removed == False).order_by(Post.created_at.desc()).limit(5).all()  # noqa: E712
        if not recent:
            return {"answer": "No posts yet today.", "source": "application_data:posts", "note": "user_generated_content"}
        listing = "; ".join(p.text[:60] for p in recent)
        return {
            "answer": f"Recent campus posts (unverified, user-generated): {listing}",
            "source": "user_generated_content:posts",
            "note": "These are anonymous/user posts, not verified facts.",
        }

    return {
        "answer": "I can help with: upcoming events, communities, and today's trending campus posts. Try asking about one of those.",
        "source": "assistant_capabilities",
    }
