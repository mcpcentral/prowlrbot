# -*- coding: utf-8 -*-
"""ROAR Protocol SDK — Identity Layer (Layer 1).

Provides DID method support, DID Document generation, and capability delegation.

DID Method Tiers:
  - did:roar — Ephemeral, auto-generated (default for local agents)
  - did:key  — Ephemeral, cryptographic (for cross-org trust without registry)
  - did:web  — Persistent, DNS-bound (for production agents with stable identity)
"""
from .did_document import DIDDocument
from .did_key import DIDKeyMethod
from .did_web import DIDWebMethod
from .delegation import CapabilityDelegation, DelegationToken, AutonomyLevel

__all__ = [
    "DIDDocument",
    "DIDKeyMethod",
    "DIDWebMethod",
    "CapabilityDelegation",
    "DelegationToken",
    "AutonomyLevel",
]
