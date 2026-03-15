# -*- coding: utf-8 -*-
"""Test that MemoryManager promotes compacted memories via MemoryTierManager."""

import pytest
from unittest.mock import MagicMock, patch
from prowlrbot.agents.memory.tier_manager import MemoryTierManager
from prowlrbot.agents.memory.archive_db import ArchiveDB


def test_tier_manager_should_promote_high_access():
    """should_promote returns True when access_count >= threshold."""
    archive = MagicMock(spec=ArchiveDB)
    mgr = MemoryTierManager(archive_db=archive)
    entry = {
        "id": "x",
        "agent_id": "a1",
        "topic": "t",
        "summary": "s",
        "access_count": 3,
        "marked_important": False,
    }
    assert mgr.should_promote(entry) is True


def test_tier_manager_should_not_promote_low_access():
    """should_promote returns False when access_count < threshold."""
    archive = MagicMock(spec=ArchiveDB)
    mgr = MemoryTierManager(archive_db=archive)
    entry = {
        "id": "x",
        "agent_id": "a1",
        "topic": "t",
        "summary": "s",
        "access_count": 1,
        "marked_important": False,
    }
    assert mgr.should_promote(entry) is False


def test_tier_manager_promote_calls_archive_store(tmp_path):
    """promote() stores entry in ArchiveDB."""
    db = ArchiveDB(str(tmp_path / "archive.db"))
    mgr = MemoryTierManager(archive_db=db)
    entry = {
        "id": "learn-1",
        "agent_id": "bot-1",
        "topic": "Python tips",
        "summary": "Use generators for memory efficiency",
    }
    mgr.promote(entry)
    results = db.search("bot-1", "generators")
    assert len(results) == 1


def test_archive_db_fts_search(tmp_path):
    """ArchiveDB stores and retrieves via FTS5."""
    db = ArchiveDB(str(tmp_path / "archive.db"))
    db.store(
        "agent-1",
        "Python best practices",
        "Use type hints for clarity",
        importance=3,
    )
    results = db.search("agent-1", "type hints")
    assert len(results) >= 1
