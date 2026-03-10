# -*- coding: utf-8 -*-
"""Tests for ROAR Protocol Phase 6 — Protocol Adapters."""
from __future__ import annotations

import unittest

from src.prowlrbot.protocols.roar import (
    AgentCard,
    AgentIdentity,
    MessageIntent,
    ROARMessage,
)
from src.prowlrbot.protocols.sdk.adapters.a2a import A2AFullAdapter
from src.prowlrbot.protocols.sdk.adapters.detect import ProtocolType, detect_protocol
from src.prowlrbot.protocols.sdk.adapters.mcp import MCPFullAdapter


class TestProtocolDetection(unittest.TestCase):
    """Tests for protocol auto-detection."""

    def test_detect_roar(self):
        msg = {"roar": "1.0", "intent": "execute", "payload": {}}
        assert detect_protocol(msg) == ProtocolType.ROAR

    def test_detect_mcp_tools_list(self):
        msg = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        assert detect_protocol(msg) == ProtocolType.MCP

    def test_detect_mcp_tools_call(self):
        msg = {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {}}
        assert detect_protocol(msg) == ProtocolType.MCP

    def test_detect_a2a_tasks_send(self):
        msg = {"jsonrpc": "2.0", "id": 3, "method": "tasks/send", "params": {}}
        assert detect_protocol(msg) == ProtocolType.A2A

    def test_detect_a2a_task_envelope(self):
        msg = {"id": "task-1", "status": {"state": "completed"}, "artifacts": []}
        assert detect_protocol(msg) == ProtocolType.A2A

    def test_detect_unknown(self):
        msg = {"foo": "bar"}
        assert detect_protocol(msg) == ProtocolType.UNKNOWN

    def test_detect_mcp_result(self):
        msg = {"jsonrpc": "2.0", "id": 1, "result": {"tools": []}}
        assert detect_protocol(msg) == ProtocolType.MCP

    def test_detect_a2a_result(self):
        msg = {"jsonrpc": "2.0", "id": 1, "result": {"id": "t-1", "status": {"state": "working"}}}
        assert detect_protocol(msg) == ProtocolType.A2A


class TestMCPAdapter(unittest.TestCase):
    """Tests for MCP ↔ ROAR bidirectional translation."""

    def test_mcp_to_roar_tools_list(self):
        mcp_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }
        roar = MCPFullAdapter.mcp_to_roar(mcp_msg)
        assert roar.intent == MessageIntent.DISCOVER
        assert roar.payload["mcp_method"] == "tools/list"
        assert roar.context["protocol"] == "mcp"

    def test_mcp_to_roar_tools_call(self):
        mcp_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "shell", "arguments": {"command": "ls"}},
        }
        roar = MCPFullAdapter.mcp_to_roar(mcp_msg)
        assert roar.intent == MessageIntent.EXECUTE
        assert roar.payload["mcp_params"]["name"] == "shell"

    def test_roar_to_mcp(self):
        identity = AgentIdentity(display_name="test")
        roar = ROARMessage(
            **{"from": identity, "to": identity},
            intent=MessageIntent.EXECUTE,
            payload={
                "mcp_method": "tools/call",
                "mcp_params": {"name": "shell", "arguments": {"command": "ls"}},
            },
            context={"jsonrpc_id": 42},
        )
        mcp = MCPFullAdapter.roar_to_mcp(roar)
        assert mcp["jsonrpc"] == "2.0"
        assert mcp["method"] == "tools/call"
        assert mcp["id"] == 42
        assert mcp["params"]["name"] == "shell"

    def test_mcp_result_to_roar(self):
        result = {"jsonrpc": "2.0", "id": 1, "result": {"tools": [{"name": "shell"}]}}
        roar = MCPFullAdapter.mcp_result_to_roar(result)
        assert roar.intent == MessageIntent.RESPOND
        assert roar.payload["mcp_result"] == {"tools": [{"name": "shell"}]}
        assert not roar.payload["mcp_is_error"]

    def test_mcp_error_to_roar(self):
        result = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32601, "message": "Method not found"},
        }
        roar = MCPFullAdapter.mcp_result_to_roar(result)
        assert roar.payload["mcp_is_error"]

    def test_round_trip_mcp_roar_mcp(self):
        original = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "browser", "arguments": {"url": "https://example.com"}},
        }
        roar = MCPFullAdapter.mcp_to_roar(original)
        back = MCPFullAdapter.roar_to_mcp(roar)
        assert back["method"] == "tools/call"
        assert back["params"]["name"] == "browser"


