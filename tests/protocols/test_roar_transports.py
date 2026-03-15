# -*- coding: utf-8 -*-
"""Tests for ROAR Protocol Phase 2 — Transport Layer & Server/Client Integration."""

from __future__ import annotations

import asyncio
import json
import unittest

from prowlrbot.protocols.roar import (
    AgentCard,
    AgentDirectory,
    AgentIdentity,
    ConnectionConfig,
    DiscoveryEntry,
    MessageIntent,
    ROARMessage,
    TransportType,
)
from prowlrbot.protocols.sdk.client import ROARClient
from prowlrbot.protocols.sdk.server import ROARServer


class TestROARServer(unittest.TestCase):
    """Tests for ROARServer message dispatch and card generation."""

    def setUp(self):
        self.identity = AgentIdentity(
            display_name="test-server",
            agent_type="service",
        )
        self.server = ROARServer(
            self.identity,
            host="127.0.0.1",
            port=9090,
            description="Test server",
            skills=["code-review", "testing"],
            channels=["http", "websocket"],
            signing_secret="test-secret",
        )

    def test_server_identity(self):
        assert self.server.identity == self.identity
        assert self.server.host == "127.0.0.1"
        assert self.server.port == 9090

    def test_get_card(self):
        card = self.server.get_card()
        assert isinstance(card, AgentCard)
        assert card.identity == self.identity
        assert card.description == "Test server"
        assert "code-review" in card.skills
        assert card.endpoints["http"] == "http://127.0.0.1:9090"

    def test_register_with_directory(self):
        directory = AgentDirectory()
        entry = self.server.register_with_directory(directory)
        assert isinstance(entry, DiscoveryEntry)
        assert entry.agent_card.identity.did == self.identity.did

        # Verify lookup works
        found = directory.lookup(self.identity.did)
        assert found is not None
        assert found.agent_card.description == "Test server"

    def test_handler_registration_decorator(self):
        @self.server.on(MessageIntent.EXECUTE)
        def handle_execute(msg: ROARMessage) -> ROARMessage:
            return ROARMessage(
                **{"from": self.identity, "to": msg.from_identity},
                intent=MessageIntent.RESPOND,
                payload={"result": "done"},
            )

        assert MessageIntent.EXECUTE in self.server._handlers

    def test_handle_message_dispatches(self):
        sender = AgentIdentity(display_name="sender")

        @self.server.on(MessageIntent.EXECUTE)
        async def handle_execute(msg: ROARMessage) -> ROARMessage:
            return ROARMessage(
                **{"from": self.server.identity, "to": msg.from_identity},
                intent=MessageIntent.RESPOND,
                payload={"result": msg.payload.get("task")},
            )

        incoming = ROARMessage(
            **{"from": sender, "to": self.identity},
            intent=MessageIntent.EXECUTE,
            payload={"task": "run-tests"},
        )

        response = asyncio.run(self.server.handle_message(incoming))
        assert response.intent == MessageIntent.RESPOND
        assert response.payload["result"] == "run-tests"

    def test_handle_message_sync_handler(self):
        sender = AgentIdentity(display_name="sender")

        @self.server.on(MessageIntent.NOTIFY)
        def handle_notify(msg: ROARMessage) -> ROARMessage:
            return ROARMessage(
                **{"from": self.server.identity, "to": msg.from_identity},
                intent=MessageIntent.RESPOND,
                payload={"ack": True},
            )

        incoming = ROARMessage(
            **{"from": sender, "to": self.identity},
            intent=MessageIntent.NOTIFY,
            payload={"event": "build_complete"},
        )

        response = asyncio.run(self.server.handle_message(incoming))
        assert response.payload["ack"] is True

    def test_handle_message_no_handler(self):
        sender = AgentIdentity(display_name="sender")
        incoming = ROARMessage(
            **{"from": sender, "to": self.identity},
            intent=MessageIntent.ASK,
            payload={"question": "who are you?"},
        )

        response = asyncio.run(self.server.handle_message(incoming))
        assert response.payload["error"] == "unhandled_intent"
        assert (
            "ASK" in response.payload["message"] or "ask" in response.payload["message"]
        )


