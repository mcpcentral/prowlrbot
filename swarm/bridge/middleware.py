# -*- coding: utf-8 -*-
"""HMAC middleware for request authentication."""

import hashlib
import hmac
import json
import logging
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class HMACMiddleware(BaseHTTPMiddleware):
    """Middleware to validate HMAC signatures on incoming requests."""

    def __init__(self, app, secret: str):
        super().__init__(app)
        self.secret = secret.encode()

    async def dispatch(self, request: Request, call_next: Callable):
        """Validate HMAC signature before processing request."""
        # Skip validation for health check
        if request.url.path == "/health":
            return await call_next(request)

        # Get signature from header
        signature = request.headers.get("X-Swarm-Signature")
        if not signature:
            logger.warning("Missing X-Swarm-Signature header")
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing signature header"},
            )

        # Read and verify body
        try:
            body = await request.body()
            if not body:
                logger.warning("Empty request body")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Empty request body"},
                )

            # Calculate expected signature
            expected = hmac.new(
                self.secret,
                body,
                hashlib.sha256,
            ).hexdigest()

            # Constant-time comparison to prevent timing attacks
            if not hmac.compare_digest(signature, expected):
                logger.warning("Invalid HMAC signature")
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid signature"},
                )

            # Reconstruct request with body for downstream handlers
            async def receive():
                return {"type": "http.request", "body": body}

            request = Request(request.scope, receive, request._send)

        except Exception as e:
            logger.error(f"Error validating signature: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Error validating signature"},
            )

        return await call_next(request)
