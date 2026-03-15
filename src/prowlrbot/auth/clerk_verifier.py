# -*- coding: utf-8 -*-
"""Verify Clerk-issued JWTs and extract user identity for backend auth."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

import jwt
from jwt import PyJWKClient

logger = logging.getLogger(__name__)


@dataclass
class ClerkClaims:
    """Verified Clerk JWT claims used to resolve or create an app user."""

    sub: str  # Clerk user ID (stable)
    email: str = ""
    # Optional: azp (authorized party) validated if CLERK_AUTHORIZED_PARTIES set


def _get_jwks_url() -> Optional[str]:
    """Return Clerk JWKS URL from env, or None if Clerk auth is disabled."""
    url = os.environ.get("CLERK_JWKS_URL", "").strip()
    return url or None


@lru_cache(maxsize=1)
def _get_jwk_client() -> Optional[PyJWKClient]:
    """Cached JWKS client for Clerk. Returns None if CLERK_JWKS_URL is not set."""
    url = _get_jwks_url()
    if not url:
        return None
    return PyJWKClient(url, cache_keys=True)


def _get_authorized_parties() -> list[str]:
    """Allowed azp (authorized party) origins, e.g. https://app.prowlrbot.com."""
    raw = os.environ.get("CLERK_AUTHORIZED_PARTIES", "").strip()
    if not raw:
        return []
    return [s.strip() for s in raw.split(",") if s.strip()]


def verify_clerk_token(token: str) -> Optional[ClerkClaims]:
    """Verify a Clerk-issued JWT and return claims, or None if invalid/disabled.

    Uses CLERK_JWKS_URL for the public key. If CLERK_AUTHORIZED_PARTIES is set,
    validates the azp claim against that list.
    """
    jwk_client = _get_jwk_client()
    if jwk_client is None:
        return None

    try:
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
    except Exception as exc:
        logger.debug("Clerk JWT verification failed: %s", exc)
        return None

    sub = payload.get("sub")
    if not sub:
        return None

    authorized_parties = _get_authorized_parties()
    if authorized_parties:
        azp = payload.get("azp")
        if azp and azp not in authorized_parties:
            logger.warning(
                "Clerk token azp %r not in CLERK_AUTHORIZED_PARTIES",
                azp,
            )
            return None

    email = (payload.get("email") or payload.get("primary_email") or "").strip()
    return ClerkClaims(sub=sub, email=email)