class TestROARClientTransport(unittest.TestCase):
    """Tests for ROARClient transport selection and connection building."""

    def setUp(self):
        self.identity = AgentIdentity(display_name="test-client")
        self.client = ROARClient(self.identity, signing_secret="client-secret")

        # Register a target agent with multiple endpoints
        self.target = AgentIdentity(display_name="target-agent")
        self.target_card = AgentCard(
            identity=self.target,
            description="Target agent",
            endpoints={
                "http": "http://localhost:8089",
                "websocket": "ws://localhost:8089/roar/ws",
            },
        )
        self.client.register(
            AgentCard(identity=self.identity, description="Test client"),
        )
        self.client.directory.register(self.target_card)

    def test_best_transport_websocket_preferred(self):
        transport = self.client._best_transport(self.target.did)
        assert transport == TransportType.WEBSOCKET

    def test_best_transport_http_fallback(self):
        # Register agent with only HTTP
        http_only = AgentIdentity(display_name="http-only")
        self.client.directory.register(
            AgentCard(
                identity=http_only,
                description="HTTP only",
                endpoints={"http": "http://localhost:9000"},
            ),
        )
        transport = self.client._best_transport(http_only.did)
        assert transport == TransportType.HTTP

    def test_best_transport_unknown_agent(self):
        transport = self.client._best_transport(
            "did:roar:agent:nonexistent-12345678",
        )
        assert transport == TransportType.HTTP  # fallback

    def test_connect_builds_config(self):
        config = self.client.connect(self.target.did, TransportType.HTTP)
        assert isinstance(config, ConnectionConfig)
        assert config.url == "http://localhost:8089"
        assert config.transport == TransportType.HTTP
        assert config.auth_method == "hmac"

    def test_connect_websocket(self):
        config = self.client.connect(self.target.did, TransportType.WEBSOCKET)
        assert config.url == "ws://localhost:8089/roar/ws"
        assert config.transport == TransportType.WEBSOCKET

    def test_connect_unknown_agent_empty_url(self):
        config = self.client.connect(
            "did:roar:agent:ghost-00000000",
            TransportType.HTTP,
        )
        assert config.url == ""

    def test_send_constructs_signed_message(self):
        msg = self.client.send(
            to_agent_id=self.target.did,
            intent=MessageIntent.DELEGATE,
            content={"task": "review PR #42"},
        )
        assert isinstance(msg, ROARMessage)
        assert msg.intent == MessageIntent.DELEGATE
        assert msg.payload["task"] == "review PR #42"
        assert "signature" in msg.auth
        assert msg.auth["signature"].startswith("hmac-sha256:")

    def test_send_resolves_identity_from_directory(self):
        msg = self.client.send(
            to_agent_id=self.target.did,
            intent=MessageIntent.EXECUTE,
            content={"action": "build"},
        )
        assert msg.to_identity.display_name == "target-agent"

    def test_send_unknown_agent_creates_placeholder(self):
        msg = self.client.send(
            to_agent_id="did:roar:agent:unknown-99999999",
            intent=MessageIntent.ASK,
            content={"question": "hello?"},
        )
        assert msg.to_identity.display_name == "unknown"


class TestTransportDispatcher(unittest.TestCase):
    """Tests for the transport dispatcher routing logic."""

    def test_unsupported_transport_raises(self):
        from prowlrbot.protocols.sdk.transports import send_message

        config = ConnectionConfig(
            transport=TransportType.GRPC,
            url="grpc://localhost:50051",
        )
        identity = AgentIdentity(display_name="test")
        msg = ROARMessage(
            **{"from": identity, "to": identity},
            intent=MessageIntent.EXECUTE,
            payload={},
        )

        with self.assertRaises((ConnectionError, NotImplementedError)):
            asyncio.run(send_message(config, msg))


class TestMessageSigningCrossTransport(unittest.TestCase):
    """Verify signing is consistent regardless of transport path."""

    def test_signed_message_verifiable(self):
        identity = AgentIdentity(display_name="signer")
        client = ROARClient(identity, signing_secret="cross-transport-secret")
        target = AgentIdentity(display_name="verifier")

        msg = client.send(
            to_agent_id=target.did,
            intent=MessageIntent.EXECUTE,
            content={"action": "test", "params": {"x": 1}},
        )

        # Verify the message can be verified with the same secret
        assert msg.verify("cross-transport-secret", max_age_seconds=60)
        # And fails with wrong secret
        assert not msg.verify("wrong-secret", max_age_seconds=60)


if __name__ == "__main__":
    unittest.main()
