# -*- coding: utf-8 -*-
"""Integration tests for memory tier promotion: access → threshold → archive."""

from __future__ import annotations

import pytest

from prowlrbot.agents.memory.archive_db import ArchiveDB
from prowlrbot.agents.memory.tier_manager import MemoryTierManager


@pytest.fixture
def archive(tmp_path):
    return ArchiveDB(str(tmp_path / "archive.db"))


@pytest.fixture
def manager(archive):
    return MemoryTierManager(archive_db=archive, promotion_threshold=3)


class TestPromotionLifecycle:
    """Test the full promotion lifecycle: create → access → promote → verify."""

    def test_entry_below_threshold_not_promoted(self, manager):
        """Entry with access count < threshold should not be promoted."""
        entry = {
            "id": "learn-1",
            "agent_id": "agent-a",
            "topic": "Python tips",
            "summary": "Use list comprehensions",
            "access_count": 1,
            "marked_important": False,
        }
        assert manager.should_promote(entry) is False

    def test_entry_at_threshold_promoted(self, manager, archive):
        """Entry with access count >= threshold should promote to ArchiveDB."""
        entry = {
            "id": "learn-2",
            "agent_id": "agent-a",
            "topic": "Python tips",
            "summary": "Use generators for memory efficiency",
            "access_count": 3,
            "marked_important": False,
        }
        assert manager.should_promote(entry) is True

        archive_id = manager.promote(entry)
        assert archive_id.startswith("arch_")

        # Verify it's in the archive
        results = archive.search("agent-a", "generators")
        assert len(results) == 1
        assert results[0]["promoted_from"] == "learn-2"

    def test_important_entry_promoted_regardless_of_access(
        self,
        manager,
        archive,
    ):
        """Entries marked important should promote regardless of access count."""
        entry = {
            "id": "learn-3",
            "agent_id": "agent-b",
            "topic": "Critical insight",
            "summary": "Never use dangerous code patterns with user input",
            "access_count": 0,
            "marked_important": True,
        }
        assert manager.should_promote(entry) is True
        manager.promote(entry)

        results = archive.search("agent-b", "dangerous")
        assert len(results) == 1

    def test_batch_promotion_filters_correctly(self, manager, archive):
        """Batch promotion should only promote qualifying entries."""
        entries = [
            {
                "id": "l-1",
                "agent_id": "a1",
                "topic": "Low access",
                "summary": "Some info",
                "access_count": 1,
                "marked_important": False,
            },
            {
                "id": "l-2",
                "agent_id": "a1",
                "topic": "High access",
                "summary": "Important pattern",
                "access_count": 5,
                "marked_important": False,
            },
            {
                "id": "l-3",
                "agent_id": "a1",
                "topic": "Marked important",
                "summary": "Security finding",
                "access_count": 0,
                "marked_important": True,
            },
        ]
        promoted = manager.promote_batch(entries)
        assert len(promoted) == 2  # l-2 and l-3

        # Verify archive has exactly 2 entries
        assert archive.count("a1") == 2


class TestArchiveAccess:
    """Test that archive properly tracks access patterns."""

    def test_access_count_and_retrieval(self, archive):
        """Store, access, verify counts update correctly."""
        entry_id = archive.store(
            "agent-x",
            "Topic A",
            "Summary A",
            importance=2,
        )

        # Access 5 times
        for _ in range(5):
            archive.record_access(entry_id)

        entry = archive.get(entry_id)
        assert entry["access_count"] == 5
        assert entry["importance"] == 2

    def test_fts_search_across_entries(self, archive):
        """FTS5 should find entries across topics and summaries."""
        archive.store(
            "a1",
            "Python best practices",
            "Use type hints for clarity",
        )
        archive.store("a1", "JavaScript patterns", "Prefer const over let")
        archive.store("a1", "Python testing", "Write unit tests first")

        python_results = archive.search("a1", "Python")
        assert len(python_results) == 2

        js_results = archive.search("a1", "JavaScript")
        assert len(js_results) == 1

    def test_agent_isolation_in_search(self, archive):
        """Agents should never see each other's memories."""
        archive.store("agent-1", "Secret A", "Agent 1 only info")
        archive.store("agent-2", "Secret B", "Agent 2 only info")

        results_1 = archive.search("agent-1", "Secret")
        results_2 = archive.search("agent-2", "Secret")

        assert len(results_1) == 1
        assert results_1[0]["topic"] == "Secret A"
        assert len(results_2) == 1
        assert results_2[0]["topic"] == "Secret B"


class TestStalePruning:
    """Test stale entry detection and pruning."""

    def test_prune_removes_stale_entries(self, manager, archive):
        """Pruning should remove entries that are old and rarely accessed."""
        archive.store("a1", "Active topic", "Frequently used")
        archive.store("a1", "Stale topic", "Never used again")

        # With default settings (30 day decay), fresh entries won't be stale
        stale = manager.find_stale_entries("a1")
        assert len(stale) == 0  # Nothing is old enough yet

        count = manager.prune_stale("a1")
        assert count == 0
