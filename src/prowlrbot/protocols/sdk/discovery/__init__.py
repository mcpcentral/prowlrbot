# -*- coding: utf-8 -*-
"""ROAR Protocol SDK — Discovery Layer (Layer 2).

Provides multi-tier agent discovery:
  - Tier 0: Local in-memory cache (always available, fastest)
  - Tier 1: Hub HTTP API (federated, cross-network)
  - Tier 2: DNS/SVCB resolution (internet-scale, standards-based)
  - Tier 3: mDNS/DNS-SD (LAN, zero-config)

Ref: IETF BANDAID draft for DNS-based agent discovery.
"""
from .cache import DiscoveryCache
from .hub import HubClient

__all__ = [
    "DiscoveryCache",
    "HubClient",
]
