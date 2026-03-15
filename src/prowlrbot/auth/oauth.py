# -*- coding: utf-8 -*-
"""OAuth2 providers for GitHub and Google social login.

No external OAuth library required — uses httpx for the token exchange
and user-info fetch. Each provider implements the standard Authorization
Code flow:

  1. Frontend redirects to ``/api/auth/oauth/<provider>``
  2. Backend builds the authorization URL and redirects the browser
  3. Provider redirects back to ``/api/auth/oauth/<provider>/callback``
  4. Backend exchanges code for access token, fetches user info
  5. Creates or links user in the local store, issues a JWT
"""

from __future__ import annotations

import logging
import os
import secrets
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)


@dataclass
class OAuthUserInfo:
    """Normalized user profile returned by an OAuth provider."""

    provider: str
    provider_id: str
    email: str
    username: str
    avatar_url: str = ""


@dataclass
class OAuthProvider:
    """Base configuration for an OAuth2 Authorization Code provider."""

    name: str
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scopes: list[str] = field(default_factory=list)

    def get_authorize_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
            "response_type": "code",
        }
        return f"{self.authorize_url}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> str:
        """Exchange authorization code for an access token."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                self.token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
            token = data.get("access_token")
            if not token:
                raise ValueError(f"No access_token in response: {data}")
            return token

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        raise NotImplementedError


class GitHubOAuth(OAuthProvider):
    """GitHub OAuth2 provider."""

    def __init__(self) -> None:
        super().__init__(
            name="github",
            client_id=os.environ.get("OAUTH_GITHUB_CLIENT_ID", ""),
            client_secret=os.environ.get("OAUTH_GITHUB_CLIENT_SECRET", ""),
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            userinfo_url="https://api.github.com/user",
            scopes=["read:user", "user:email"],
        )

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(self.userinfo_url, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            email = data.get("email", "")
            if not email:
                # GitHub may not return email in profile — fetch from emails API
                emails_resp = await client.get(
                    "https://api.github.com/user/emails",
                    headers=headers,
                )
                if emails_resp.status_code == 200:
                    emails = emails_resp.json()
                    primary = next(
                        (e for e in emails if e.get("primary")),
                        emails[0] if emails else None,
                    )
                    if primary:
                        email = primary.get("email", "")

            return OAuthUserInfo(
                provider="github",
                provider_id=str(data["id"]),
                email=email,
                username=data.get("login", ""),
                avatar_url=data.get("avatar_url", ""),
            )


class GoogleOAuth(OAuthProvider):
    """Google OAuth2 provider."""

    def __init__(self) -> None:
        super().__init__(
            name="google",
            client_id=os.environ.get("OAUTH_GOOGLE_CLIENT_ID", ""),
            client_secret=os.environ.get("OAUTH_GOOGLE_CLIENT_SECRET", ""),
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
            scopes=["openid", "email", "profile"],
        )

    def get_authorize_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{self.authorize_url}?{urlencode(params)}"

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                self.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            data = resp.json()

            return OAuthUserInfo(
                provider="google",
                provider_id=str(data["id"]),
                email=data.get("email", ""),
                username=data.get("email", "").split("@")[0],
                avatar_url=data.get("picture", ""),
            )


# Registry of available providers
_PROVIDERS: dict[str, OAuthProvider] = {}


def get_provider(name: str) -> Optional[OAuthProvider]:
    """Get an OAuth provider by name, initializing on first access."""
    if not _PROVIDERS:
        _init_providers()
    return _PROVIDERS.get(name)


def list_providers() -> list[str]:
    """Return names of configured (non-empty client_id) providers."""
    if not _PROVIDERS:
        _init_providers()
    return [name for name, p in _PROVIDERS.items() if p.client_id]


def _init_providers() -> None:
    gh = GitHubOAuth()
    if gh.client_id:
        _PROVIDERS["github"] = gh

    google = GoogleOAuth()
    if google.client_id:
        _PROVIDERS["google"] = google


def generate_state() -> str:
    """Generate a cryptographically random state parameter for CSRF protection."""
    return secrets.token_urlsafe(32)
