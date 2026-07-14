# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Simple in-process rate limiting middleware (no external dependencies).

Suitable for a single backend container. Multi-replica deployments would need
a shared store — document that limitation in the ops guide.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("middleware.rate_limit")

# path-prefix -> (max_requests, window_seconds)
_RULES: Tuple[Tuple[str, int, int], ...] = (
    ("/api/v1/auth/login", 20, 60),
    ("/api/v1/auth/register", 10, 60),
    ("/api/v1/auth/forgot-password", 5, 60),
    ("/api/v1/auth/reset-password", 10, 60),
    ("/api/v1/auth/change-password", 10, 60),
    ("/api/v1/files/upload", 30, 60),
    ("/api/v1/chat/", 60, 60),
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Reject excess requests to sensitive endpoints with HTTP 429."""

    def __init__(self, app):
        super().__init__(app)
        self._hits: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)

    def _match_rule(self, path: str) -> Tuple[int, int] | None:
        for prefix, limit, window in _RULES:
            if path.startswith(prefix):
                return limit, window
        return None

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    async def dispatch(self, request: Request, call_next) -> Response:
        rule = self._match_rule(request.url.path)
        if rule is None:
            return await call_next(request)

        limit, window = rule
        key = (self._client_key(request), request.url.path.split("?")[0])
        now = time.monotonic()
        bucket = self._hits[key]

        while bucket and now - bucket[0] > window:
            bucket.popleft()

        if len(bucket) >= limit:
            logger.warning(
                "Rate limit exceeded for %s on %s (%s/%ss)",
                key[0],
                key[1],
                limit,
                window,
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again shortly."},
                headers={"Retry-After": str(window)},
            )

        bucket.append(now)
        return await call_next(request)
