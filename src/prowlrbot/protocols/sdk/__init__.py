# -*- coding: utf-8 -*-
"""ROAR Protocol SDK — Unified agent communication protocol.

Provides client/server primitives and multi-transport support for
ROAR agent-to-agent messaging (HTTP, WebSocket, stdio).

Usage::

    from prowlrbot.protocols.sdk import ROARClient, ROARServer, create_roar_router
"""
from ..roar import (
    AgentIdentity,
    AgentCard,
    AgentCapability,
    AgentDirectory,
    DiscoveryEntry,
    TransportType,
    ConnectionConfig,
    ROARMessage,
    MessageIntent,
    StreamEvent,
    StreamEventType,
    MCPAdapter,
    A2AAdapter,
)
from .client import ROARClient
from .server import ROARServer
from .router import create_roar_router
from .streaming import EventBus, StreamFilter, Subscription, AIMDController, IdempotencyGuard
from .crypto import KeyPair, Ed25519Signer, NACL_AVAILABLE
from .identity import (
    DIDDocument, DIDKeyMethod, DIDWebMethod,
    CapabilityDelegation, DelegationToken, AutonomyLevel,
)

__all__ = [
    # Core types
    "AgentIdentity",
    "AgentCard",
    "AgentCapability",
    "AgentDirectory",
    "DiscoveryEntry",
    "TransportType",
    "ConnectionConfig",
    "ROARMessage",
    "MessageIntent",
    "StreamEvent",
    "StreamEventType",
    # Protocol adapters
    "MCPAdapter",
    "A2AAdapter",
    # SDK classes
    "ROARClient",
    "ROARServer",
    "create_roar_router",
    # Streaming
    "EventBus",
    "StreamFilter",
    "Subscription",
    "AIMDController",
    "IdempotencyGuard",
    # Crypto
    "KeyPair",
    "Ed25519Signer",
    "NACL_AVAILABLE",
    # Identity
    "DIDDocument",
    "DIDKeyMethod",
    "DIDWebMethod",
    "CapabilityDelegation",
    "DelegationToken",
    "AutonomyLevel",
]
