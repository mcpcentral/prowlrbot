# -*- coding: utf-8 -*-
"""Security headers middleware for CSP, CORS, and general hardening."""

from __future__ import annotations

from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Default Content-Security-Policy directives suitable for the ProwlrBot console
# (React + Vite dev + Ant Design).
#
# NOTE:
# - We intentionally avoid ``'strict-dynamic'`` here because the console is
#   served as a static HTML shell with a compiled JS bundle (no nonces or
#   hashes).  With ``'strict-dynamic'`` and no trusted script via nonce/hash,
#   Chrome will ignore host-based allow‑listing and block the main bundle,
#   resulting in a blank screen.
DEFAULT_CSP_DIRECTIVES: dict[str, str] = {
    "default-src": "'self'",
    # Allow same‑origin scripts (including bundled assets) but keep inline
    # scripts disabled by default.
    "script-src": "'self'",
    "style-src": "'self' 'unsafe-inline'",  # CSS inline is low risk
    "img-src": "'self' data: blob:",
    "font-src": "'self' data:",
    "connect-src": "'self' ws: wss:",
    "frame-ancestors": "'none'",
    "base-uri": "'self'",
    "form-action": "'self'",
}


def _build_csp_header(directives: dict[str, str]) -> str:
    """Serialize a directives dict into a CSP header value.

    Example output:
        ``default-src 'self'; script-src 'self' 'unsafe-inline'; ...``
    """
    return "; ".join(f"{key} {value}" for key, value in directives.items())


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects standard security headers into every HTTP response.

    Parameters
    ----------
    app:
        The ASGI application to wrap.
    csp_directives:
        Optional mapping of CSP directive-name to value.  Merged on top of
        ``DEFAULT_CSP_DIRECTIVES`` so callers only need to specify overrides.
    allowed_origins:
        Reserved for future CORS integration.  Currently unused — CORS is
        typically configured separately via ``CORSMiddleware``.
    """

    def __init__(
        self,
        app,
        csp_directives: Optional[dict[str, str]] = None,
        allowed_origins: Optional[list[str]] = None,
    ) -> None:
        super().__init__(app)
        merged = dict(DEFAULT_CSP_DIRECTIVES)
        if csp_directives:
            merged.update(csp_directives)
        self._csp_header = _build_csp_header(merged)
        self._allowed_origins = allowed_origins or []

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # --- Always-on headers ---
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        # X-XSS-Protection omitted — deprecated by modern browsers and can
        # introduce vulnerabilities in IE. CSP provides better protection.
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(self), geolocation=()"
        )

        # HSTS — only meaningful over TLS.
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # CSP is irrelevant for JSON API responses and can interfere with
        # clients that inspect headers, so skip it for /api/ routes.
        if not request.url.path.startswith("/api/"):
            response.headers["Content-Security-Policy"] = self._csp_header

        return response
