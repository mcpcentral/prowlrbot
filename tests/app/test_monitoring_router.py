# -*- coding: utf-8 -*-
"""Tests for monitoring API endpoints."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from prowlrbot.app.routers.monitoring import router as monitoring_router
from prowlrbot.app.routers import monitoring as monitoring_mod
from prowlrbot.monitor.engine import MonitorEngine
from prowlrbot.monitor.storage import MonitorStorage


@pytest.fixture
def storage(tmp_path):
    s = MonitorStorage(db_path=tmp_path / "test_monitors.db")
    yield s
    s.close()


@pytest.fixture
def engine(storage):
    return MonitorEngine(storage=storage)


@pytest.fixture
def app(engine, monkeypatch):
    """Minimal FastAPI app with the monitoring router and a test engine."""
    _app = FastAPI()
    _app.include_router(monitoring_router)
    # Inject test engine so endpoints don't use the global singleton
    monkeypatch.setattr(monitoring_mod, "_engine", engine)
    return _app


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestListMonitors:
    @pytest.mark.asyncio
    async def test_empty_list(self, client):
        resp = await client.get("/monitors")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_after_create(self, client):
        await client.post(
            "/monitors",
            json={"url": "https://example.com", "type": "web", "interval_minutes": 60},
        )
        resp = await client.get("/monitors")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["url"] == "https://example.com"
        assert data[0]["interval_minutes"] == 60


class TestCreateMonitor:
    @pytest.mark.asyncio
    async def test_create_web_monitor(self, client):
        resp = await client.post(
            "/monitors",
            json={"url": "https://example.com", "type": "web", "interval_minutes": 30},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["id"].startswith("mon_")
        assert data["type"] == "web"
        assert data["url"] == "https://example.com"
        assert data["interval_minutes"] == 30

    @pytest.mark.asyncio
    async def test_create_api_monitor(self, client):
        resp = await client.post(
            "/monitors",
            json={
                "url": "https://api.example.com/status",
                "type": "api",
                "interval_minutes": 15,
                "method": "POST",
                "expected_status": 201,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "api"

    @pytest.mark.asyncio
    async def test_create_monitor_default_interval(self, client):
        resp = await client.post(
            "/monitors",
            json={"url": "https://example.com"},
        )
        assert resp.status_code == 200
        assert resp.json()["interval_minutes"] == 60


class TestGetMonitor:
    @pytest.mark.asyncio
    async def test_get_existing(self, client):
        create_resp = await client.post(
            "/monitors",
            json={"url": "https://example.com", "type": "web", "interval_minutes": 60},
        )
        monitor_id = create_resp.json()["id"]
        resp = await client.get(f"/monitors/{monitor_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == monitor_id

    @pytest.mark.asyncio
    async def test_get_not_found(self, client):
        resp = await client.get("/monitors/nonexistent")
        assert resp.status_code == 404


class TestDeleteMonitor:
    @pytest.mark.asyncio
    async def test_delete_existing(self, client):
        create_resp = await client.post(
            "/monitors",
            json={"url": "https://example.com", "type": "web", "interval_minutes": 60},
        )
        monitor_id = create_resp.json()["id"]
        resp = await client.delete(f"/monitors/{monitor_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

        # Verify it's gone
        list_resp = await client.get("/monitors")
        assert list_resp.json() == []

    @pytest.mark.asyncio
    async def test_delete_not_found(self, client):
        resp = await client.delete("/monitors/nonexistent")
        assert resp.status_code == 404


class TestMonitorHistory:
    @pytest.mark.asyncio
    async def test_history_empty(self, client):
        resp = await client.get("/monitors/nonexistent/history")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_history_with_snapshot(self, client, engine):
        create_resp = await client.post(
            "/monitors",
            json={"url": "https://example.com", "type": "web", "interval_minutes": 60},
        )
        monitor_id = create_resp.json()["id"]
        # Simulate a stored snapshot
        engine.storage.save(monitor_id, "<html>content</html>")

        resp = await client.get(f"/monitors/{monitor_id}/history")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["monitor_name"] == monitor_id
        assert "checked_at" in data[0]
