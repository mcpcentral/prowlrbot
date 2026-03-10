# -*- coding: utf-8 -*-
"""Protocol auto-detection — sniff incoming messages to determine format.

Examines the structure of an incoming JSON message to determine whether
it's ROAR native, MCP (JSON-RPC 2.0), or A2A protocol format, then
routes to the appropriate adapter.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional, Tuple


class ProtocolType(str, Enum):
    """Detected protocol type."""

    ROAR = "roar"
    MCP = "mcp"
    A2A = "a2a"
    UNKNOWN = "unknown"


def detect_protocol(message: Dict[str, Any]) -> ProtocolType:
    """Detect the protocol of an incoming message.

    Detection heuristics (in priority order):
    1. ROAR: Has "roar" version field and "intent" field
    2. MCP: Has "jsonrpc" field and method starts with known MCP prefix
    3. A2A: Has "jsonrpc" field and method starts with "tasks/"
    4. Generic JSON-RPC: Has "jsonrpc" but unknown method

    Args:
        message: The raw JSON message dict.

    Returns:
        The detected ProtocolType.
    """
    # ROAR native
    if "roar" in message and "intent" in message:
        return ProtocolType.ROAR

    # JSON-RPC based protocols
    if message.get("jsonrpc") == "2.0":
        method = message.get("method", "")

        # A2A methods
        if method.startswith("tasks/") or method.startswith("agent/"):
            return ProtocolType.A2A

        # MCP methods
        mcp_prefixes = (
            "tools/", "resources/", "prompts/",
            "completion/", "initialize", "notifications/",
        )
        if any(method.startswith(p) for p in mcp_prefixes):
            return ProtocolType.MCP

        # JSON-RPC result (check for A2A task structure)
        result = message.get("result", {})
        if isinstance(result, dict):
            if "status" in result and "id" in result:
                return ProtocolType.A2A
            if "tools" in result or "resources" in result:
                return ProtocolType.MCP

    # Check for A2A task envelope
    if "status" in message and "id" in message and "artifacts" in message:
        return ProtocolType.A2A

    return ProtocolType.UNKNOWN
