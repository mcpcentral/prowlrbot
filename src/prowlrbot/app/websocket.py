# -*- coding: utf-8 -*-
"""WebSocket endpoint for real-time dashboard events."""

import asyncio
import hashlib
import hmac
import json
import os
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from prowlrbot.dashboard.events import DashboardEvent, EventBus


def _verify_ws_token(ws: WebSocket) -> bool:
    """Verify WebSocket auth token from query params.

    Returns True if auth passes (or no auth is configured).
    """
    token_hash = os.environ.get("PROWLRBOT_API_TOKEN_HASH", "")
    hub_secret = os.environ.get("PROWLR_HUB_SECRET", "")
    if not token_hash and not hub_secret:
        return True  # No auth configured
    token = ws.query_params.get("token", "")
    if not token:
        return False
    if hub_secret and hmac.compare_digest(token, hub_secret):
        return True
    if token_hash:
        return hmac.compare_digest(
            hashlib.sha256(token.encode()).hexdigest(), token_hash
        )
    return False


def create_websocket_router(event_bus: EventBus) -> APIRouter:
    """Create a WebSocket router connected to the event bus."""
    router = APIRouter()

    @router.websocket("/ws/dashboard")
    async def dashboard_ws(
        websocket: WebSocket,
        session_id: Optional[str] = Query(None),
    ):
        if not session_id:
            await websocket.close(code=4000, reason="session_id required")
            return

        if not _verify_ws_token(websocket):
            await websocket.close(code=4001, reason="Authentication required")
            return

        await websocket.accept()

        queue: asyncio.Queue[DashboardEvent] = asyncio.Queue()

        async def handler(event: DashboardEvent):
            await queue.put(event)

        event_bus.subscribe(session_id, handler)

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    await websocket.send_json(json.loads(event.to_json()))
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    await websocket.send_json({"type": "ping"})
        except WebSocketDisconnect:
            pass
        finally:
            event_bus.unsubscribe(session_id, handler)

    return router
