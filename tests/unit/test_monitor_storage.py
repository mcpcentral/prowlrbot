# -*- coding: utf-8 -*-
"""Tests for prowlrbot.monitor.storage."""
import tempfile
from pathlib import Path

import pytest

from prowlrbot.monitor.storage import MonitorStorage


@pytest.fixture
def storage(tmp_path):
    db = tmp_path / "test_monitors.db"
    s = MonitorStorage(db_path=db)
    yield s
    s.close()


class TestMonitorStorage:
    def test_save_and_load(self, storage):
        storage.save("m1", "content v1")
        snap = storage.load("m1")
        assert snap is not None
        assert snap.monitor_name == "m1"
        assert snap.content == "content v1"
        assert snap.checked_at  # not empty

    def test_load_nonexistent(self, storage):
        assert storage.load("does-not-exist") is None

    def test_save_upsert(self, storage):
        storage.save("m1", "v1")
        storage.save("m1", "v2")
        snap = storage.load("m1")
        assert snap.content == "v2"

    def test_delete(self, storage):
        storage.save("m1", "data")
        assert storage.delete("m1") is True
        assert storage.load("m1") is None

    def test_delete_nonexistent(self, storage):
        assert storage.delete("nope") is False

    def test_list_monitors(self, storage):
        storage.save("b-monitor", "x")
        storage.save("a-monitor", "y")
        names = storage.list_monitors()
        assert names == ["a-monitor", "b-monitor"]

    def test_list_empty(self, storage):
        assert storage.list_monitors() == []
