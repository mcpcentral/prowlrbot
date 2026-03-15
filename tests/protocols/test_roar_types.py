# -*- coding: utf-8 -*-
"""Tests for ROAR Protocol type conformance and cross-SDK compatibility."""

import hashlib
import hmac
import json

import pytest

from prowlrbot.protocols.roar import (
    A2AAdapter,
    AgentCapability,
    AgentCard,
    AgentDirectory,
    AgentIdentity,
    ConnectionConfig,
    MCPAdapter,
    MessageIntent,
    ROARMessage,
    StreamEvent,
    StreamEventType,
    TransportType,
)


class TestAgentIdentity:
    """Test Layer 1: Identity."""

    def test_auto_generated_did(self):
        """DID is auto-generated from display_name and agent_type."""
        identity = AgentIdentity(display_name="code-reviewer")
        assert identity.did.startswith("did:roar:agent:code-reviewer-")
        assert len(identity.did) > len("did:roar:agent:code-reviewer-")

    def test_custom_did(self):
        """Custom DID is preserved when provided."""
        identity = AgentIdentity(did="did:web:example.com", display_name="ext")
        assert identity.did == "did:web:example.com"

    def test_agent_types(self):
        """All four agent types generate correct DID prefix."""
        for agent_type in ("agent", "tool", "human", "ide"):
            identity = AgentIdentity(
                display_name="test",
                agent_type=agent_type,
            )
            assert f"did:roar:{agent_type}:" in identity.did

    def test_public_key_optional(self):
        """public_key field is optional and defaults to None."""
        identity = AgentIdentity(display_name="test")
        assert identity.public_key is None

        identity_with_key = AgentIdentity(
            display_name="test",
            public_key="abcdef1234567890",
        )
        assert identity_with_key.public_key == "abcdef1234567890"

    def test_slug_truncation(self):
        """Long display names are truncated to 20 chars in slug."""
        long_name = "a" * 50
        identity = AgentIdentity(display_name=long_name)
        # Slug part (between agent_type: and -uuid) should be max 20 chars
        parts = identity.did.split(":")
        slug_and_uuid = parts[-1]  # e.g. "aaaaaaaaaaaaaaaaaaa-a1b2c3d4"
        slug = slug_and_uuid.rsplit("-", 1)[0]
        assert len(slug) <= 20


class TestMessageIntent:
    """Test that MessageIntent has exactly 7 values matching the spec."""

    def test_all_intents(self):
        expected = {
            "execute",
            "delegate",
            "update",
            "ask",
            "respond",
            "notify",
            "discover",
        }
        actual = {intent.value for intent in MessageIntent}
        assert actual == expected

    def test_intent_count(self):
        assert len(MessageIntent) == 7


class TestROARMessage:
    """Test Layer 4: Exchange."""

    def setup_method(self):
        self.alice = AgentIdentity(display_name="alice")
        self.bob = AgentIdentity(display_name="bob")

    def test_message_creation(self):
        msg = ROARMessage(
            **{"from": self.alice, "to": self.bob},
            intent=MessageIntent.DELEGATE,
            payload={"task": "review"},
        )
        assert msg.roar == "1.0"
        assert msg.id.startswith("msg_")
        assert msg.from_identity.display_name == "alice"
        assert msg.to_identity.display_name == "bob"
        assert msg.intent == MessageIntent.DELEGATE
        assert msg.payload == {"task": "review"}

    def test_sign_and_verify(self):
        msg = ROARMessage(
            **{"from": self.alice, "to": self.bob},
            intent=MessageIntent.ASK,
            payload={"question": "deploy?"},
        )
        msg.sign("test-secret")
        assert msg.auth["signature"].startswith("hmac-sha256:")
        assert msg.verify("test-secret")
        assert not msg.verify("wrong-secret")

    def test_signing_canonical_body(self):
        """Verify the exact canonical body used for signing.

        This is the cross-SDK compatibility test — TypeScript MUST produce
        the same canonical body for the same message fields.
        The canonical body covers: id, from, to, intent, payload, context, timestamp.
        """
        msg = ROARMessage(
            **{"from": self.alice, "to": self.bob},
            intent=MessageIntent.EXECUTE,
            payload={"action": "test", "params": {"x": 1}},
        )
        # Sign first to populate auth.timestamp
        msg.sign("cross-sdk-secret")

        # Manually compute what the canonical body should be
        expected_body = json.dumps(
            {
                "id": msg.id,
                "from": self.alice.did,
                "to": self.bob.did,
                "intent": "execute",
                "payload": {"action": "test", "params": {"x": 1}},
                "context": {},
                "timestamp": msg.auth["timestamp"],
            },
            sort_keys=True,
        )
        sig_hex = msg.auth["signature"].split(":")[1]

        # Independently compute HMAC
        expected_sig = hmac.new(
            b"cross-sdk-secret",
            expected_body.encode(),
            hashlib.sha256,
        ).hexdigest()
        assert sig_hex == expected_sig

    def test_context_preserved(self):
        msg = ROARMessage(
            **{"from": self.alice, "to": self.bob},
            intent=MessageIntent.RESPOND,
            payload={"result": "ok"},
            context={"in_reply_to": "msg_abc123", "protocol": "a2a"},
        )
        assert msg.context["in_reply_to"] == "msg_abc123"
        assert msg.context["protocol"] == "a2a"


