# -*- coding: utf-8 -*-
"""Tests for the Studio integration API router."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from prowlrbot.app.routers.studio import router as studio_router


@pytest.fixture
def app():
    """Minimal FastAPI app with just the studio router mounted."""
    _app = FastAPI()
    _app.include_router(studio_router)
    return _app


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_studio_health(client):
    resp = await client.get("/studio/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "uptime_seconds" in data
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_studio_agents_list_requires_auth(client):
    resp = await client.get("/studio/agents")
    # Requires auth — should be 401 without a Bearer token
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_studio_run_agent_requires_auth(client):
    resp = await client.post(
        "/studio/agents/test-agent/run",
        json={"query": "hello", "autonomy": "delegate"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_studio_stop_agent_requires_auth(client):
    resp = await client.post("/studio/agents/test-agent/stop")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_studio_message_agent_requires_auth(client):
    resp = await client.post(
        "/studio/agents/test-agent/message",
        json={"content": "hello"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_studio_update_autonomy_requires_auth(client):
    resp = await client.put(
        "/studio/agents/test-agent/autonomy",
        json={"level": "watch"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_studio_validate_token_missing_bearer(client):
    resp = await client.post("/studio/auth/validate")
    assert resp.status_code == 401
    assert "Missing Bearer token" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_studio_validate_token_invalid(client):
    resp = await client.post(
        "/studio/auth/validate",
        headers={"authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401
