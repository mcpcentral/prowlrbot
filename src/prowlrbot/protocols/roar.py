# -*- coding: utf-8 -*-
"""ROAR Protocol — Real-time Open Agent Runtime.

Unified protocol for agent identity, discovery, communication, and streaming.
Layers: Identity / Discovery / Connect / Exchange / Stream.
Backward compatible with MCP, A2A, and ACP.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from prowlrbot.compat import StrEnum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Layer 1: ROAR/Identity — W3C DID-based agent identity
# ---------------------------------------------------------------------------


class AgentIdentity(BaseModel):
    """W3C DID-based agent identity."""

    did: str = ""  # e.g. "did:roar:agent:<unique-id>"
    display_name: str = ""
    agent_type: str = "agent"  # agent, tool, human, ide
    capabilities: List[str] = Field(default_factory=list)
    version: str = "1.0"
    public_key: Optional[str] = None  # Ed25519 public key (hex-encoded)

    def model_post_init(self, __context: Any) -> None:
        if not self.did:
            uid = uuid.uuid4().hex[:16]
            slug = self.display_name.lower().replace(" ", "-")[:20] or "agent"
            self.did = f"did:roar:{self.agent_type}:{slug}-{uid}"


class AgentCapability(BaseModel):
    """A declared capability that an agent can perform."""

    name: str
    description: str = ""
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)


class AgentCard(BaseModel):
    """Capability descriptor for discovery (A2A-compatible)."""

    identity: AgentIdentity
    description: str = ""
    skills: List[str] = Field(default_factory=list)
    channels: List[str] = Field(default_factory=list)
    endpoints: Dict[str, str] = Field(default_factory=dict)
    declared_capabilities: List[AgentCapability] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Layer 2: ROAR/Discovery — Decentralized agent discovery
# ---------------------------------------------------------------------------


class DiscoveryEntry(BaseModel):
    """Entry in the agent discovery directory."""

    agent_card: AgentCard
    registered_at: float = Field(default_factory=time.time)
    last_seen: float = Field(default_factory=time.time)
    hub_url: str = ""  # Which hub registered this agent


class AgentDirectory:
    """In-memory agent directory for local discovery."""

    def __init__(self) -> None:
        self._agents: Dict[str, DiscoveryEntry] = {}

    def register(self, card: AgentCard) -> DiscoveryEntry:
        entry = DiscoveryEntry(agent_card=card)
        self._agents[card.identity.did] = entry
        return entry

    def unregister(self, did: str) -> bool:
        return self._agents.pop(did, None) is not None

    def lookup(self, did: str) -> Optional[DiscoveryEntry]:
        return self._agents.get(did)

    def search(self, capability: str) -> List[DiscoveryEntry]:
        """Find agents with a specific capability."""
        return [
            entry
            for entry in self._agents.values()
            if capability in entry.agent_card.identity.capabilities
        ]

    def list_all(self) -> List[DiscoveryEntry]:
        return list(self._agents.values())


# ---------------------------------------------------------------------------
# Layer 3: ROAR/Connect — Unified transport
# ---------------------------------------------------------------------------


class TransportType(StrEnum):
    STDIO = "stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"
    GRPC = "grpc"


class ConnectionConfig(BaseModel):
    """Configuration for connecting to a ROAR endpoint."""

    transport: TransportType = TransportType.HTTP
    url: str = ""
    auth_method: str = "hmac"  # hmac, jwt, mtls, none
    secret: str = ""
    timeout_ms: int = 30000


# ---------------------------------------------------------------------------
# Layer 4: ROAR/Exchange — Unified message format
# ---------------------------------------------------------------------------


class MessageIntent(StrEnum):
    """What the sender wants the receiver to do."""

    EXECUTE = "execute"  # Agent → Tool
    DELEGATE = "delegate"  # Agent → Agent
    UPDATE = "update"  # Agent → IDE
    ASK = "ask"  # Agent → Human
    RESPOND = "respond"  # Response to any of the above
    NOTIFY = "notify"  # One-way notification
    DISCOVER = "discover"  # Discovery request


class ROARMessage(BaseModel):
    """Unified ROAR message — one format for everything."""

    roar: str = "1.0"
    id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:10]}")
    from_identity: AgentIdentity = Field(alias="from")
    to_identity: AgentIdentity = Field(alias="to")
    intent: MessageIntent
    payload: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    auth: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)

    model_config = {"populate_by_name": True}

    def _signing_body(self) -> str:
        """Build the canonical JSON body for HMAC signing.

        Covers ALL security-relevant fields: id, from, to, intent,
        payload, context, and the auth timestamp (set before signing).
        """
        return json.dumps(
            {
                "id": self.id,
                "from": self.from_identity.did,
                "to": self.to_identity.did,
                "intent": self.intent,
                "payload": self.payload,
                "context": self.context,
                "timestamp": self.auth.get("timestamp", self.timestamp),
            },
            sort_keys=True,
        )

    def sign(self, secret: str) -> "ROARMessage":
        """Add HMAC-SHA256 signature covering all message fields."""
        now = time.time()
        self.auth = {"timestamp": now}
        body = self._signing_body()
        sig = hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        self.auth["signature"] = f"hmac-sha256:{sig}"
        return self

    def verify(self, secret: str, max_age_seconds: float = 300.0) -> bool:
        """Verify HMAC signature with replay protection.

        Args:
            secret: The shared signing secret.
            max_age_seconds: Maximum age of the message in seconds (default 5 min).
                Set to 0 to disable timestamp checking.

        Returns:
            True if signature is valid and message is within the time window.
        """
        sig_value = self.auth.get("signature", "")
        if not sig_value.startswith("hmac-sha256:"):
            return False

        # Check timestamp freshness (replay protection)
        if max_age_seconds > 0:
            msg_time = self.auth.get("timestamp", 0)
            age = abs(time.time() - msg_time)
            if age > max_age_seconds:
                return False

        expected_sig = sig_value.split(":", 1)[1]
        body = self._signing_body()
        actual_sig = hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected_sig, actual_sig)


# ---------------------------------------------------------------------------
# Layer 5: ROAR/Stream — Real-time event streaming
# ---------------------------------------------------------------------------


class StreamEventType(StrEnum):
    TOOL_CALL = "tool_call"
    MCP_REQUEST = "mcp_request"
    REASONING = "reasoning"
    TASK_UPDATE = "task_update"
    MONITOR_ALERT = "monitor_alert"
    AGENT_STATUS = "agent_status"
    CHECKPOINT = "checkpoint"
    WORLD_UPDATE = "world_update"  # AgentVerse


class StreamEvent(BaseModel):
    """A real-time streaming event."""

    type: StreamEventType
    source: str = ""  # DID of event source
    session_id: str = ""
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


# ---------------------------------------------------------------------------
# Protocol Adapters (backward compatibility)
# ---------------------------------------------------------------------------


class MCPAdapter:
    """Translate between MCP tool calls and ROAR messages."""

    @staticmethod
    def mcp_to_roar(
        tool_name: str,
        params: Dict[str, Any],
        from_agent: AgentIdentity,
    ) -> ROARMessage:
        tool_identity = AgentIdentity(
            display_name=tool_name,
            agent_type="tool",
        )
        return ROARMessage(
            **{
                "from": from_agent,
                "to": tool_identity,
            },
            intent=MessageIntent.EXECUTE,
            payload={"action": tool_name, "params": params},
        )

    @staticmethod
    def roar_to_mcp(msg: ROARMessage) -> Dict[str, Any]:
        return {
            "tool": msg.payload.get("action", ""),
            "params": msg.payload.get("params", {}),
        }


class A2AAdapter:
    """Translate between A2A agent tasks and ROAR messages."""

    @staticmethod
    def a2a_task_to_roar(
        task: Dict[str, Any],
        from_agent: AgentIdentity,
        to_agent: AgentIdentity,
    ) -> ROARMessage:
        return ROARMessage(
            **{
                "from": from_agent,
                "to": to_agent,
            },
            intent=MessageIntent.DELEGATE,
            payload=task,
            context={"protocol": "a2a"},
        )

    @staticmethod
    def roar_to_a2a(msg: ROARMessage) -> Dict[str, Any]:
        return {
            "task_id": msg.id,
            "from": msg.from_identity.did,
            "to": msg.to_identity.did,
            "payload": msg.payload,
        }
