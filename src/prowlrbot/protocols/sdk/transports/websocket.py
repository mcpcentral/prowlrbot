# -*- coding: utf-8 -*-
"""ROAR WebSocket Transport — persistent bidirectional communication.

Uses the ``websockets`` library for async WebSocket connections.
After the HTTP upgrade handshake, both sides can send ROARMessage
frames at any time. Ideal for real-time streaming (Layer 5).

Ref: Neither MCP nor A2A support WebSocket — this is a ROAR differentiator.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Callable, Dict, Optional

from ...roar import ConnectionConfig, ROARMessage

logger = logging.getLogger(__name__)


async def websocket_send(
    config: ConnectionConfig,
    message: ROARMessage,
) -> ROARMessage:
    """Send a ROAR message via WebSocket and wait for the response.

    Opens a WebSocket connection, sends the message, waits for a single
    response, then closes. For persistent connections, use ``WebSocketConnection``.

    Args:
        config: Connection config with WebSocket URL (ws:// or wss://).
        message: The message to send.

    Returns:
        The response ROARMessage.

    Raises:
        ConnectionError: If the WebSocket connection fails.
    """
    import websockets

    url = config.url
    if not url:
        raise ConnectionError("WebSocket transport requires a URL")

    # Convert http(s) to ws(s) if needed
    if url.startswith("http://"):
        url = "ws://" + url[7:]
    elif url.startswith("https://"):
        url = "wss://" + url[8:]

    if not url.endswith("/roar/ws"):
        url = url.rstrip("/") + "/roar/ws"

    payload = json.dumps(message.model_dump(by_alias=True))
    timeout = config.timeout_ms / 1000

    try:
        async with websockets.connect(
            url,
            open_timeout=timeout,
            close_timeout=5,
            additional_headers={"X-ROAR-Protocol": message.roar},
        ) as ws:
            await ws.send(payload)
            response_raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
            data = json.loads(response_raw)
            return ROARMessage.model_validate(data)
    except Exception as exc:
        raise ConnectionError(f"WebSocket error to {url}: {exc}") from exc


class WebSocketConnection:
    """Persistent WebSocket connection for bidirectional ROAR messaging.

    Usage::

        conn = WebSocketConnection(config)
        await conn.connect()

        # Send messages
        response = await conn.send(message)

        # Stream events
        async for event in conn.events():
            print(event)

        await conn.close()
    """

    def __init__(self, config: ConnectionConfig) -> None:
        self._config = config
        self._ws: Any = None
        self._connected = False
        self._event_callbacks: list[Callable[..., Any]] = []

    @property
    def connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        """Open the WebSocket connection."""
        import websockets

        url = self._config.url
        if url.startswith("http://"):
            url = "ws://" + url[7:]
        elif url.startswith("https://"):
            url = "wss://" + url[8:]
        if not url.endswith("/roar/ws"):
            url = url.rstrip("/") + "/roar/ws"

        self._ws = await websockets.connect(
            url,
            open_timeout=self._config.timeout_ms / 1000,
            additional_headers={"X-ROAR-Protocol": "1.0"},
        )
        self._connected = True
        logger.info("WebSocket connected to %s", url)

    async def send(self, message: ROARMessage) -> ROARMessage:
        """Send a message and wait for a response."""
        if not self._ws or not self._connected:
            raise ConnectionError("WebSocket not connected")

        payload = json.dumps(message.model_dump(by_alias=True))
        await self._ws.send(payload)
        response_raw = await asyncio.wait_for(
            self._ws.recv(),
            timeout=self._config.timeout_ms / 1000,
        )
        data = json.loads(response_raw)
        return ROARMessage.model_validate(data)

    async def events(self) -> AsyncIterator[Dict[str, Any]]:
        """Yield incoming events/messages from the WebSocket."""
        if not self._ws or not self._connected:
            raise ConnectionError("WebSocket not connected")

        try:
            async for raw in self._ws:
                try:
                    data = json.loads(raw)
                    yield data
                except json.JSONDecodeError:
                    logger.warning("Non-JSON WebSocket frame: %s", raw[:100])
        except Exception:
            self._connected = False
            raise

    async def close(self) -> None:
        """Close the WebSocket connection."""
        if self._ws:
            await self._ws.close()
            self._connected = False
            logger.info("WebSocket connection closed")
