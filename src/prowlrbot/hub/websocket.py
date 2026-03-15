# -*- coding: utf-8 -*-
"""WebSocket support for the ProwlrHub bridge."""

import asyncio
import hmac
import json
import logging
import os

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

# Connected WebSocket clients
_ws_clients: set[WebSocket] = set()

# Connection limit to prevent DoS
MAX_WS_CLIENTS = 50
# Max inbound message size (bytes)
MAX_MESSAGE_SIZE = 1024

# Rate limit: max new connections per IP per minute
_ws_connect_times: dict[str, list[float]] = {}
_WS_CONNECTS_PER_MINUTE = 10


async def broadcast_ws(event: dict):
    """Push event to all connected WebSocket clients."""
    global _ws_clients
    if not _ws_clients:
        return
    dead = set()
    msg = json.dumps(event, default=str)
    for ws in _ws_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    _ws_clients -= dead


def _verify_warroom_token(token: str, secret: str, token_hash: str) -> bool:
    """Return True if token is valid (hub secret, API token hash, or JWT)."""
    if secret and hmac.compare_digest(token, secret):
        return True
    if token_hash:
        import hashlib

        if hmac.compare_digest(
            hashlib.sha256(token.encode()).hexdigest(),
            token_hash,
        ):
            return True
        # Console users log in with JWT; accept valid JWT for same-origin War Room WS
        try:
            from ..auth.jwt_handler import JWTHandler
            from ..auth.middleware import _JWT_SECRET

            expiry = int(os.environ.get("PROWLRBOT_JWT_EXPIRY_MINUTES", "60"))
            handler = JWTHandler(
                secret_key=_JWT_SECRET,
                expiry_minutes=expiry,
            )
            handler.decode_token(token)
            return True
        except (ValueError, Exception):
            pass
    return False


async def warroom_ws(ws: WebSocket):
    """Real-time war room event stream with auth and connection limits."""
    # Verify auth token — required when PROWLR_HUB_SECRET or
    # PROWLRBOT_API_TOKEN_HASH is set (i.e. auth is enabled).
    secret = os.environ.get("PROWLR_HUB_SECRET", "")
    token_hash = os.environ.get("PROWLRBOT_API_TOKEN_HASH", "")
    if secret or token_hash:
        token = ws.query_params.get("token", "")
        if not token:
            await ws.close(code=4001, reason="Authentication required")
            return
        if not _verify_warroom_token(token, secret, token_hash):
            await ws.close(code=4001, reason="Unauthorized")
            return

    # Rate limit new connections per IP
    import time

    client_ip = ws.client.host if ws.client else "unknown"
    now = time.time()
    cutoff = now - 60.0
    times = _ws_connect_times.get(client_ip, [])
    times = [t for t in times if t >= cutoff]
    if len(times) >= _WS_CONNECTS_PER_MINUTE:
        await ws.close(code=4003, reason="Connection rate limit exceeded")
        return
    times.append(now)
    _ws_connect_times[client_ip] = times

    # Enforce connection limit
    if len(_ws_clients) >= MAX_WS_CLIENTS:
        await ws.close(code=4002, reason="Too many connections")
        return

    await ws.accept()
    _ws_clients.add(ws)
    logger.info("WebSocket client connected (%d total)", len(_ws_clients))
    try:
        while True:
            try:
                data = await asyncio.wait_for(ws.receive_text(), timeout=35)
                # Enforce message size limit
                if len(data) > MAX_MESSAGE_SIZE:
                    await ws.close(code=1009, reason="Message too large")
                    break
                if data == "ping":
                    await ws.send_text("pong")
            except asyncio.TimeoutError:
                # Send keepalive
                await ws.send_text(json.dumps({"type": "keepalive"}))
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        _ws_clients.discard(ws)
        logger.info(
            "WebSocket client disconnected (%d remaining)",
            len(_ws_clients),
        )
