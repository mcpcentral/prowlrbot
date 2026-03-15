# -*- coding: utf-8 -*-
"""Tests for ACP JSON-RPC 2.0 server."""

import pytest
from prowlrbot.protocols.acp_server import ACPServer


@pytest.fixture
def server():
    return ACPServer()


class TestACPLifecycle:
    async def test_initialize_returns_capabilities(self, server):
        resp = await server.handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        )
        assert resp["result"]["name"] == "ProwlrBot"
        assert resp["result"]["capabilities"]["prompting"] is True

    async def test_session_new_returns_session_id(self, server):
        await server.handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        )
        resp = await server.handle_request(
            {"jsonrpc": "2.0", "id": 2, "method": "session/new", "params": {}},
        )
        assert "session_id" in resp["result"]
        assert resp["result"]["session_id"].startswith("acp_")

    async def test_session_cancel(self, server):
        resp = await server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "session/cancel",
                "params": {},
            },
        )
        assert resp["result"]["status"] == "cancelled"

    async def test_shutdown(self, server):
        resp = await server.handle_request(
            {"jsonrpc": "2.0", "id": 4, "method": "shutdown", "params": {}},
        )
        assert resp["result"]["status"] == "shutdown"

    async def test_unknown_method_returns_error(self, server):
        resp = await server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "bogus/method",
                "params": {},
            },
        )
        assert "error" in resp
        assert resp["error"]["code"] == -32601


class TestACPPrompt:
    async def test_prompt_without_session_returns_error(self, server):
        resp = await server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "session/prompt",
                "params": {"prompt": "hello"},
            },
        )
        assert resp["result"].get("status") == "error"

    async def test_prompt_without_runner_returns_no_runner(self, server):
        """With session but no runner, should return no_runner status."""
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
                "params": {"prompt": "What is 2+2?"},
            },
        )
        result = resp["result"]
        assert "session_id" in result
        assert result["status"] == "no_runner"

    async def test_prompt_with_mock_runner(self):
        """With a mock runner, should return the runner's response."""
        from unittest.mock import MagicMock

        async def _stream(request):
            msg = MagicMock()
            msg.content = f"Mock answer to: {request.input[0].content[0].text}"
            yield msg, True

        class MockRunner:
            async def stream_query(self, request):
                async for item in _stream(request):
                    yield item

        server = ACPServer(runner=MockRunner())
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
                "params": {"prompt": "What is 2+2?"},
            },
        )
        result = resp["result"]
        assert result["status"] == "ok"
        assert "Mock answer" in result["response"]

    async def test_prompt_runner_exception_returns_error(self):
        """If runner raises, should return error status."""

        class FailRunner:
            async def stream_query(self, request):
                raise RuntimeError("Model unavailable")
                yield  # make it an async generator

        server = ACPServer(runner=FailRunner())
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
                "params": {"prompt": "hello"},
            },
        )
        result = resp["result"]
        assert result["status"] == "error"
        assert result["response"] == "Internal processing error."
