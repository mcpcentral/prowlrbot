# -*- coding: utf-8 -*-
"""Tests for ROAR Protocol Phase 5 — Discovery Enhancement."""
from __future__ import annotations

import time
import unittest

from src.prowlrbot.protocols.roar import AgentCard, AgentIdentity, DiscoveryEntry
from src.prowlrbot.protocols.sdk.discovery.cache import DiscoveryCache


def _make_entry(name: str, skills: list = None) -> DiscoveryEntry:
    identity = AgentIdentity(display_name=name)
    card = AgentCard(
        identity=identity,
        description=f"{name} agent",
        skills=skills or [],
        endpoints={"http": f"http://localhost:8089/{name}"},
    )
    return DiscoveryEntry(agent_card=card)


class TestDiscoveryCache(unittest.TestCase):
    """Tests for TTL + LRU discovery cache."""

    def test_put_and_get(self):
        cache = DiscoveryCache()
        entry = _make_entry("planner")
        cache.put(entry)
        found = cache.get(entry.agent_card.identity.did)
        assert found is not None
        assert found.agent_card.identity.display_name == "planner"

    def test_cache_miss(self):
        cache = DiscoveryCache()
        assert cache.get("did:roar:agent:nonexistent-12345678") is None

    def test_ttl_expiration(self):
        cache = DiscoveryCache(default_ttl=0.05)
        entry = _make_entry("expiring")
        cache.put(entry)
        assert cache.get(entry.agent_card.identity.did) is not None
        time.sleep(0.1)
        assert cache.get(entry.agent_card.identity.did) is None

    def test_lru_eviction(self):
        cache = DiscoveryCache(max_entries=2)
        e1 = _make_entry("agent-1")
        e2 = _make_entry("agent-2")
        e3 = _make_entry("agent-3")

        cache.put(e1)
        cache.put(e2)
        cache.put(e3)  # Evicts e1

        assert cache.get(e1.agent_card.identity.did) is None
        assert cache.get(e2.agent_card.identity.did) is not None
        assert cache.get(e3.agent_card.identity.did) is not None

    def test_invalidate(self):
        cache = DiscoveryCache()
        entry = _make_entry("removable")
        cache.put(entry)
        did = entry.agent_card.identity.did
        assert cache.invalidate(did)
        assert cache.get(did) is None

    def test_search_by_capability(self):
        cache = DiscoveryCache()
        cache.put(_make_entry("reviewer", skills=["code-review", "testing"]))
        cache.put(_make_entry("deployer", skills=["deploy", "monitoring"]))

        results = cache.search("code-review")
        assert len(results) == 1
        assert results[0].agent_card.identity.display_name == "reviewer"

    def test_stats(self):
        cache = DiscoveryCache()
        entry = _make_entry("stats-test")
        cache.put(entry)

        cache.get(entry.agent_card.identity.did)  # Hit
        cache.get("did:roar:agent:miss-12345678")  # Miss

        stats = cache.stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["hit_rate"] == 0.5

    def test_clear(self):
        cache = DiscoveryCache()
        cache.put(_make_entry("a"))
        cache.put(_make_entry("b"))
        assert cache.size == 2
        cache.clear()
        assert cache.size == 0

    def test_custom_ttl_per_entry(self):
        cache = DiscoveryCache(default_ttl=300.0)
        entry = _make_entry("short-lived")
        cache.put(entry, ttl=0.05)
        assert cache.get(entry.agent_card.identity.did) is not None
        time.sleep(0.1)
        assert cache.get(entry.agent_card.identity.did) is None


if __name__ == "__main__":
    unittest.main()
