# -*- coding: utf-8 -*-
"""WebSocket endpoint for real-time dashboard events."""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from prowlrbot.dashboard.events import DashboardEvent, EventBus


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
