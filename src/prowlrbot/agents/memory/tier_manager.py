# -*- coding: utf-8 -*-
"""Orchestrate memory promotion and demotion between tiers.

The ProwlrBot memory system has three conceptual tiers:

1. **Short-term** -- in-process ``ProwlrBotInMemoryMemory`` (conversation
   window, compacted via ``MemoryManager``).
2. **Medium-term** -- a future "learning" store where frequently-referenced
   facts accumulate within a session or across sessions.
3. **Long-term** -- ``ArchiveDB`` (SQLite + FTS5), permanent knowledge.

``MemoryTierManager`` decides *when* an entry should be promoted from
medium-term to long-term and executes the promotion.  Demotion (pruning
stale long-term entries) is also supported.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from .archive_db import ArchiveDB

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

PROMOTION_THRESHOLD: int = 3
"""Access count at which an entry is auto-promoted to long-term storage."""

DECAY_DAYS: int = 30
"""Days without access before a long-term entry becomes a candidate for
pruning."""


class MemoryTierManager:
    """Manage promotion from medium-term to long-term memory.

    Args:
        archive_db: The long-term ``ArchiveDB`` instance.
        promotion_threshold: Override the default access-count threshold.
        decay_days: Override the default staleness window (days).
    """

    def __init__(
        self,
        archive_db: ArchiveDB,
        promotion_threshold: int = PROMOTION_THRESHOLD,
        decay_days: int = DECAY_DAYS,
    ) -> None:
        self._archive = archive_db
        self._promotion_threshold = promotion_threshold
        self._decay_days = decay_days

    # ------------------------------------------------------------------
    # Promotion logic
    # ------------------------------------------------------------------

    def should_promote(self, entry: Dict[str, Any]) -> bool:
        """Decide whether a medium-term entry should be promoted.

        An entry qualifies if any of the following hold:

        * ``marked_important`` is truthy.
        * ``access_count`` meets or exceeds the promotion threshold.

        Args:
            entry: Dict with at least ``access_count`` and optionally
                ``marked_important``.

        Returns:
            ``True`` when the entry should be promoted.
        """
        if entry.get("marked_important"):
            return True
        return entry.get("access_count", 0) >= self._promotion_threshold

    def promote(self, entry: Dict[str, Any]) -> str:
        """Promote a medium-term entry into the long-term archive.

        Args:
            entry: Must contain ``agent_id``, ``topic``, ``summary``.
                Optionally ``id`` (used as ``promoted_from``),
                ``importance``.

        Returns:
            The new archive entry id.
        """
        archive_id = self._archive.store(
            agent_id=entry["agent_id"],
            topic=entry["topic"],
            summary=entry["summary"],
            importance=entry.get("importance", 1),
            promoted_from=entry.get("id", ""),
        )
        logger.info(
            "Promoted entry %s -> %s for agent %s",
            entry.get("id", "?"),
            archive_id,
            entry["agent_id"],
        )
        return archive_id

    def promote_batch(self, entries: List[Dict[str, Any]]) -> List[str]:
        """Evaluate and promote a batch of entries.

        Only entries that pass :meth:`should_promote` are actually stored.

        Args:
            entries: List of medium-term entry dicts.

        Returns:
            List of newly created archive entry ids (only promoted ones).
        """
        promoted_ids: List[str] = []
        for entry in entries:
            if self.should_promote(entry):
                promoted_ids.append(self.promote(entry))
        return promoted_ids

    # ------------------------------------------------------------------
    # Demotion / pruning
    # ------------------------------------------------------------------

    def find_stale_entries(self, agent_id: str) -> List[Dict]:
        """Find long-term entries that have not been accessed recently.

        An entry is "stale" when its ``last_accessed`` timestamp is older
        than ``decay_days`` and its ``access_count`` is low (< 2).

        Args:
            agent_id: Scope the search to a single agent.

        Returns:
            List of stale entry dicts.
        """
        entries = self._archive.list_by_agent(agent_id, limit=500)
        now = datetime.now(timezone.utc)
        stale: List[Dict] = []
        for entry in entries:
            try:
                last = datetime.fromisoformat(entry["last_accessed"])
            except (ValueError, TypeError):
                continue
            age_days = (now - last).days
            if age_days >= self._decay_days and entry.get("access_count", 0) < 2:
                stale.append(entry)
        return stale

    def prune_stale(self, agent_id: str) -> int:
        """Delete stale long-term entries for an agent.

        Args:
            agent_id: Target agent.

        Returns:
            Number of entries pruned.
        """
        stale = self.find_stale_entries(agent_id)
        pruned = 0
        for entry in stale:
            if self._archive.delete(entry["id"]):
                pruned += 1
                logger.info(
                    "Pruned stale archive entry %s for agent %s",
                    entry["id"],
                    agent_id,
                )
        return pruned
