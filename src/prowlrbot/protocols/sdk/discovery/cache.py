# -*- coding: utf-8 -*-
"""TTL-based discovery cache with LRU eviction.

Wraps the base AgentDirectory with a time-to-live cache layer.
Entries are automatically evicted after TTL expiration and when
the cache exceeds its capacity.
"""
from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, List, Optional

from ...roar import AgentCard, DiscoveryEntry


@dataclass
class CacheEntry:
    """A cached discovery entry with timestamp."""

    entry: DiscoveryEntry
    cached_at: float
    ttl: float

    @property
    def expired(self) -> bool:
        return time.time() - self.cached_at > self.ttl


class DiscoveryCache:
    """TTL + LRU discovery cache.

    Provides fast lookups for recently discovered agents. Falls through
    to the upstream resolver (hub or DNS) on cache miss.

    Usage::

        cache = DiscoveryCache(max_entries=500, default_ttl=300.0)
        cache.put(entry)
        found = cache.get("did:roar:agent:planner-abc12345")
    """

    def __init__(
        self,
        max_entries: int = 1000,
        default_ttl: float = 300.0,
    ) -> None:
        self._max_entries = max_entries
        self._default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._hits: int = 0
        self._misses: int = 0

    def get(self, did: str) -> Optional[DiscoveryEntry]:
        """Look up a cached entry by DID.

        Returns None on cache miss or expired entry.
        """
        entry = self._cache.get(did)
        if entry is None:
            self._misses += 1
            return None
        if entry.expired:
            del self._cache[did]
            self._misses += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(did)
        self._hits += 1
        return entry.entry

    def put(
        self,
        entry: DiscoveryEntry,
        ttl: Optional[float] = None,
    ) -> None:
        """Cache a discovery entry.

        Args:
            entry: The discovery entry to cache.
            ttl: Override TTL for this entry (seconds).
        """
        did = entry.agent_card.identity.did
        self._cache[did] = CacheEntry(
            entry=entry,
            cached_at=time.time(),
            ttl=ttl or self._default_ttl,
        )
        self._cache.move_to_end(did)
        self._evict()

    def invalidate(self, did: str) -> bool:
        """Remove a specific entry from cache."""
        if did in self._cache:
            del self._cache[did]
            return True
        return False

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def search(self, capability: str) -> List[DiscoveryEntry]:
        """Search cached entries by capability."""
        self._evict_expired()
        results = []
        for ce in self._cache.values():
            card = ce.entry.agent_card
            if capability in card.skills or capability in card.description:
                results.append(ce.entry)
        return results

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def stats(self) -> Dict:
        total = self._hits + self._misses
        return {
            "size": self.size,
            "max_entries": self._max_entries,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0.0,
        }

    def _evict(self) -> None:
        """Evict oldest entries if over capacity."""
        while len(self._cache) > self._max_entries:
            self._cache.popitem(last=False)

    def _evict_expired(self) -> None:
        """Remove expired entries."""
        expired = [
            did for did, ce in self._cache.items() if ce.expired
        ]
        for did in expired:
            del self._cache[did]
