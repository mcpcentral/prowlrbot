# -*- coding: utf-8 -*-
"""Sliding-window rate limiter with per-role tier configs and ASGI middleware."""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RateLimitConfig(BaseModel):
    """Rate limiting thresholds for a single tier."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10


# ---------------------------------------------------------------------------
# Tier configs keyed by role name
# ---------------------------------------------------------------------------

TIER_CONFIGS: Dict[str, RateLimitConfig] = {
    "admin": RateLimitConfig(
        requests_per_minute=300,
        requests_per_hour=10000,
        burst_size=50,
    ),
    "operator": RateLimitConfig(
        requests_per_minute=120,
        requests_per_hour=5000,
        burst_size=20,
    ),
    "viewer": RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1000,
        burst_size=10,
    ),
    "agent": RateLimitConfig(
        requests_per_minute=200,
        requests_per_hour=8000,
        burst_size=30,
    ),
    "anonymous": RateLimitConfig(
        requests_per_minute=200,
        requests_per_hour=5000,
        burst_size=30,
    ),
}


class RateLimiter:
    """In-memory sliding-window rate limiter.

    Tracks request timestamps per client key and enforces per-minute,
    per-hour, and burst limits.
    """

    def __init__(
        self,
        default_config: Optional[RateLimitConfig] = None,
    ) -> None:
        self.default_config = default_config or RateLimitConfig()
        self._windows: Dict[str, List[float]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(
        self,
        client_key: str,
        config: Optional[RateLimitConfig] = None,
    ) -> bool:
        """Return ``True`` if the request is allowed, ``False`` otherwise."""
        cfg = config or self.default_config
        now = time.time()
        self._cleanup(client_key)

        timestamps = self._windows.setdefault(client_key, [])

        # --- burst check (last 1 second) ---
        one_second_ago = now - 1.0
        burst_count = sum(1 for ts in timestamps if ts >= one_second_ago)
        if burst_count >= cfg.burst_size:
            return False

        # --- per-minute check ---
        one_minute_ago = now - 60.0
        minute_count = sum(1 for ts in timestamps if ts >= one_minute_ago)
        if minute_count >= cfg.requests_per_minute:
            return False

        # --- per-hour check ---
        hour_count = len(timestamps)  # cleanup already removed >1h entries
        if hour_count >= cfg.requests_per_hour:
            return False

        # Allowed — record timestamp
        timestamps.append(now)
        return True

    def get_remaining(
        self,
        client_key: str,
        config: Optional[RateLimitConfig] = None,
    ) -> Dict[str, object]:
        """Return remaining quota and next reset time for *client_key*."""
        cfg = config or self.default_config
        now = time.time()
        self._cleanup(client_key)

        timestamps = self._windows.get(client_key, [])

        one_minute_ago = now - 60.0
        minute_count = sum(1 for ts in timestamps if ts >= one_minute_ago)
        remaining_minute = max(0, cfg.requests_per_minute - minute_count)

        hour_count = len(timestamps)
        remaining_hour = max(0, cfg.requests_per_hour - hour_count)

        # Reset time: earliest timestamp in the current minute window expires
        minute_timestamps = [ts for ts in timestamps if ts >= one_minute_ago]
        if minute_timestamps:
            reset_time = min(minute_timestamps) + 60.0
        else:
            reset_time = now + 60.0

        return {
            "remaining_minute": remaining_minute,
            "remaining_hour": remaining_hour,
            "reset": reset_time,
        }

    def reset(self, client_key: str) -> None:
        """Clear all recorded timestamps for *client_key*."""
        self._windows.pop(client_key, None)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _cleanup(self, client_key: str) -> None:
        """Remove timestamps older than 1 hour for *client_key*."""
        timestamps = self._windows.get(client_key)
        if timestamps is None:
            return
        cutoff = time.time() - 3600.0
        self._windows[client_key] = [ts for ts in timestamps if ts >= cutoff]

        # Periodic global sweep: every 1000 checks, purge stale client keys
        # to prevent unbounded memory growth in long-running processes.
        if not hasattr(self, "_check_count"):
            self._check_count = 0
        self._check_count += 1
        if self._check_count % 1000 == 0:
            stale_keys = [
                k for k, v in self._windows.items() if not v or max(v) < cutoff
            ]
            for k in stale_keys:
                del self._windows[k]


# ---------------------------------------------------------------------------
# FastAPI / Starlette middleware
# ---------------------------------------------------------------------------


def _extract_client_key(request: Request) -> str:
    """Derive a client key from the request.

    Priority:
    1. ``Authorization`` header — extract the subject from a JWT (base64
       middle segment) without full verification so the middleware stays
       lightweight.  Full auth is handled elsewhere.
    2. ``X-Forwarded-For`` header (first address).
    3. Client IP from the ASGI scope.
    """
    # If auth middleware already verified the user, use their ID
    user_id = getattr(getattr(request, "state", None), "user_id", None)
    if user_id:
        return f"user:{user_id}"

    # Fallback: use a hash of the bearer token as key (without decoding
    # the JWT payload, which would trust unverified claims).
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        import hashlib

        token_hash = hashlib.sha256(auth_header[7:].encode()).hexdigest()[:16]
        return f"token:{token_hash}"

    # Use the real client IP from ASGI scope — never trust X-Forwarded-For
    # as it can be spoofed. If behind a trusted reverse proxy, configure
    # uvicorn's --proxy-headers or use ProxyHeadersMiddleware instead.
    client = request.client
    if client:
        return f"ip:{client.host}"

    return "ip:unknown"


def _extract_role(request: Request) -> str:
    """Extract the user role from request state (set by auth middleware).

    Only trusts the role if the auth middleware has already verified the JWT
    and placed the role on request.state. Never decodes the JWT inline —
    an attacker could forge claims to get a higher rate limit tier.
    """
    role = getattr(getattr(request, "state", None), "role", None)
    if role and role in TIER_CONFIGS:
        return role
    return "anonymous"


# Paths that bypass rate limiting
_EXEMPT_PATHS = {"/health", "/healthz", "/api/health"}

# Auth endpoints get stricter limits to prevent brute-force/credential-stuffing
_AUTH_RATE_CONFIG = RateLimitConfig(
    requests_per_minute=10,
    requests_per_hour=50,
    burst_size=3,
)
_AUTH_PATHS = {"/api/auth/login", "/api/auth/register"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that enforces per-client rate limits.

    Usage::

        from prowlrbot.auth.rate_limiter import RateLimitMiddleware

        app.add_middleware(RateLimitMiddleware)
    """

    def __init__(self, app, limiter: Optional[RateLimiter] = None, **kwargs) -> None:  # type: ignore[override]
        super().__init__(app, **kwargs)
        self.limiter = limiter or RateLimiter()

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        # Skip health check endpoints
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        client_key = _extract_client_key(request)

        # Auth endpoints get stricter per-IP limits
        if request.url.path in _AUTH_PATHS:
            client = request.client
            auth_key = f"auth:{client.host}" if client else "auth:unknown"
            config = _AUTH_RATE_CONFIG
            if not self.limiter.check(auth_key, config):
                info = self.limiter.get_remaining(auth_key, config)
                retry_after = int(info["reset"] - time.time())  # type: ignore[operator]
                retry_after = max(1, retry_after)
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Too many authentication attempts. Please try again later.",
                    },
                    headers={"Retry-After": str(retry_after)},
                )

        role = _extract_role(request)
        config = TIER_CONFIGS.get(role, TIER_CONFIGS["anonymous"])

        if not self.limiter.check(client_key, config):
            info = self.limiter.get_remaining(client_key, config)
            retry_after = int(info["reset"] - time.time())  # type: ignore[operator]
            retry_after = max(1, retry_after)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(info["reset"])),  # type: ignore[arg-type]
                },
            )

        response: Response = await call_next(request)

        # Attach rate-limit headers to successful responses
        info = self.limiter.get_remaining(client_key, config)
        response.headers["X-RateLimit-Remaining"] = str(
            info["remaining_minute"],
        )
        response.headers["X-RateLimit-Reset"] = str(int(info["reset"]))  # type: ignore[arg-type]

        return response


# Convenience alias
rate_limit_middleware = RateLimitMiddleware
