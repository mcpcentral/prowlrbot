# -*- coding: utf-8 -*-
"""ACP (Agent Client Protocol) server — expose ProwlrBot as an ACP agent.

When running, any IDE with ACP support (VS Code, Zed, JetBrains) can use
ProwlrBot as its coding agent via JSON-RPC 2.0 over stdio.

Usage:
    prowlr acp   # start ACP server on stdio
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Maximum input line length (1 MB) to prevent memory exhaustion.
_MAX_LINE_LENGTH = 1_048_576


class ACPServer:
    """Minimal ACP JSON-RPC 2.0 server over stdio."""

    def __init__(self, runner=None) -> None:
        self._session_id: Optional[str] = None
        self._initialized = False
        self._runner = runner

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Route a JSON-RPC request to the appropriate handler."""
        # Validate JSON-RPC 2.0 structure
        if request.get("jsonrpc") != "2.0":
            return self._error_response(
                request.get("id"),
                -32600,
                "Invalid Request: missing or invalid jsonrpc version",
            )

        method = request.get("method", "")
        if not isinstance(method, str) or not method:
            return self._error_response(
                request.get("id"), -32600, "Invalid Request: missing or invalid method"
            )

        params = request.get("params", {})
        req_id = request.get("id")

        handlers = {
            "initialize": self._handle_initialize,
            "session/new": self._handle_session_new,
            "session/prompt": self._handle_session_prompt,
            "session/cancel": self._handle_session_cancel,
            "shutdown": self._handle_shutdown,
        }

        handler = handlers.get(method)
        if handler is None:
            return self._error_response(req_id, -32601, "Method not found")

        try:
            result = await handler(params)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except Exception as exc:
            logger.exception("ACP handler error for method %s", method)
            return self._error_response(req_id, -32603, "Internal error")

    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ACP initialize handshake."""
        self._initialized = True
        return {
            "name": "ProwlrBot",
            "version": "1.0.0",
            "capabilities": {
                "prompting": True,
                "streaming": True,
                "tools": True,
            },
        }

    async def _handle_session_new(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new ACP session."""
        import uuid

        self._session_id = f"acp_{uuid.uuid4().hex[:8]}"
        return {"session_id": self._session_id}

    async def _handle_session_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process a prompt in the current session."""
        prompt = params.get("prompt", "")
        if not self._session_id:
            return {
                "error": "No active session. Call session/new first.",
                "status": "error",
            }

        if self._runner is None:
            return {
                "session_id": self._session_id,
                "response": "No runner configured.",
                "status": "no_runner",
            }

        try:
            from agentscope_runtime.engine.schemas.agent_schemas import (
                AgentRequest,
                Message,
                TextContent,
            )

            request = AgentRequest(
                input=[Message(role="user", content=[TextContent(text=str(prompt))])],
                session_id=self._session_id,
                user_id="acp_user",
            )

            last_text = ""
            async for agent_msg, _is_last in self._runner.stream_query(request):
                text = getattr(agent_msg, "content", None)
                if isinstance(text, str):
                    last_text = text
                elif hasattr(agent_msg, "get_text_content"):
                    last_text = agent_msg.get_text_content() or last_text

            return {
                "session_id": self._session_id,
                "response": last_text,
                "status": "ok",
            }
        except Exception:
            logger.exception("ACP prompt processing error")
            return {
                "session_id": self._session_id,
                "response": "Internal processing error.",
                "status": "error",
            }

    async def _handle_session_cancel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel the current session."""
        self._session_id = None
        return {"status": "cancelled"}

    async def _handle_shutdown(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Shut down the ACP server."""
        self._initialized = False
        return {"status": "shutdown"}

    @staticmethod
    def _error_response(req_id: Any, code: int, message: str) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message},
        }

    async def run_stdio(self) -> None:
        """Run the ACP server reading JSON-RPC from stdin, writing to stdout."""
        import asyncio

        loop = asyncio.get_running_loop()
        while True:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break

            # Enforce max line length (DoS protection)
            if len(line) > _MAX_LINE_LENGTH:
                error = self._error_response(None, -32600, "Request too large")
                sys.stdout.write(json.dumps(error) + "\n")
                sys.stdout.flush()
                continue

            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                error = self._error_response(None, -32700, "Parse error")
                sys.stdout.write(json.dumps(error) + "\n")
                sys.stdout.flush()
                continue
            response = await self.handle_request(request)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
