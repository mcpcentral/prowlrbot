# -*- coding: utf-8 -*-
"""ROAR Protocol SDK — FastAPI router for receiving ROAR messages.

Mount this router on a FastAPI app to accept incoming ROAR messages
over HTTP and WebSocket. Dispatches to the ROARServer handler.

Includes optional in-memory token-bucket rate limiting (no external deps).

Usage::

    from fastapi import FastAPI
    from prowlrbot.protocols.sdk.router import create_roar_router
    from prowlrbot.protocols.sdk.server import ROARServer

    server = ROARServer(identity)
    app = FastAPI()
    app.include_router(create_roar_router(server, rate_limit=60))
"""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from typing import Any, Dict, Optional, Set

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse, StreamingResponse

from ..roar import ROARMessage

logger = logging.getLogger(__name__)

# Maximum concurrent SSE connections to prevent resource exhaustion.
_MAX_SSE_CONNECTIONS = 100


class TokenBucket:
    """In-memory token bucket rate limiter.

    Tokens refill at a steady rate. Each request consumes one token.
    When the bucket is empty, requests are rejected until tokens refill.

    Args:
        max_tokens: Maximum tokens (burst capacity).
        refill_rate: Tokens added per second.
    """

    def __init__(self, max_tokens: float, refill_rate: float) -> None:
        self._max_tokens = max_tokens
        self._refill_rate = refill_rate
        self._tokens = max_tokens
        self._last_refill = time.monotonic()

    def consume(self) -> bool:
        """Try to consume one token.

        Returns:
            True if a token was available and consumed, False if rate limited.
        """
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(
            self._max_tokens,
            self._tokens + elapsed * self._refill_rate,
        )
        self._last_refill = now

        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True
        return False


def _sanitize_error(exc: Exception) -> str:
    """Return a safe error message without internal details."""
    exc_type = type(exc).__name__
    if "validation" in exc_type.lower():
        return "Message validation failed. Check the request body format."
    return "Internal processing error."