class TestA2AAdapter(unittest.TestCase):
    """Tests for A2A ↔ ROAR bidirectional translation."""

    def test_a2a_send_to_roar(self):
        a2a_req = {
            "jsonrpc": "2.0",
            "id": "req-1",
            "method": "tasks/send",
            "params": {
                "id": "task-1",
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": "Review this PR"}],
                },
                "sessionId": "sess-42",
            },
        }
        roar = A2AFullAdapter.a2a_send_to_roar(a2a_req)
        assert roar.intent == MessageIntent.DELEGATE
        assert roar.payload["a2a_task_id"] == "task-1"
        assert roar.context["protocol"] == "a2a"

    def test_roar_to_a2a_send(self):
        identity = AgentIdentity(display_name="test")
        roar = ROARMessage(
            **{"from": identity, "to": identity},
            intent=MessageIntent.DELEGATE,
            payload={"task": "Review PR #42", "a2a_task_id": "task-99"},
        )
        a2a = A2AFullAdapter.roar_to_a2a_send(roar)
        assert a2a["method"] == "tasks/send"
        assert a2a["params"]["id"] == "task-99"
        assert a2a["params"]["message"]["role"] == "user"

    def test_a2a_task_to_roar_response(self):
        task = {
            "id": "task-1",
            "status": {"state": "completed"},
            "artifacts": [{"parts": [{"type": "text", "text": "LGTM"}]}],
        }
        roar = A2AFullAdapter.a2a_task_to_roar_response(task)
        assert roar.intent == MessageIntent.RESPOND
        assert roar.payload["a2a_status"] == "completed"
        assert len(roar.payload["a2a_artifacts"]) == 1

    def test_a2a_sse_to_stream_event(self):
        sse = {
            "id": "task-1",
            "status": {"state": "working", "message": "Processing..."},
        }
        event = A2AFullAdapter.a2a_sse_to_stream_event(
            sse, source_did="did:roar:agent:a2a-12345678"
        )
        assert event.type == "task_update"
        assert event.data["status"] == "working"
        assert event.data["protocol"] == "a2a"

    def test_a2a_card_to_roar(self):
        a2a_card = {
            "name": "Code Reviewer",
            "description": "Reviews code for quality",
            "url": "https://agent.example.com/a2a",
            "skills": [
                {"id": "review", "name": "code-review"},
                {"id": "test", "name": "testing"},
            ],
        }
        roar_card = A2AFullAdapter.a2a_card_to_roar(a2a_card)
        assert roar_card.identity.display_name == "Code Reviewer"
        assert "code-review" in roar_card.skills
        assert roar_card.endpoints["http"] == "https://agent.example.com/a2a"

    def test_roar_card_to_a2a(self):
        identity = AgentIdentity(display_name="My Agent")
        card = AgentCard(
            identity=identity,
            description="Test agent",
            skills=["code-review", "testing"],
            endpoints={"http": "http://localhost:8089", "websocket": "ws://localhost:8089/ws"},
        )
        a2a = A2AFullAdapter.roar_card_to_a2a(card)
        assert a2a["name"] == "My Agent"
        assert a2a["capabilities"]["streaming"] is True
        assert len(a2a["skills"]) == 2

    def test_task_state_mapping(self):
        """Verify all A2A v0.3.0 states map correctly."""
        expected = {
            "submitted": "pending",
            "working": "running",
            "input-required": "blocked",
            "completed": "completed",
            "failed": "failed",
            "canceled": "cancelled",
            "rejected": "rejected",
        }
        assert A2AFullAdapter.TASK_STATE_MAP == expected


if __name__ == "__main__":
    unittest.main()
