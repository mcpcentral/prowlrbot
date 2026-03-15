# -*- coding: utf-8 -*-
"""Simple in-memory rate limiter for API endpoints."""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


@dataclass
class RateLimiter:
    """Token bucket rate limiter."""

    max_requests: int = 100
    window_seconds: float = 60.0
    _requests: Dict[str, List[float]] = field(
        default_factory=lambda: defaultdict(list),
    )

    def allow(self, client_id: str) -> bool:
        """Check if a request from client_id is allowed."""
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old entries
        self._requests[client_id] = [
            t for t in self._requests[client_id] if t > window_start
        ]

        if len(self._requests[client_id]) >= self.max_requests:
            return False

        self._requests[client_id].append(now)
        return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting API requests."""

    def __init__(
        self,
        app,
        max_requests: int = 100,
        window_seconds: float = 60.0,
    ):
        super().__init__(app)
        self.limiter = RateLimiter(
            max_requests=max_requests,
            window_seconds=window_seconds,
        )

    async def dispatch(self, request: Request, call_next):
        # Only rate-limit API endpoints
        if not request.url.path.startswith("/api"):
            return await call_next(request)

        # Skip health checks
        if request.url.path in ("/api/health",):
            return await call_next(request)

        client_id = request.client.host if request.client else "unknown"

        if not self.limiter.allow(client_id):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
            )

        return await call_next(request)
