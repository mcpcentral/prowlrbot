# -*- coding: utf-8 -*-
"""Idempotency guard — deduplicates events by key.

Uses a bounded LRU-style set of seen keys to ensure at-least-once
delivery doesn't result in duplicate processing. Keys expire after
a configurable TTL.

The guard is lightweight (in-memory) and suitable for single-process
deployments. For distributed dedup, use Redis or NATS dedup.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Optional


class IdempotencyGuard:
    """Deduplicates events using idempotency keys.

    Each event should carry a unique key (typically the event ID or
    a hash of its content). The guard tracks seen keys and rejects
    duplicates within the TTL window.

    Attributes:
        max_keys: Maximum number of keys to track (LRU eviction).
        ttl_seconds: How long to remember a key before allowing reuse.
    """

    def __init__(
        self,
        max_keys: int = 10000,
        ttl_seconds: float = 300.0,
    ) -> None:
        self._max_keys = max_keys
        self._ttl = ttl_seconds
        self._seen: OrderedDict[str, float] = OrderedDict()

    def is_duplicate(self, key: str) -> bool:
        """Check if this key has been seen recently.

        Args:
            key: Idempotency key (e.g., event ID).

        Returns:
            True if the key was seen within the TTL window.
        """
        self._evict_expired()
        now = time.time()

        if key in self._seen:
            ts = self._seen[key]
            if now - ts < self._ttl:
                return True
            # Expired — allow reprocessing
            del self._seen[key]

        # Record this key
        self._seen[key] = now

        # LRU eviction if over capacity
        while len(self._seen) > self._max_keys:
            self._seen.popitem(last=False)

        return False

    def mark_seen(self, key: str) -> None:
        """Explicitly mark a key as seen."""
        self._seen[key] = time.time()
        while len(self._seen) > self._max_keys:
            self._seen.popitem(last=False)

    @property
    def size(self) -> int:
        """Number of tracked keys."""
        return len(self._seen)

    def clear(self) -> None:
        """Clear all tracked keys."""
        self._seen.clear()

    def _evict_expired(self) -> None:
        """Remove keys older than TTL from the front of the OrderedDict."""
        if not self._seen:
            return
        cutoff = time.time() - self._ttl
        # OrderedDict is ordered by insertion; evict from front
        while self._seen:
            key, ts = next(iter(self._seen.items()))
            if ts > cutoff:
                break
            del self._seen[key]
