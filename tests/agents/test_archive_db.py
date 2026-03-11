# -*- coding: utf-8 -*-
"""Tests for long-term agent memory archive."""
import pytest

from prowlrbot.agents.memory.archive_db import ArchiveDB


@pytest.fixture
def db(tmp_path):
    archive = ArchiveDB(str(tmp_path / "archive.db"))
    yield archive
    archive.close()


class TestStoreAndRetrieve:
    def test_store_returns_id(self, db):
        entry_id = db.store("agent-1", "Python tips", "Use type hints for clarity")
        assert entry_id.startswith("arch_")

    def test_search_finds_stored_entry(self, db):
        db.store("agent-1", "Python best practices", "Use type hints for clarity", importance=3)
        results = db.search("agent-1", "type hints")
        assert len(results) >= 1
        assert "type hints" in results[0]["summary"].lower()

    def test_get_by_id(self, db):
        entry_id = db.store("agent-1", "Topic A", "Summary A")
        entry = db.get(entry_id)
        assert entry is not None
        assert entry["topic"] == "Topic A"
        assert entry["summary"] == "Summary A"

    def test_get_missing_returns_none(self, db):
        assert db.get("nonexistent") is None


class TestAgentIsolation:
    def test_agents_cannot_see_each_others_entries(self, db):
        db.store("agent-1", "Secret A", "value a")
        db.store("agent-2", "Secret B", "value b")
        results_a = db.search("agent-1", "Secret")
        results_b = db.search("agent-2", "Secret")
        assert all(r["agent_id"] == "agent-1" for r in results_a)
        assert all(r["agent_id"] == "agent-2" for r in results_b)

    def test_list_by_agent(self, db):
        db.store("agent-1", "A1", "data1")
        db.store("agent-1", "A2", "data2")
        db.store("agent-2", "B1", "other")
        entries = db.list_by_agent("agent-1")
        assert len(entries) == 2
        assert all(e["agent_id"] == "agent-1" for e in entries)


class TestPromotionTracking:
    def test_promoted_from_is_recorded(self, db):
        db.store("agent-1", "Promoted knowledge", "important info", promoted_from="learning-123")
        results = db.search("agent-1", "Promoted")
        assert results[0]["promoted_from"] == "learning-123"

    def test_default_promoted_from_is_empty(self, db):
        db.store("agent-1", "Regular entry", "just data")
        results = db.search("agent-1", "Regular")
        assert results[0]["promoted_from"] == ""


class TestAccessTracking:
    def test_access_count_increments(self, db):
        db.store("agent-1", "Accessed item", "data")
        results = db.search("agent-1", "Accessed")
        entry_id = results[0]["id"]
        db.record_access(entry_id)
        db.record_access(entry_id)
        entry = db.get(entry_id)
        assert entry["access_count"] == 2

    def test_last_accessed_updates(self, db):
        entry_id = db.store("agent-1", "Timestamp test", "check time")
        before = db.get(entry_id)["last_accessed"]
        db.record_access(entry_id)
        after = db.get(entry_id)["last_accessed"]
        assert after >= before


class TestMaintenance:
    def test_delete_entry(self, db):
        entry_id = db.store("agent-1", "To delete", "bye")
        assert db.delete(entry_id) is True
        assert db.get(entry_id) is None

    def test_delete_nonexistent_returns_false(self, db):
        assert db.delete("nope") is False

    def test_count(self, db):
        assert db.count() == 0
        db.store("agent-1", "One", "1")
        db.store("agent-1", "Two", "2")
        db.store("agent-2", "Three", "3")
        assert db.count() == 3
        assert db.count("agent-1") == 2
        assert db.count("agent-2") == 1

    def test_search_with_empty_query(self, db):
        db.store("agent-1", "Something", "stuff")
        assert db.search("agent-1", "") == []
        assert db.search("agent-1", "   ") == []
