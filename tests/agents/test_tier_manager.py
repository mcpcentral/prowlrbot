# -*- coding: utf-8 -*-
"""Tests for memory tier promotion and demotion."""
from datetime import datetime, timedelta, timezone

import pytest

from prowlrbot.agents.memory.archive_db import ArchiveDB
from prowlrbot.agents.memory.tier_manager import MemoryTierManager


@pytest.fixture
def archive(tmp_path):
    db = ArchiveDB(str(tmp_path / "archive.db"))
    yield db
    db.close()


@pytest.fixture
def manager(archive):
    return MemoryTierManager(archive_db=archive)


# ------------------------------------------------------------------
# Promotion decisions
# ------------------------------------------------------------------


class TestShouldPromote:
    def test_high_access_count_promotes(self, manager):
        entry = {
            "id": "l-1",
            "agent_id": "a1",
            "topic": "test",
            "summary": "data",
            "access_count": 5,
            "marked_important": False,
        }
        assert manager.should_promote(entry) is True

    def test_marked_important_promotes(self, manager):
        entry = {
            "id": "l-2",
            "agent_id": "a1",
            "topic": "test",
            "summary": "data",
            "access_count": 1,
            "marked_important": True,
        }
        assert manager.should_promote(entry) is True

    def test_low_access_does_not_promote(self, manager):
        entry = {
            "id": "l-3",
            "agent_id": "a1",
            "topic": "test",
            "summary": "data",
            "access_count": 1,
            "marked_important": False,
        }
        assert manager.should_promote(entry) is False

    def test_exact_threshold_promotes(self, manager):
        entry = {
            "id": "l-4",
            "agent_id": "a1",
            "topic": "test",
            "summary": "data",
            "access_count": 3,
            "marked_important": False,
        }
        assert manager.should_promote(entry) is True

    def test_custom_threshold(self, archive):
        mgr = MemoryTierManager(archive_db=archive, promotion_threshold=10)
        entry = {"access_count": 5, "marked_important": False}
        assert mgr.should_promote(entry) is False
        entry["access_count"] = 10
        assert mgr.should_promote(entry) is True


# ------------------------------------------------------------------
# Promotion execution
# ------------------------------------------------------------------


class TestPromote:
    def test_promote_entry(self, manager, archive):
        entry = {
            "id": "learn-1",
            "agent_id": "a1",
            "topic": "Python tips",
            "summary": "Use generators for memory efficiency",
        }
        archive_id = manager.promote(entry)
        assert archive_id.startswith("arch_")
        results = archive.search("a1", "generators")
        assert len(results) == 1
        assert results[0]["promoted_from"] == "learn-1"

    def test_promote_preserves_importance(self, manager, archive):
        entry = {
            "id": "learn-2",
            "agent_id": "a1",
            "topic": "Critical fact",
            "summary": "Must remember this",
            "importance": 5,
        }
        manager.promote(entry)
        results = archive.search("a1", "Critical")
        assert results[0]["importance"] == 5

    def test_promote_batch(self, manager, archive):
        entries = [
            {
                "id": "b1",
                "agent_id": "a1",
                "topic": "High access",
                "summary": "often used",
                "access_count": 5,
                "marked_important": False,
            },
            {
                "id": "b2",
                "agent_id": "a1",
                "topic": "Low access",
                "summary": "rarely used",
                "access_count": 1,
                "marked_important": False,
            },
            {
                "id": "b3",
                "agent_id": "a1",
                "topic": "Important",
                "summary": "flagged",
                "access_count": 0,
                "marked_important": True,
            },
        ]
        promoted = manager.promote_batch(entries)
        # Only b1 and b3 should be promoted
        assert len(promoted) == 2
        assert archive.count("a1") == 2


# ------------------------------------------------------------------
# Demotion / pruning
# ------------------------------------------------------------------


class TestStalePruning:
    def test_find_stale_entries(self, manager, archive):
        # Insert an entry and manually backdate its last_accessed
        entry_id = archive.store("a1", "Old fact", "stale data")
        old_date = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        archive._conn.execute(
            "UPDATE archive SET last_accessed = ?, access_count = 0 WHERE id = ?",
            (old_date, entry_id),
        )
        archive._conn.commit()

        stale = manager.find_stale_entries("a1")
        assert len(stale) == 1
        assert stale[0]["id"] == entry_id

    def test_active_entries_are_not_stale(self, manager, archive):
        archive.store("a1", "Fresh fact", "just created")
        stale = manager.find_stale_entries("a1")
        assert len(stale) == 0

    def test_frequently_accessed_old_entries_not_stale(self, manager, archive):
        entry_id = archive.store("a1", "Old but loved", "popular")
        old_date = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        archive._conn.execute(
            "UPDATE archive SET last_accessed = ?, access_count = 5 WHERE id = ?",
            (old_date, entry_id),
        )
        archive._conn.commit()

        stale = manager.find_stale_entries("a1")
        assert len(stale) == 0

    def test_prune_stale(self, manager, archive):
        entry_id = archive.store("a1", "Prune me", "gone soon")
        old_date = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        archive._conn.execute(
            "UPDATE archive SET last_accessed = ?, access_count = 0 WHERE id = ?",
            (old_date, entry_id),
        )
        archive._conn.commit()

        pruned = manager.prune_stale("a1")
        assert pruned == 1
        assert archive.get(entry_id) is None

    def test_prune_with_nothing_stale(self, manager, archive):
        archive.store("a1", "Keep me", "still fresh")
        assert manager.prune_stale("a1") == 0
