# -*- coding: utf-8 -*-
"""ROAR HTTP Transport — request-response over HTTP/HTTPS.

Uses httpx for async HTTP. Messages are sent as JSON POST bodies
to the endpoint URL. Responses are returned synchronously.

Ref: MCP uses "Streamable HTTP" (2025-11-25 spec), A2A uses HTTP POST.
ROAR HTTP transport is compatible with both patterns.
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Dict

import httpx

from ...roar import ConnectionConfig, ROARMessage

logger = logging.getLogger(__name__)


async def http_send(
    config: ConnectionConfig,
    message: ROARMessage,
) -> ROARMessage:
    """Send a ROAR message via HTTP POST and return the response.

    Args:
        config: Connection config with URL and auth details.
        message: The message to send.

    Returns:
        The response ROARMessage parsed from JSON.

    Raises:
        ConnectionError: If the HTTP request fails.
    """
    url = config.url.rstrip("/")
    if not url:
        raise ConnectionError(
            "HTTP transport requires a URL in ConnectionConfig",
        )

    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-ROAR-Protocol": message.roar,
    }

    # Add auth header based on method
    if config.auth_method == "jwt" and config.secret:
        headers["Authorization"] = f"Bearer {config.secret}"
    elif config.auth_method == "hmac":
        # HMAC auth is in the message body (auth field), not headers
        pass

    payload = message.model_dump(by_alias=True)

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(config.timeout_ms / 1000),
    ) as client:
        try:
            response = await client.post(
                f"{url}/roar/message",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return ROARMessage.model_validate(data)
        except httpx.ConnectError as exc:
            raise ConnectionError(
                f"Failed to connect to {url}: {exc}",
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise ConnectionError(
                f"HTTP {exc.response.status_code} from {url}: "
                f"{exc.response.text[:200]}",
            ) from exc


async def http_stream_events(
    config: ConnectionConfig,
    session_id: str = "",
) -> AsyncIterator[Dict[str, Any]]:
    """Subscribe to SSE events from a ROAR agent via HTTP.

    Uses Server-Sent Events (SSE) — compatible with A2A's streaming
    and MCP's Streamable HTTP transport.

    Args:
        config: Connection config with URL.
        session_id: Optional session ID to filter events.

    Yields:
        Parsed event data dictionaries.
    """
    url = config.url.rstrip("/")
    params: Dict[str, str] = {}
    if session_id:
        params["session_id"] = session_id

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(None),  # No timeout for SSE
    ) as client:
        async with client.stream(
            "GET",
            f"{url}/roar/events",
            params=params,
            headers={"Accept": "text/event-stream"},
        ) as response:
            response.raise_for_status()
            buffer = ""
            async for chunk in response.aiter_text():
                buffer += chunk
                while "\n\n" in buffer:
                    event_str, buffer = buffer.split("\n\n", 1)
                    event = _parse_sse_event(event_str)
                    if event:
                        yield event


def _parse_sse_event(raw: str) -> Dict[str, Any] | None:
    """Parse a single SSE event block into a dict."""
    import json

    data_lines = []
    event_type = "message"

    for line in raw.strip().split("\n"):
        if line.startswith("data: "):
            data_lines.append(line[6:])
        elif line.startswith("event: "):
            event_type = line[7:]
        elif line.startswith(":"):
            continue  # Comment

    if not data_lines:
        return None

    data_str = "\n".join(data_lines)
    try:
        data = json.loads(data_str)
    except json.JSONDecodeError:
        data = {"text": data_str}

    return {"event": event_type, "data": data}