def create_roar_router(
    server: Any,
    rate_limit: int = 0,
    auth_token: str = "",
) -> APIRouter:
    """Create a FastAPI router wired to a ROARServer.

    Args:
        server: A ``ROARServer`` instance that handles incoming messages.
        rate_limit: Maximum requests per minute (0 = no limit).
            Uses an in-memory token bucket. Default 0 (disabled).
        auth_token: Optional Bearer token for authenticating WS/SSE
            connections. Empty string disables auth on these endpoints.

    Returns:
        An APIRouter with /roar/message (POST), /roar/ws (WebSocket),
        and /roar/events (SSE) endpoints.
    """
    import hmac as _hmac

    from .server import ROARServer

    assert isinstance(server, ROARServer)
    router = APIRouter(prefix="/roar", tags=["roar"])

    # Set up rate limiter if configured
    _limiter: Optional[TokenBucket] = None
    if rate_limit > 0:
        _limiter = TokenBucket(
            max_tokens=float(rate_limit),
            refill_rate=rate_limit / 60.0,
        )

    # Track active SSE connections to enforce limits
    _active_sse: Set[str] = set()

    # Seen message IDs for idempotency (bounded LRU-ish set)
    _seen_message_ids: Dict[str, float] = {}
    _SEEN_MAX = 10_000
    _SEEN_TTL = 600.0  # 10 minutes

    def _check_rate_limit() -> Optional[JSONResponse]:
        """Return a 429 response if rate limited, None otherwise."""
        if _limiter is not None and not _limiter.consume():
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limited",
                    "detail": "Too many requests. Please try again later.",
                },
            )
        return None

    def _check_seen(msg_id: str) -> bool:
        """Return True if this message ID was already processed (replay)."""
        now = time.time()
        # Evict expired entries periodically
        if len(_seen_message_ids) > _SEEN_MAX:
            expired = [k for k, v in _seen_message_ids.items() if now - v > _SEEN_TTL]
            for k in expired:
                _seen_message_ids.pop(k, None)

        if msg_id in _seen_message_ids:
            return True
        _seen_message_ids[msg_id] = now
        return False

    def _verify_auth_header(authorization: Optional[str]) -> None:
        """Verify Bearer token if auth_token is configured."""
        if not auth_token:
            return
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid authorization",
            )
        token = authorization[7:]
        if not _hmac.compare_digest(token, auth_token):
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization token",
            )

    @router.post("/message")
    async def handle_message(body: Dict[str, Any], request: Request) -> Any:
        """Receive a ROAR message via HTTP POST and return the response."""
        limited = _check_rate_limit()
        if limited is not None:
            return limited

        try:
            incoming = ROARMessage.model_validate(body)
        except Exception as exc:
            logger.warning("Invalid ROAR message: %s", exc)
            return JSONResponse(
                status_code=400,
                content={
                    "error": "invalid_message",
                    "detail": _sanitize_error(exc),
                },
            )

        # Hard reject on signature failure when server has a signing secret
        if server._signing_secret:
            if not incoming.verify(server._signing_secret):
                logger.warning(
                    "Signature verification failed for message %s from %s",
                    incoming.id,
                    incoming.from_identity.did,
                )
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "signature_invalid",
                        "detail": "HMAC signature verification failed.",
                    },
                )

        # Replay protection via idempotency guard
        if _check_seen(incoming.id):
            return JSONResponse(
                status_code=409,
                content={
                    "error": "duplicate_message",
                    "detail": "Message already processed.",
                },
            )

        response = await server.handle_message(incoming)
        return response.model_dump(by_alias=True)

    @router.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket) -> None:
        """Bidirectional WebSocket endpoint for ROAR messages.

        If auth_token is configured, the first frame must be a JSON
        object with {"type": "auth", "token": "<bearer-token>"}.
        """
        await ws.accept()

        # Authenticate if required
        if auth_token:
            try:
                raw = await ws.receive_text()
                auth_data = json.loads(raw)
                if auth_data.get("type") != "auth" or not _hmac.compare_digest(
                    auth_data.get("token", ""),
                    auth_token,
                ):
                    await ws.send_text(
                        json.dumps(
                            {
                                "error": "auth_failed",
                                "detail": "Invalid token.",
                            },
                        ),
                    )
                    await ws.close(code=4001)
                    return
                await ws.send_text(json.dumps({"type": "auth_ok"}))
            except Exception:
                await ws.close(code=4001)
                return

        logger.info("ROAR WebSocket connection established")
        try:
            while True:
                raw = await ws.receive_text()

                if _limiter is not None and not _limiter.consume():
                    await ws.send_text(
                        json.dumps(
                            {
                                "error": "rate_limited",
                                "detail": "Too many requests. Please try again later.",
                            },
                        ),
                    )
                    continue

                try:
                    data = json.loads(raw)
                    incoming = ROARMessage.model_validate(data)

                    # Verify signature on WebSocket frames too
                    if server._signing_secret and not incoming.verify(
                        server._signing_secret,
                    ):
                        await ws.send_text(
                            json.dumps(
                                {
                                    "error": "signature_invalid",
                                    "detail": "HMAC signature verification failed.",
                                },
                            ),
                        )
                        continue

                    # Replay protection
                    if _check_seen(incoming.id):
                        await ws.send_text(
                            json.dumps(
                                {
                                    "error": "duplicate_message",
                                    "detail": "Message already processed.",
                                },
                            ),
                        )
                        continue

                    response = await server.handle_message(incoming)
                    await ws.send_text(
                        json.dumps(response.model_dump(by_alias=True)),
                    )
                except Exception as exc:
                    await ws.send_text(
                        json.dumps(
                            {
                                "error": "processing_error",
                                "detail": _sanitize_error(exc),
                            },
                        ),
                    )
        except WebSocketDisconnect:
            logger.info("ROAR WebSocket disconnected")

    @router.get("/events")
    async def event_stream(
        request: Request,
        session_id: str = "",
        event_type: str = "",
        source: str = "",
        authorization: Optional[str] = Header(None),
    ) -> Any:
        """SSE endpoint for streaming ROAR events.

        Requires Bearer auth when auth_token is configured.
        """
        _verify_auth_header(authorization)

        limited = _check_rate_limit()
        if limited is not None:
            return limited

        # Enforce SSE connection limit
        if len(_active_sse) >= _MAX_SSE_CONNECTIONS:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "too_many_connections",
                    "detail": "SSE connection limit reached.",
                },
            )

        import uuid

        conn_id = uuid.uuid4().hex[:12]

        from .streaming import StreamFilter

        filter_spec = StreamFilter(
            event_types=[t.strip() for t in event_type.split(",") if t.strip()],
            source_dids=[source] if source else [],
            session_ids=[session_id] if session_id else [],
        )

        async def generate():
            _active_sse.add(conn_id)
            try:
                yield 'event: connected\ndata: {"status": "streaming"}\n\n'

                sub = server.event_bus.subscribe(filter_spec)
                try:
                    async for event in sub:
                        data = json.dumps(
                            {
                                "type": event.type,
                                "source": event.source,
                                "session_id": event.session_id,
                                "data": event.data,
                                "timestamp": event.timestamp,
                            },
                        )
                        yield f"event: {event.type}\ndata: {data}\n\n"
                finally:
                    sub.close()
            finally:
                _active_sse.discard(conn_id)

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-ROAR-Protocol": "1.0",
            },
        )

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        """Health check for the ROAR server (minimal info, no auth required)."""
        return {
            "status": "ok",
            "protocol": "roar/1.0",
        }

    return router
