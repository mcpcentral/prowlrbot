# -*- coding: utf-8 -*-
"""ROAR Protocol SDK — Client for agent-to-agent communication.

Supports local (in-memory) and remote (HTTP, WebSocket, stdio) message dispatch.
Transport selection is automatic based on the target agent's registered endpoints.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from ..roar import (
    AgentCard,
    AgentDirectory,
    AgentIdentity,
    ConnectionConfig,
    DiscoveryEntry,
    MessageIntent,
    ROARMessage,
    StreamEvent,
    TransportType,
)

logger = logging.getLogger(__name__)


class ROARClient:
    """Client for discovering agents and sending ROAR messages.

    Supports both local (construct-only) and remote (transport-dispatched)
    message sending. When a target agent has registered endpoints, ``send_remote``
    dispatches over the wire. Otherwise, ``send`` constructs and signs locally.

    Usage::

        identity = AgentIdentity(display_name="my-agent")
        client = ROARClient(identity)

        # Register self
        card = AgentCard(identity=identity, description="My agent")
        client.register(card)

        # Discover other agents
        agents = client.discover(capability="code-review")

        # Send a message (local — construct and sign)
        msg = client.send(
            to_agent_id=agents[0].agent_card.identity.did,
            intent=MessageIntent.DELEGATE,
            content={"task": "review this PR"},
        )

        # Send remotely (over HTTP/WebSocket/stdio)
        response = await client.send_remote(
            to_agent_id="did:roar:agent:reviewer-abc123",
            intent=MessageIntent.DELEGATE,
            content={"task": "review this PR"},
        )
    """

    def __init__(
        self,
        identity: AgentIdentity,
        directory_url: Optional[str] = None,
        signing_secret: str = "",
    ) -> None:
        self._identity = identity
        self._directory_url = directory_url
        self._signing_secret = signing_secret or uuid.uuid4().hex
        self._directory = AgentDirectory()
        self._card: Optional[AgentCard] = None

    # -- public API -----------------------------------------------------------

    @property
    def identity(self) -> AgentIdentity:
        """Return the client's agent identity."""
        return self._identity

    @property
    def directory(self) -> AgentDirectory:
        """Return the local agent directory."""
        return self._directory

    def register(self, card: AgentCard) -> DiscoveryEntry:
        """Register this agent with the local directory.

        Args:
            card: The agent card describing this agent's capabilities.

        Returns:
            The discovery entry created for this agent.
        """
        self._card = card
        return self._directory.register(card)

    def discover(self, capability: Optional[str] = None) -> List[DiscoveryEntry]:
        """Find agents, optionally filtered by capability.

        Args:
            capability: If provided, only return agents with this capability.

        Returns:
            List of matching discovery entries.
        """
        if capability:
            return self._directory.search(capability)
        return self._directory.list_all()

    def send(
        self,
        to_agent_id: str,
        intent: MessageIntent,
        content: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> ROARMessage:
        """Create, sign, and return a ROAR message (local, no transport).

        Constructs the message locally. For actual network dispatch,
        use ``send_remote`` instead.

        Args:
            to_agent_id: DID of the target agent.
            intent: What the sender wants the receiver to do.
            content: Payload dictionary.
            context: Optional context metadata.

        Returns:
            A signed ``ROARMessage`` ready for transmission.
        """
        entry = self._directory.lookup(to_agent_id)
        to_identity = (
            entry.agent_card.identity
            if entry
            else AgentIdentity(did=to_agent_id, display_name="unknown")
        )

        msg = ROARMessage(
            **{"from": self._identity, "to": to_identity},
            intent=intent,
            payload=content,
            context=context or {},
        )
        return self._sign_message(msg)

    async def send_remote(
        self,
        to_agent_id: str,
        intent: MessageIntent,
        content: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        transport: Optional[TransportType] = None,
    ) -> ROARMessage:
        """Send a message over the wire and return the response.

        Looks up the target agent's endpoints, selects the best transport,
        dispatches the message, and returns the remote agent's response.

        Args:
            to_agent_id: DID of the target agent.
            intent: What the sender wants.
            content: Payload dictionary.
            context: Optional context metadata.
            transport: Preferred transport (auto-selects if None).

        Returns:
            The response ``ROARMessage`` from the remote agent.

        Raises:
            ConnectionError: If no endpoint is found or transport fails.
        """
        # Build and sign the message
        msg = self.send(to_agent_id, intent, content, context)

        # Resolve connection config
        config = self.connect(
            to_agent_id,
            transport=transport or self._best_transport(to_agent_id),
        )

        if not config.url:
            raise ConnectionError(
                f"No endpoint found for agent {to_agent_id}. "
                "Register the agent or provide a transport override."
            )

        # Dispatch over the wire
        from .transports import send_message

        logger.info(
            "Sending %s to %s via %s",
            intent.value,
            to_agent_id[:40],
            config.transport.value,
        )
        response = await send_message(config, msg, self._signing_secret)
        return response

    def connect(
        self,
        agent_id: str,
        transport: TransportType = TransportType.HTTP,
    ) -> ConnectionConfig:
        """Build a connection config for the given agent.

        Looks up the agent's registered endpoints and returns a
        ``ConnectionConfig`` with the appropriate URL and auth details.

        Args:
            agent_id: DID of the agent to connect to.
            transport: Preferred transport type.

        Returns:
            A ``ConnectionConfig`` for establishing a connection.
        """
        entry = self._directory.lookup(agent_id)
        url = ""
        if entry:
            endpoints = entry.agent_card.endpoints
            url = endpoints.get(transport.value, endpoints.get("http", ""))

        return ConnectionConfig(
            transport=transport,
            url=url,
            auth_method="hmac",
            secret=self._signing_secret,
        )

    @asynccontextmanager
    async def stream_events(
        self,
        agent_id: str,
        callback: Callable[..., Any],
        transport: Optional[TransportType] = None,
        filter_types: Optional[List[str]] = None,
        session_id: str = "",
    ) -> AsyncIterator[None]:
        """Open a streaming connection to a remote agent.

        Uses WebSocket (preferred) or SSE (HTTP fallback) to receive
        real-time ``StreamEvent`` objects from the target agent.

        Args:
            agent_id: DID of the agent to stream from.
            callback: Called with each ``StreamEvent`` or dict.
            transport: Override transport (default: auto-select).
            filter_types: Event types to subscribe to (empty = all).
            session_id: Filter to a specific session.

        Yields:
            None — events arrive via the callback while inside the block.
        """
        selected = transport or self._best_transport(agent_id)
        config = self.connect(agent_id, selected)

        if selected == TransportType.WEBSOCKET:
            from .transports.websocket import WebSocketConnection

            conn = WebSocketConnection(config)
            await conn.connect()
            try:
                # Start a background task to receive and dispatch events
                async def _ws_listener():
                    try:
                        async for data in conn.events():
                            callback(data)
                    except Exception:
                        pass

                import asyncio

                task = asyncio.create_task(_ws_listener())
                yield
            finally:
                task.cancel()
                await conn.close()
        elif selected == TransportType.HTTP:
            from .transports.http import http_stream_events

            import asyncio

            async def _sse_listener():
                try:
                    async for event in http_stream_events(config, session_id):
                        callback(event)
                except Exception:
                    pass

            task = asyncio.create_task(_sse_listener())
            try:
                yield
            finally:
                task.cancel()
        else:
            yield

    @contextmanager
    def stream_events_sync(self, callback: Callable[..., Any]):
        """Synchronous placeholder for backward compatibility.

        Deprecated: Use ``stream_events`` (async) instead.
        """
        yield

    # -- internal -------------------------------------------------------------

    def _best_transport(self, agent_id: str) -> TransportType:
        """Select the best transport for a given agent.

        Priority: WebSocket > HTTP > stdio.
        Falls back to HTTP if no endpoints are registered.
        """
        entry = self._directory.lookup(agent_id)
        if not entry:
            return TransportType.HTTP

        endpoints = entry.agent_card.endpoints
        if "websocket" in endpoints:
            return TransportType.WEBSOCKET
        if "http" in endpoints:
            return TransportType.HTTP
        if "stdio" in endpoints:
            return TransportType.STDIO
        return TransportType.HTTP

    def _sign_message(self, msg: ROARMessage) -> ROARMessage:
        """Sign a message with HMAC-SHA256 using the client's secret.

        Args:
            msg: The message to sign.

        Returns:
            The same message instance, now with ``auth`` populated.
        """
        body = json.dumps(
            {"id": msg.id, "intent": msg.intent, "payload": msg.payload},
            sort_keys=True,
        )
        sig = hmac.new(
            self._signing_secret.encode(), body.encode(), hashlib.sha256
        ).hexdigest()
        msg.auth = {
            "signature": f"hmac-sha256:{sig}",
            "signer": self._identity.did,
            "timestamp": time.time(),
        }
        return msg
