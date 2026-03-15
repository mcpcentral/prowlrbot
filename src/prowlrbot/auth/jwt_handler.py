# -*- coding: utf-8 -*-
"""Manual JWT implementation using HMAC-SHA256 (no external dependency)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Optional

from .models import Role, TokenPayload, User


def _b64url_encode(data: bytes) -> str:
    """Base64-url encode *data* without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    """Base64-url decode *s*, re-adding padding as needed."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


class JWTHandler:
    """Create and verify JWT tokens using HMAC-SHA256."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        expiry_minutes: int = 60,
    ) -> None:
        self._secret = secret_key.encode("utf-8")
        self._algorithm = algorithm
        self._expiry_minutes = expiry_minutes

    # ------------------------------------------------------------------
    # internal
    # ------------------------------------------------------------------

    def _sign(self, header_b64: str, payload_b64: str) -> str:
        msg = f"{header_b64}.{payload_b64}".encode("ascii")
        sig = hmac.new(self._secret, msg, hashlib.sha256).digest()
        return _b64url_encode(sig)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def create_token(self, user: User) -> str:
        """Create a signed JWT for *user*."""
        now = time.time()
        header = {"alg": self._algorithm, "typ": "JWT"}
        payload = TokenPayload(
            sub=user.id,
            username=user.username,
            role=user.role,
            iat=now,
            exp=now + self._expiry_minutes * 60,
            iss="prowlrbot",
            aud="prowlrbot-api",
        )
        header_b64 = _b64url_encode(
            json.dumps(header, separators=(",", ":")).encode(),
        )
        payload_b64 = _b64url_encode(
            json.dumps(payload.model_dump(), separators=(",", ":")).encode(),
        )
        signature = self._sign(header_b64, payload_b64)
        return f"{header_b64}.{payload_b64}.{signature}"

    def decode_token(self, token: str) -> TokenPayload:
        """Decode and validate a JWT, returning the payload.

        Raises:
            ValueError: If the token is malformed, the signature is invalid,
                or the token has expired.
        """
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Malformed JWT: expected 3 parts")

        header_b64, payload_b64, signature = parts

        # Verify signature
        expected_sig = self._sign(header_b64, payload_b64)
        if not hmac.compare_digest(signature, expected_sig):
            raise ValueError("Invalid JWT signature")

        # Decode payload
        try:
            raw = json.loads(_b64url_decode(payload_b64))
        except (json.JSONDecodeError, Exception) as exc:
            raise ValueError(f"Invalid JWT payload: {exc}") from exc

        payload = TokenPayload(**raw)

        # Check expiry
        if payload.exp < time.time():
            raise ValueError("JWT has expired")

        # Validate issuer
        if payload.iss != "prowlrbot":
            raise ValueError("Invalid JWT issuer")

        # Validate audience
        if payload.aud != "prowlrbot-api":
            raise ValueError("Invalid JWT audience")

        return payload

    def refresh_token(self, token: str) -> str:
        """Decode an existing token and create a new one with a fresh expiry.

        The original token must still be valid (not expired).
        """
        payload = self.decode_token(token)
        # Build a minimal User just to re-create the token.
        user = User(
            id=payload.sub,
            username=payload.username,
            role=payload.role,
        )
        return self.create_token(user)
