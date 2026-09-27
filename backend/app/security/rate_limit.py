"""
A minimal in-memory sliding-window rate limiter.

This is intentionally simple (a dict keyed by client identity, no Redis)
because a B.Tech single-process demo deployment doesn't need a distributed
limiter, and it keeps the mechanism easy to explain in a viva: every request
records its timestamp; anything older than the window is dropped; if too
many remain, the request is rejected with 429.
"""
import time
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import get_settings

settings = get_settings()
_hits: dict[str, deque] = defaultdict(deque)


def _client_key(request: Request) -> str:
    auth = request.headers.get("authorization")
    if auth:
        return f"auth:{auth[-24:]}"
    client = request.client
    return f"ip:{client.host if client else 'unknown'}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi"):
            return await call_next(request)

        key = _client_key(request)
        now = time.time()
        window = settings.RATE_LIMIT_WINDOW_SECONDS
        bucket = _hits[key]

        while bucket and bucket[0] < now - window:
            bucket.popleft()

        if len(bucket) >= settings.RATE_LIMIT_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
            )

        bucket.append(now)
        return await call_next(request)
