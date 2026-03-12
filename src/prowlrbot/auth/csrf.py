# -*- coding: utf-8 -*-
"""CSRF protection using the double-submit cookie pattern."""

from __future__ import annotations

import os
import secrets
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# Cookie name shared between the cookie and the expected header.
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"

# HTTP methods that are considered "safe" (read-only) and do not require
# CSRF validation per RFC 7231.
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

# Paths that are exempt from CSRF checks (e.g. login/register — no cookie
# exists yet, and health probes should never be blocked).
EXEMPT_PATHS = frozenset(
    {
        "/api/auth/login",
        "/api/auth/register",
        "/api/health",
    }
)


class CSRFProtection:
    """Stateless CSRF helpers using the double-submit cookie pattern.

    The token is a cryptographically random 32-byte hex string stored in a
    cookie.  The client reads the cookie (HttpOnly=False) and echoes the value
    back in the ``X-CSRF-Token`` request header.  The middleware compares the
    two values using ``secrets.compare_digest`` to prevent timing attacks.
    """

    @staticmethod
    def generate_token() -> str:
        """Return a cryptographically random 32-byte hex token."""
        return secrets.token_hex(32)

    @staticmethod
    def set_cookie(
        response: Response,
        token: str,
        *,
        secure: Optional[bool] = None,
    ) -> None:
        """Attach the CSRF cookie to *response*.

        Parameters
        ----------
        response:
            The outgoing Starlette/FastAPI response.
        token:
            The CSRF token value.
        secure:
            Whether to set the ``Secure`` flag.  Defaults to ``True`` when the
            ``PROWLRBOT_ENV`` environment variable is ``"production"``.
        """
        if secure is None:
            secure = os.getenv("PROWLRBOT_ENV", "").lower() == "production"

        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=token,
            httponly=False,  # JS must be able to read the cookie
            samesite="strict",
            secure=secure,
            path="/",
        )

    @staticmethod
    def validate(request: Request) -> bool:
        """Return ``True`` when the CSRF cookie matches the header.

        Uses constant-time comparison to prevent timing side-channels.
        """
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        header_token = request.headers.get(CSRF_HEADER_NAME)

        if not cookie_token or not header_token:
            return False

        return secrets.compare_digest(cookie_token, header_token)


class CSRFMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that enforces double-submit-cookie CSRF checks.

    * Safe methods (GET, HEAD, OPTIONS) are always allowed through.
    * Exempt paths (login, register, health) bypass validation.
    * For state-changing methods (POST, PUT, DELETE, PATCH, etc.):
      - If no CSRF cookie exists yet, a fresh token is generated and set on the
        response (the request itself is allowed through so the client can
        bootstrap the token).
      - If a cookie exists but the header is missing or mismatched, the request
        is rejected with ``403 Forbidden``.
    """

    def __init__(self, app) -> None:
        super().__init__(app)
        self._csrf = CSRFProtection()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Safe methods never need CSRF validation.
        if request.method in SAFE_METHODS:
            response = await call_next(request)
            # Ensure a CSRF cookie is present so the client can pick it up.
            if CSRF_COOKIE_NAME not in request.cookies:
                self._csrf.set_cookie(response, self._csrf.generate_token())
            return response

        # Exempt paths (e.g. login before a cookie could exist).
        if request.url.path in EXEMPT_PATHS:
            response = await call_next(request)
            # Bootstrap the cookie if missing.
            if CSRF_COOKIE_NAME not in request.cookies:
                self._csrf.set_cookie(response, self._csrf.generate_token())
            return response

        # --- State-changing request on a protected path ---

        # No CSRF cookie — reject. The client must first make a GET
        # request to obtain the cookie before issuing state-changing
        # requests.
        if CSRF_COOKIE_NAME not in request.cookies:
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "CSRF cookie missing. Make a GET request first to obtain the CSRF token."
                },
            )

        # Cookie exists — validate.
        if not self._csrf.validate(request):
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF validation failed"},
            )

        return await call_next(request)
