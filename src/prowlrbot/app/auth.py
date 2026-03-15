# -*- coding: utf-8 -*-
"""API authentication for ProwlrBot."""

import hashlib
import hmac
import logging
import secrets
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..auth.jwt_handler import JWTHandler
from ..auth.middleware import _JWT_SECRET

logger = logging.getLogger(__name__)


@dataclass
class AuthConfig:
    """Authentication configuration."""

    enabled: bool = True
    token_hash: str = ""


_security = HTTPBearer(auto_error=False)


def generate_api_token() -> str:
    """Generate a cryptographically secure API token."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """Hash a token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def verify_api_token(token: str, stored_hash: str) -> bool:
    """Verify a token against its stored hash."""
    if not token or not stored_hash:
        return False
    return hmac.compare_digest(hash_token(token), stored_hash)


class AuthDependency:
    """FastAPI dependency for bearer token authentication."""

    def __init__(self, auth_config: AuthConfig):
        self.auth_config = auth_config

    async def __call__(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Security(_security),
    ) -> Optional[str]:
        # Auth disabled — allow all
        if not self.auth_config.enabled:
            return None

        # No token configured — block state-changing requests, allow reads.
        # This prevents unauthenticated writes on fresh installs while still
        # letting the console UI load and display data.
        # Auth endpoints are always allowed so users can log in via JWT.
        if not self.auth_config.token_hash:
            path = request.url.path
            if path.startswith("/api/auth/"):
                return None
            method = request.method
            if method in ("POST", "PUT", "DELETE", "PATCH"):
                logger.error(
                    "Blocked %s %s — no PROWLRBOT_API_TOKEN_HASH set. "
                    "Generate one with: prowlr token",
                    method,
                    path,
                )
                raise HTTPException(
                    status_code=401,
                    detail="API authentication not configured. "
                    "Run 'prowlr token' to generate an API token.",
                )
            # Allow GET/HEAD/OPTIONS for read-only console access
            return None

        # Static assets, health check, and auth endpoints — no API-token needed.
        # JWT auth endpoints must be accessible so users can log in.
        path = request.url.path
        if path in ("/", "/health", "/api/health") or not path.startswith("/api"):
            return None
        if path.startswith("/api/auth/oauth/") or path in (
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/oauth/providers",
        ):
            return None

        if credentials is None:
            raise HTTPException(status_code=401, detail="Missing authentication token")

        token = credentials.credentials

        # Accept either a valid API token or a valid JWT
        if self.auth_config.token_hash and verify_api_token(
            token, self.auth_config.token_hash
        ):
            return token

        # Try legacy app JWT
        try:
            import os

            expiry = int(os.environ.get("PROWLRBOT_JWT_EXPIRY_MINUTES", "60"))
            handler = JWTHandler(secret_key=_JWT_SECRET, expiry_minutes=expiry)
            handler.decode_token(token)
            return token
        except (ValueError, Exception):
            pass

        # Try Clerk JWT (when CLERK_JWKS_URL is set)
        from ..auth.clerk_verifier import verify_clerk_token

        if verify_clerk_token(token) is not None:
            return token

        raise HTTPException(status_code=401, detail="Invalid authentication token")
