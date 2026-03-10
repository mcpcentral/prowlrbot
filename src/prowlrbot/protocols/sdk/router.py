# -*- coding: utf-8 -*-
"""ROAR Protocol SDK — FastAPI router for receiving ROAR messages.

Mount this router on a FastAPI app to accept incoming ROAR messages
over HTTP and WebSocket. Dispatches to the ROARServer handler.

Usage::

    from fastapi import FastAPI
    from prowlrbot.protocols.sdk.router import create_roar_router
    from prowlrbot.protocols.sdk.server import ROARServer

    server = ROARServer(identity)
    app = FastAPI()
    app.include_router(create_roar_router(server))
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from ..roar import ROARMessage

logger = logging.getLogger(__name__)


def create_roar_router(server: Any) -> APIRouter:
    """Create a FastAPI router wired to a ROARServer.

    Args:
        server: A ``ROARServer`` instance that handles incoming messages.

    Returns:
        An APIRouter with /roar/message (POST), /roar/ws (WebSocket),
        and /roar/events (SSE) endpoints.
    """
    from .server import ROARServer

    assert isinstance(server, ROARServer)
    router = APIRouter(prefix="/roar", tags=["roar"])

    @router.post("/message")
    async def handle_message(body: Dict[str, Any]) -> Dict[str, Any]:
        """Receive a ROAR message via HTTP POST and return the response.

        The request body is a JSON-serialized ROARMessage. The response
        is the handler's ROARMessage serialized to JSON.
        """
        try:
            incoming = ROARMessage.model_validate(body)
        except Exception as exc:
            logger.warning("Invalid ROAR message: %s", exc)
            return {"error": "invalid_message", "detail": str(exc)}

        # Verify signature if server has a secret
        if server._signing_secret and not incoming.verify(server._signing_secret):
            logger.warning(
                "Signature verification failed for message %s from %s",
                incoming.id,
                incoming.from_identity.did,
            )
            # Still process — verification is advisory in v1.0
            # In v2.0 this will become a hard reject

        response = await server.handle_message(incoming)
        return response.model_dump(by_alias=True)

    @router.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket) -> None:
        """Bidirectional WebSocket endpoint for ROAR messages.

        Each incoming frame is a JSON ROARMessage. Responses are sent
        back as JSON frames. The connection stays open for streaming.
        """
        await ws.accept()
        logger.info("ROAR WebSocket connection established")
        try:
            while True:
                raw = await ws.receive_text()
                try:
                    data = json.loads(raw)
                    incoming = ROARMessage.model_validate(data)
                    response = await server.handle_message(incoming)
                    await ws.send_text(
                        json.dumps(response.model_dump(by_alias=True))
                    )
                except Exception as exc:
                    error_msg = json.dumps({
                        "error": "processing_error",
                        "detail": str(exc),
                    })
                    await ws.send_text(error_msg)
        except WebSocketDisconnect:
            logger.info("ROAR WebSocket disconnected")

    @router.get("/events")
    async def event_stream(
        session_id: str = "",
        event_type: str = "",
        source: str = "",
    ) -> StreamingResponse:
        """SSE endpoint for streaming ROAR events.

        Compatible with A2A's SSE streaming and MCP's Streamable HTTP.
        Subscribes to the server's event bus with optional filters.

        Query params:
            session_id: Filter events to this session.
            event_type: Comma-separated event types to receive.
            source: Filter events to this source DID.
        """
        from .streaming import StreamFilter

        filter_spec = StreamFilter(
            event_types=[t.strip() for t in event_type.split(",") if t.strip()],
            source_dids=[source] if source else [],
            session_ids=[session_id] if session_id else [],
        )

        async def generate():
            yield "event: connected\ndata: {\"status\": \"streaming\"}\n\n"

            sub = server.event_bus.subscribe(filter_spec)
            try:
                async for event in sub:
                    data = json.dumps({
                        "type": event.type,
                        "source": event.source,
                        "session_id": event.session_id,
                        "data": event.data,
                        "timestamp": event.timestamp,
                    })
                    yield f"event: {event.type}\ndata: {data}\n\n"
            finally:
                sub.close()

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
        """Health check for the ROAR server."""
        card = server.get_card()
        return {
            "status": "ok",
            "agent": card.identity.did,
            "name": card.identity.display_name,
            "protocol": "roar/1.0",
            "transports": list(card.endpoints.keys()),
        }

    return router
