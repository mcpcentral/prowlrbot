# -*- coding: utf-8 -*-
"""Tests for scheduled monitor execution via APScheduler."""

from __future__ import annotations

import pytest

from prowlrbot.monitor.engine import MonitorEngine
from prowlrbot.monitor.storage import MonitorStorage


@pytest.fixture
def storage(tmp_path):
    s = MonitorStorage(db_path=tmp_path / "monitors.db")
    yield s
    s.close()


@pytest.fixture
async def engine(storage):
    eng = MonitorEngine(storage=storage)
    yield eng
    # Shutdown scheduler if started — must happen while the event loop is
    # still running, hence this fixture is async.
    if eng._scheduler is not None:
        eng._scheduler.shutdown(wait=False)


class TestScheduleMonitor:
    @pytest.mark.asyncio
    async def test_schedule_returns_job_id(self, engine):
        job_id = engine.schedule_monitor(
            "https://example.com", interval_minutes=60
        )
        assert job_id is not None
        assert isinstance(job_id, str)

    @pytest.mark.asyncio
    async def test_scheduled_monitor_count_increments(self, engine):
        assert engine.get_scheduled_monitors() == 0
        engine.schedule_monitor("https://example.com", interval_minutes=60)
        assert engine.get_scheduled_monitors() == 1
        engine.schedule_monitor("https://other.com", interval_minutes=30)
        assert engine.get_scheduled_monitors() == 2

    @pytest.mark.asyncio
    async def test_schedule_registers_config(self, engine):
        engine.schedule_monitor(
            "https://example.com",
            interval_minutes=60,
            name="test-web",
        )
        configs = engine.list()
        assert len(configs) == 1
        assert configs[0].name == "test-web"
        assert configs[0].url == "https://example.com"

    @pytest.mark.asyncio
    async def test_schedule_api_monitor(self, engine):
        job_id = engine.schedule_monitor(
            "https://api.example.com/health",
            interval_minutes=15,
            monitor_type="api",
            name="test-api",
        )
        assert job_id is not None
        configs = engine.list()
        assert len(configs) == 1
        assert configs[0].type == "api"

    @pytest.mark.asyncio
    async def test_schedule_auto_generates_name(self, engine):
        engine.schedule_monitor(
            "https://example.com", interval_minutes=60
        )
        configs = engine.list()
        assert len(configs) == 1
        assert configs[0].name.startswith("mon_")

    @pytest.mark.asyncio
    async def test_unschedule_removes_job(self, engine):
        job_id = engine.schedule_monitor(
            "https://example.com", interval_minutes=60
        )
        assert engine.get_scheduled_monitors() == 1
        removed = engine.unschedule_monitor(job_id)
        assert removed is True
        assert engine.get_scheduled_monitors() == 0
        assert engine.list() == []

    @pytest.mark.asyncio
    async def test_unschedule_nonexistent_returns_false(self, engine):
        # Need scheduler to exist first
        engine.schedule_monitor("https://example.com", interval_minutes=60)
        removed = engine.unschedule_monitor("nonexistent-job-id")
        assert removed is False

    def test_unschedule_without_scheduler_returns_false(self, engine):
        removed = engine.unschedule_monitor("some-id")
        assert removed is False


class TestStoragePathInit:
    @pytest.mark.asyncio
    async def test_engine_with_storage_path(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        engine = MonitorEngine(storage_path=db_path)
        assert engine.storage is not None
        job_id = engine.schedule_monitor(
            "https://example.com", interval_minutes=60
        )
        assert engine.get_scheduled_monitors() == 1
        engine._scheduler.shutdown(wait=False)
