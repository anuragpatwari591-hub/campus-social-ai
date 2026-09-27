"""
FastAPI application entrypoint.

On startup, tables are created directly from the SQLAlchemy models
(Base.metadata.create_all) rather than via a migration tool -- this keeps
the "how does the schema get created" story simple and demonstrable for a
B.Tech viva. See seed_data/seed.py for populating the college directory and
demo content afterwards.
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import engine, Base
from app.security.rate_limit import RateLimitMiddleware
import app.models  # noqa: F401  (import registers all models with Base.metadata)

from app.routers import (
    auth, colleges, campus, posts, reels, stories, communities, rooms,
    matching, messaging, moderation, ai_studio, notifications, campus_life,
    uploads, admin,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered student social & campus platform (B.Tech project)",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # relaxed for local/demo use; tighten to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}


for router in (
    auth.router, colleges.router, campus.router, posts.router, reels.router,
    stories.router, communities.router, rooms.router, matching.router,
    messaging.router, moderation.router, ai_studio.router, notifications.router,
    campus_life.router, uploads.router, admin.router,
):
    app.include_router(router)