class TestStreamEventType:
    """Test that StreamEventType has exactly 8 values matching the spec."""

    def test_all_event_types(self):
        expected = {
            "tool_call",
            "mcp_request",
            "reasoning",
            "task_update",
            "monitor_alert",
            "agent_status",
            "checkpoint",
            "world_update",
        }
        actual = {t.value for t in StreamEventType}
        assert actual == expected

    def test_event_type_count(self):
        assert len(StreamEventType) == 8


class TestStreamEvent:
    """Test Layer 5: Stream."""

    def test_event_creation(self):
        event = StreamEvent(
            type=StreamEventType.REASONING,
            source="did:roar:agent:planner-abc",
            session_id="sess_001",
            data={"step": 1, "thought": "analyzing"},
        )
        assert event.type == StreamEventType.REASONING
        assert event.source == "did:roar:agent:planner-abc"
        assert event.data["step"] == 1


class TestTransportType:
    """Test Layer 3: Connect."""

    def test_all_transports(self):
        expected = {"stdio", "http", "websocket", "grpc"}
        actual = {t.value for t in TransportType}
        assert actual == expected


class TestAgentDirectory:
    """Test Layer 2: Discovery."""

    def test_register_and_lookup(self):
        directory = AgentDirectory()
        identity = AgentIdentity(
            display_name="summarizer",
            capabilities=["text-summary"],
        )
        card = AgentCard(
            identity=identity,
            description="Summarizes text",
            endpoints={"http": "http://localhost:9001"},
        )
        entry = directory.register(card)
        assert entry.agent_card.identity.did == identity.did

        found = directory.lookup(identity.did)
        assert found is not None
        assert found.agent_card.description == "Summarizes text"

    def test_search_by_capability(self):
        directory = AgentDirectory()
        card1 = AgentCard(
            identity=AgentIdentity(
                display_name="a",
                capabilities=["code-review"],
            ),
        )
        card2 = AgentCard(
            identity=AgentIdentity(
                display_name="b",
                capabilities=["translation"],
            ),
        )
        directory.register(card1)
        directory.register(card2)

        results = directory.search("code-review")
        assert len(results) == 1
        assert results[0].agent_card.identity.display_name == "a"

    def test_unregister(self):
        directory = AgentDirectory()
        identity = AgentIdentity(display_name="temp")
        card = AgentCard(identity=identity)
        directory.register(card)
        assert directory.unregister(identity.did)
        assert directory.lookup(identity.did) is None
        assert not directory.unregister("nonexistent")


class TestMCPAdapter:
    """Test MCP backward compatibility adapter."""

    def test_mcp_to_roar(self):
        agent = AgentIdentity(display_name="caller")
        msg = MCPAdapter.mcp_to_roar("read_file", {"path": "/tmp/test"}, agent)
        assert msg.intent == MessageIntent.EXECUTE
        assert msg.payload["action"] == "read_file"
        assert msg.payload["params"] == {"path": "/tmp/test"}
        assert msg.to_identity.agent_type == "tool"

    def test_roar_to_mcp(self):
        agent = AgentIdentity(display_name="caller")
        msg = MCPAdapter.mcp_to_roar("query_db", {"sql": "SELECT 1"}, agent)
        result = MCPAdapter.roar_to_mcp(msg)
        assert result["tool"] == "query_db"
        assert result["params"] == {"sql": "SELECT 1"}


class TestA2AAdapter:
    """Test A2A backward compatibility adapter."""

    def test_a2a_task_to_roar(self):
        from_agent = AgentIdentity(display_name="orchestrator")
        to_agent = AgentIdentity(display_name="researcher")
        task = {"query": "latest AI news", "max_results": 10}

        msg = A2AAdapter.a2a_task_to_roar(task, from_agent, to_agent)
        assert msg.intent == MessageIntent.DELEGATE
        assert msg.payload == task
        assert msg.context["protocol"] == "a2a"

    def test_roar_to_a2a(self):
        from_agent = AgentIdentity(display_name="orchestrator")
        to_agent = AgentIdentity(display_name="researcher")
        task = {"query": "test"}

        msg = A2AAdapter.a2a_task_to_roar(task, from_agent, to_agent)
        result = A2AAdapter.roar_to_a2a(msg)
        assert result["from"] == from_agent.did
        assert result["to"] == to_agent.did
        assert result["payload"] == task
