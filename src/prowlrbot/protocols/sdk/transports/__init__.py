# -*- coding: utf-8 -*-
"""ROAR Transport Layer — dispatch messages over HTTP, WebSocket, stdio, or gRPC.

Each transport implements the same async interface:
    async def send(config, message) -> ROARMessage  # request-response
    async def connect(config) -> Connection          # persistent connection

Transport selection is based on ConnectionConfig.transport.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...roar import ConnectionConfig, ROARMessage, TransportType

if TYPE_CHECKING:
    pass


async def send_message(
    config: ConnectionConfig,
    message: ROARMessage,
    secret: str = "",
) -> ROARMessage:
    """Send a ROAR message over the configured transport and return the response.

    This is the main dispatch function. It selects the appropriate transport
    based on ``config.transport`` and handles signing/verification.

    Args:
        config: Connection configuration with transport type and URL.
        message: The ROAR message to send.
        secret: Signing secret (used for verification of response).

    Returns:
        The response ROARMessage from the remote agent.

    Raises:
        ValueError: If the transport type is not supported.
        ConnectionError: If the transport fails to connect.
    """
    if config.transport == TransportType.HTTP:
        from .http import http_send

        return await http_send(config, message)
    elif config.transport == TransportType.WEBSOCKET:
        from .websocket import websocket_send

        return await websocket_send(config, message)
    elif config.transport == TransportType.STDIO:
        from .stdio import stdio_send

        return await stdio_send(config, message)
    elif config.transport == TransportType.GRPC:
        raise NotImplementedError(
            "gRPC transport is planned for a future release. "
            "Use HTTP or WebSocket for now.",
        )
    else:
        raise ValueError(f"Unsupported transport: {config.transport}")
