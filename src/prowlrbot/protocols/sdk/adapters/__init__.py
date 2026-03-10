# -*- coding: utf-8 -*-
"""ROAR Protocol SDK — Protocol Adapters (Layer 4 Bridge).

Bidirectional adapters for translating between ROAR and external protocols:
  - MCP: Tool lifecycle (list/call/result), resources, prompts
  - A2A: Agent Card, Task lifecycle (submit/working/done/failed), SSE streaming
  - ACP: Agent Communication Protocol (OpenClaw)

Each adapter provides `to_roar()` and `from_roar()` static methods for
message translation, plus protocol-specific helpers.

Auto-detection sniffs incoming messages to route them to the right adapter.
"""
from .mcp import MCPFullAdapter
from .a2a import A2AFullAdapter
from .detect import detect_protocol, ProtocolType

__all__ = [
    "MCPFullAdapter",
    "A2AFullAdapter",
    "detect_protocol",
    "ProtocolType",
]
