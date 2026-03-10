# -*- coding: utf-8 -*-
"""API authentication for ProwlrBot."""

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


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

        # No token configured — allow all (first run)
        if not self.auth_config.token_hash:
            return None

        # Static assets and health check — no auth needed
        path = request.url.path
        if path in ("/", "/health", "/api/health") or not path.startswith("/api"):
            return None

        if credentials is None:
            raise HTTPException(status_code=401, detail="Missing authentication token")

        if not verify_api_token(credentials.credentials, self.auth_config.token_hash):
            raise HTTPException(status_code=401, detail="Invalid authentication token")

        return credentials.credentials
