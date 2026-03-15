# -*- coding: utf-8 -*-
"""OAuth2 login endpoints for GitHub and Google."""

from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from ...auth.jwt_handler import JWTHandler
from ...auth.middleware import _JWT_SECRET
from ...auth.models import AuthResponse
from ...auth.oauth import get_provider, list_providers, generate_state
from ...auth.store import UserStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/oauth", tags=["oauth"])

_store: Optional[UserStore] = None
# In-memory state store (short-lived CSRF tokens for OAuth flow).
# In a multi-process setup, use Redis or a DB table instead.
_pending_states: dict[str, str] = {}


def _get_store() -> UserStore:
    global _store
    if _store is None:
        _store = UserStore()
    return _store


def _get_jwt() -> JWTHandler:
    expiry = int(os.environ.get("PROWLRBOT_JWT_EXPIRY_MINUTES", "60"))
    return JWTHandler(secret_key=_JWT_SECRET, expiry_minutes=expiry)


@router.get(
    "/providers",
    summary="List configured OAuth providers",
)
async def oauth_providers() -> dict:
    """Return which OAuth providers are available (have client IDs configured)."""
    return {"providers": list_providers()}


@router.get(
    "/{provider_name}",
    summary="Start OAuth login flow",
)
async def oauth_start(
    provider_name: str,
    request: Request,
) -> RedirectResponse:
    """Redirect the user to the OAuth provider's authorization page."""
    provider = get_provider(provider_name)
    if provider is None:
        raise HTTPException(
            status_code=404,
            detail=f"OAuth provider '{provider_name}' is not configured. "
            f"Set OAUTH_{provider_name.upper()}_CLIENT_ID and "
            f"OAUTH_{provider_name.upper()}_CLIENT_SECRET env vars.",
        )

    state = generate_state()
    _pending_states[state] = provider_name

    # Build callback URL from the current request
    base_url = os.environ.get(
        "PROWLRBOT_BASE_URL",
        str(request.base_url).rstrip("/"),
    )
    redirect_uri = f"{base_url}/api/auth/oauth/{provider_name}/callback"

    authorize_url = provider.get_authorize_url(redirect_uri, state)
    return RedirectResponse(url=authorize_url)


@router.get(
    "/{provider_name}/callback",
    summary="OAuth callback — exchange code for JWT",
)
async def oauth_callback(
    provider_name: str,
    request: Request,
    code: str = "",
    state: str = "",
    error: str = "",
) -> RedirectResponse:
    """Handle the OAuth provider's callback, create/link user, issue JWT."""
    if error:
        logger.warning("OAuth error from %s: %s", provider_name, error)
        return RedirectResponse(url=f"/?oauth_error={error}")

    if not code or not state:
        raise HTTPException(
            status_code=400,
            detail="Missing code or state parameter",
        )

    # Verify CSRF state
    expected_provider = _pending_states.pop(state, None)
    if expected_provider is None or expected_provider != provider_name:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired state parameter",
        )

    provider = get_provider(provider_name)
    if provider is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown provider: {provider_name}",
        )

    # Build callback URL (must match what we sent to the provider)
    base_url = os.environ.get(
        "PROWLRBOT_BASE_URL",
        str(request.base_url).rstrip("/"),
    )
    redirect_uri = f"{base_url}/api/auth/oauth/{provider_name}/callback"

    try:
        access_token = await provider.exchange_code(code, redirect_uri)
        user_info = await provider.get_user_info(access_token)
    except Exception as exc:
        logger.error(
            "OAuth token exchange failed for %s: %s",
            provider_name,
            exc,
        )
        return RedirectResponse(url="/?oauth_error=token_exchange_failed")

    # Create or link user
    store = _get_store()
    user = store.authenticate_oauth(
        provider=user_info.provider,
        provider_id=user_info.provider_id,
        email=user_info.email,
        username=user_info.username,
        avatar_url=user_info.avatar_url,
    )

    # Issue JWT
    jwt = _get_jwt()
    token = jwt.create_token(user)

    # Redirect to frontend with token in URL fragment (not query param for security)
    return RedirectResponse(url=f"/#/oauth/callback?token={token}")
