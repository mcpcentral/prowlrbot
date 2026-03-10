# -*- coding: utf-8 -*-
"""Capability delegation and graduated autonomy.

Implements the graduated autonomy model where agents operate at
different trust levels, and capabilities can be delegated from
one agent to another with constraints.

Autonomy Levels (from design doc):
  - WATCH    — Agent can observe but not act.
  - GUIDE    — Agent can suggest actions for human approval.
  - DELEGATE — Agent can act on specific delegated capabilities.
  - AUTONOMOUS — Agent can act freely within its declared capabilities.

Delegation tokens encode who granted what capability to whom,
with optional time limits and scope constraints.

Ref: ROAR Design Doc §4 Identity Enhancement
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AutonomyLevel(str, Enum):
    """Graduated autonomy levels for agents."""

    WATCH = "watch"
    GUIDE = "guide"
    DELEGATE = "delegate"
    AUTONOMOUS = "autonomous"

    def can_act(self) -> bool:
        """Return True if this level allows the agent to take actions."""
        return self in (AutonomyLevel.DELEGATE, AutonomyLevel.AUTONOMOUS)

    def requires_approval(self) -> bool:
        """Return True if actions at this level need human approval."""
        return self in (AutonomyLevel.WATCH, AutonomyLevel.GUIDE)


@dataclass
class DelegationToken:
    """A token granting capabilities from one agent to another.

    Attributes:
        id: Unique token ID.
        grantor: DID of the agent granting the capability.
        grantee: DID of the agent receiving the capability.
        capabilities: List of capability names being delegated.
        autonomy_level: Maximum autonomy level for this delegation.
        constraints: Additional constraints (e.g., rate limits, scope).
        issued_at: When the token was created.
        expires_at: When the token expires (0 = no expiry).
        revoked: Whether the token has been revoked.
    """

    id: str = ""
    grantor: str = ""
    grantee: str = ""
    capabilities: List[str] = field(default_factory=list)
    autonomy_level: AutonomyLevel = AutonomyLevel.GUIDE
    constraints: Dict[str, Any] = field(default_factory=dict)
    issued_at: float = 0.0
    expires_at: float = 0.0
    revoked: bool = False

    def __post_init__(self):
        if not self.id:
            self.id = f"dt-{uuid.uuid4().hex[:16]}"
        if not self.issued_at:
            self.issued_at = time.time()

    @property
    def expired(self) -> bool:
        """Check if this token has expired."""
        if self.expires_at <= 0:
            return False
        return time.time() > self.expires_at

    @property
    def valid(self) -> bool:
        """Check if this token is currently valid."""
        return not self.revoked and not self.expired

    def allows(self, capability: str) -> bool:
        """Check if this token grants a specific capability."""
        if not self.valid:
            return False
        return capability in self.capabilities or "*" in self.capabilities


class CapabilityDelegation:
    """Manages delegation tokens between agents.

    Usage::

        delegation = CapabilityDelegation()

        # Grant capabilities
        token = delegation.grant(
            grantor="did:roar:human:admin-12345678",
            grantee="did:roar:agent:planner-abcdef00",
            capabilities=["code-review", "testing"],
            autonomy_level=AutonomyLevel.DELEGATE,
            ttl_seconds=3600,
        )

        # Check authorization
        if delegation.is_authorized(
            agent_did="did:roar:agent:planner-abcdef00",
            capability="code-review",
        ):
            # Agent can proceed
            ...

        # Revoke
        delegation.revoke(token.id)
    """

    def __init__(self) -> None:
        self._tokens: Dict[str, DelegationToken] = {}
        self._by_grantee: Dict[str, List[str]] = {}  # grantee DID → token IDs

    def grant(
        self,
        grantor: str,
        grantee: str,
        capabilities: List[str],
        autonomy_level: AutonomyLevel = AutonomyLevel.GUIDE,
        constraints: Optional[Dict[str, Any]] = None,
        ttl_seconds: float = 0,
    ) -> DelegationToken:
        """Grant capabilities from grantor to grantee.

        Args:
            grantor: DID of the granting agent/human.
            grantee: DID of the receiving agent.
            capabilities: List of capability names to delegate.
            autonomy_level: Maximum autonomy for these capabilities.
            constraints: Additional scope constraints.
            ttl_seconds: Time-to-live (0 = no expiry).

        Returns:
            The created DelegationToken.
        """
        token = DelegationToken(
            grantor=grantor,
            grantee=grantee,
            capabilities=capabilities,
            autonomy_level=autonomy_level,
            constraints=constraints or {},
            expires_at=time.time() + ttl_seconds if ttl_seconds > 0 else 0,
        )
        self._tokens[token.id] = token
        self._by_grantee.setdefault(grantee, []).append(token.id)
        return token

    def revoke(self, token_id: str) -> bool:
        """Revoke a delegation token.

        Args:
            token_id: The token to revoke.

        Returns:
            True if the token was found and revoked.
        """
        token = self._tokens.get(token_id)
        if token:
            token.revoked = True
            return True
        return False

    def is_authorized(
        self,
        agent_did: str,
        capability: str,
        min_autonomy: AutonomyLevel = AutonomyLevel.DELEGATE,
    ) -> bool:
        """Check if an agent is authorized for a capability.

        Args:
            agent_did: The agent's DID.
            capability: The capability to check.
            min_autonomy: Minimum required autonomy level.

        Returns:
            True if the agent has a valid token for this capability.
        """
        token_ids = self._by_grantee.get(agent_did, [])
        autonomy_order = [
            AutonomyLevel.WATCH,
            AutonomyLevel.GUIDE,
            AutonomyLevel.DELEGATE,
            AutonomyLevel.AUTONOMOUS,
        ]
        min_idx = autonomy_order.index(min_autonomy)

        for tid in token_ids:
            token = self._tokens.get(tid)
            if not token or not token.valid:
                continue
            if not token.allows(capability):
                continue
            token_idx = autonomy_order.index(token.autonomy_level)
            if token_idx >= min_idx:
                return True
        return False

    def get_autonomy_level(self, agent_did: str) -> AutonomyLevel:
        """Get the highest autonomy level granted to an agent.

        Args:
            agent_did: The agent's DID.

        Returns:
            The highest valid autonomy level, or WATCH if none.
        """
        token_ids = self._by_grantee.get(agent_did, [])
        autonomy_order = [
            AutonomyLevel.WATCH,
            AutonomyLevel.GUIDE,
            AutonomyLevel.DELEGATE,
            AutonomyLevel.AUTONOMOUS,
        ]
        highest = AutonomyLevel.WATCH
        highest_idx = 0

        for tid in token_ids:
            token = self._tokens.get(tid)
            if not token or not token.valid:
                continue
            idx = autonomy_order.index(token.autonomy_level)
            if idx > highest_idx:
                highest = token.autonomy_level
                highest_idx = idx

        return highest

    def list_tokens(self, grantee: Optional[str] = None) -> List[DelegationToken]:
        """List delegation tokens, optionally filtered by grantee."""
        if grantee:
            token_ids = self._by_grantee.get(grantee, [])
            return [self._tokens[tid] for tid in token_ids if tid in self._tokens]
        return list(self._tokens.values())

    def cleanup_expired(self) -> int:
        """Remove expired and revoked tokens. Returns count removed."""
        to_remove = [
            tid for tid, token in self._tokens.items()
            if not token.valid
        ]
        for tid in to_remove:
            token = self._tokens.pop(tid)
            grantee_list = self._by_grantee.get(token.grantee, [])
            if tid in grantee_list:
                grantee_list.remove(tid)
        return len(to_remove)
