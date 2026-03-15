# -*- coding: utf-8 -*-
"""Integration tests for protocol stack: ACP server → agent runner → response."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from prowlrbot.protocols.acp_server import ACPServer


class TestACPFullLifecycle:
    """End-to-end ACP lifecycle: init → session → prompt → shutdown."""

    async def test_full_lifecycle_with_mock_runner(self):
        """Test complete ACP lifecycle with a mocked AgentRunner."""

        async def _stream(request):
            msg = MagicMock()
            msg.content = "The answer is 4."
            yield msg, True

        mock_runner = MagicMock()
        mock_runner.stream_query = _stream

        server = ACPServer(runner=mock_runner)

        # 1. Initialize
        resp = await server.handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        )
        assert resp["result"]["name"] == "ProwlrBot"
        assert resp["result"]["capabilities"]["prompting"] is True

        # 2. Create session
        resp = await server.handle_request(
            {"jsonrpc": "2.0", "id": 2, "method": "session/new", "params": {}},
        )
        session_id = resp["result"]["session_id"]
        assert session_id.startswith("acp_")

        # 3. Send prompt
        resp = await server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "session/prompt",
                "params": {"prompt": "What is 2+2?"},
            },
        )
        assert resp["result"]["session_id"] == session_id
        assert "4" in resp["result"]["response"]

        # 4. Shutdown
        resp = await server.handle_request(
            {"jsonrpc": "2.0", "id": 4, "method": "shutdown", "params": {}},
        )
        assert resp["result"]["status"] == "shutdown"

    async def test_prompt_before_session_fails(self):
        """Sending a prompt without creating a session should fail."""
        server = ACPServer()
        await server.handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        )

        resp = await server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "session/prompt",
                "params": {"prompt": "Hello"},
            },
        )
        result = resp["result"]
        assert result.get("status") == "error" or "error" in result

    async def test_multiple_prompts_in_session(self):
        """Multiple prompts in a single session should all work."""
        call_count = 0

        async def _stream(request):
            nonlocal call_count
            call_count += 1
            msg = MagicMock()
            msg.content = f"Response #{call_count}"
            yield msg, True

        mock_runner = MagicMock()
        mock_runner.stream_query = _stream

        server = ACPServer(runner=mock_runner)
        await server.handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        )
        await server.handle_request(
            {"jsonrpc": "2.0", "id": 2, "method": "session/new", "params": {}},
        )

        for i in range(3):
            resp = await server.handle_request(
                {
                    "jsonrpc": "2.0",
                    "id": 10 + i,
                    "method": "session/prompt",
                    "params": {"prompt": f"Question {i}"},
                },
            )
            assert resp["result"]["status"] == "ok"

        assert call_count == 3


class TestACPErrorHandling:
    """Test ACP error handling paths."""

    async def test_runner_exception_returns_error(self):
        """If the runner raises, ACP should return an error response."""

        async def _fail_stream(request):
            raise RuntimeError("Model unavailable")
            yield  # make it an async generator

        mock_runner = MagicMock()
        mock_runner.stream_query = _fail_stream

        server = ACPServer(runner=mock_runner)
        await server.handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        )
        await server.handle_request(
            {"jsonrpc": "2.0", "id": 2, "method": "session/new", "params": {}},
        )

        resp = await server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "session/prompt",
                "params": {"prompt": "test"},
            },
        )
        assert resp["result"]["status"] == "error"
        assert resp["result"][
            "response"
        ]  # error message present (generic, not leaking internals)

    async def test_unknown_method(self):
        """Unknown JSON-RPC methods should return error code -32601."""
        server = ACPServer()
        resp = await server.handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "bogus/foo", "params": {}},
        )
        assert "error" in resp
        assert resp["error"]["code"] == -32601
