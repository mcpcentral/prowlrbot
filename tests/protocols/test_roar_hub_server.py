# -*- coding: utf-8 -*-
"""Tests for the Discovery Hub server."""

from __future__ import annotations

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from prowlrbot.protocols.sdk.discovery.hub_server import create_hub_router


def _make_app(api_key: str = "") -> TestClient:
    """Create a test client with the hub router mounted."""
    app = FastAPI()
    app.include_router(create_hub_router(api_key=api_key))
    return TestClient(app)


def _agent_payload(
    did: str = "",
    display_name: str = "test-agent",
    capabilities: list = None,
    **kwargs,
) -> dict:
    """Build a register agent request body."""
    body = {
        "did": did,
        "display_name": display_name,
        "agent_type": "agent",
        "description": f"{display_name} description",
        "skills": kwargs.get("skills", []),
        "channels": kwargs.get("channels", []),
        "endpoints": kwargs.get("endpoints", {}),
        "capabilities": capabilities or [],
    }
    body.update(kwargs)
    return body


class TestHubServerRegistration(unittest.TestCase):
    """Tests for agent registration endpoints."""

    def test_register_agent(self):
        client = _make_app()
        resp = client.post(
            "/agents",
            json=_agent_payload(display_name="planner"),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "planner"
        assert "did" in data
        assert data["registered_at"] > 0

    def test_register_with_explicit_did(self):
        client = _make_app()
        resp = client.post(
            "/agents",
            json=_agent_payload(
                did="did:roar:agent:custom-123",
                display_name="custom",
            ),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["did"] == "did:roar:agent:custom-123"

    def test_register_with_capabilities(self):
        client = _make_app()
        resp = client.post(
            "/agents",
            json=_agent_payload(
                display_name="capable",
                capabilities=["code-review", "testing"],
            ),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "code-review" in data["capabilities"]
        assert "testing" in data["capabilities"]


class TestHubServerLookup(unittest.TestCase):
    """Tests for agent lookup endpoints."""

    def test_lookup_by_did(self):
        client = _make_app()
        # Register first
        reg = client.post(
            "/agents",
            json=_agent_payload(
                did="did:roar:agent:lookup-test",
                display_name="lookup",
            ),
        )
        did = reg.json()["did"]

        # Lookup
        resp = client.get(f"/agents/{did}")
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "lookup"

    def test_lookup_missing_returns_404(self):
        client = _make_app()
        resp = client.get("/agents/did:roar:agent:nonexistent-123")
        assert resp.status_code == 404


class TestHubServerSearch(unittest.TestCase):
    """Tests for agent search endpoints."""

    def test_search_by_capability(self):
        client = _make_app()
        client.post(
            "/agents",
            json=_agent_payload(
                did="did:roar:agent:reviewer-1",
                display_name="reviewer",
                capabilities=["code-review"],
            ),
        )
        client.post(
            "/agents",
            json=_agent_payload(
                did="did:roar:agent:deployer-1",
                display_name="deployer",
                capabilities=["deploy"],
            ),
        )

        resp = client.get("/agents", params={"q": "code-review"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["agents"][0]["display_name"] == "reviewer"

    def test_search_no_results(self):
        client = _make_app()
        resp = client.get("/agents", params={"q": "nonexistent"})
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_list_all_agents(self):
        client = _make_app()
        client.post(
            "/agents",
            json=_agent_payload(did="did:roar:agent:a-1", display_name="a"),
        )
        client.post(
            "/agents",
            json=_agent_payload(did="did:roar:agent:b-1", display_name="b"),
        )

        resp = client.get("/agents")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2


class TestHubServerUnregister(unittest.TestCase):
    """Tests for agent unregister endpoint."""

    def test_unregister(self):
        client = _make_app()
        client.post(
            "/agents",
            json=_agent_payload(
                did="did:roar:agent:removable-1",
                display_name="removable",
            ),
        )

        resp = client.delete("/agents/did:roar:agent:removable-1")
        assert resp.status_code == 200
        assert resp.json()["status"] == "removed"

        # Verify gone
        resp = client.get("/agents/did:roar:agent:removable-1")
        assert resp.status_code == 404

    def test_unregister_missing_returns_404(self):
        client = _make_app()
        resp = client.delete("/agents/did:roar:agent:nope-123")
        assert resp.status_code == 404


class TestHubServerAuth(unittest.TestCase):
    """Tests for API key authentication."""

    def test_valid_api_key(self):
        client = _make_app(api_key="secret-key-123")
        resp = client.post(
            "/agents",
            json=_agent_payload(display_name="authed"),
            headers={"X-API-Key": "secret-key-123"},
        )
        assert resp.status_code == 200

    def test_missing_api_key_returns_401(self):
        client = _make_app(api_key="secret-key-123")
        resp = client.post(
            "/agents",
            json=_agent_payload(display_name="noauth"),
        )
        assert resp.status_code == 401

    def test_wrong_api_key_returns_401(self):
        client = _make_app(api_key="secret-key-123")
        resp = client.post(
            "/agents",
            json=_agent_payload(display_name="wrongauth"),
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401

    def test_no_auth_when_key_empty(self):
        """No API key requirement when api_key is empty string."""
        client = _make_app(api_key="")
        resp = client.post(
            "/agents",
            json=_agent_payload(display_name="nokeyrequired"),
        )
        assert resp.status_code == 200

    def test_auth_on_all_endpoints(self):
        """All endpoints enforce auth when api_key is set."""
        client = _make_app(api_key="key")

        assert client.get("/agents").status_code == 401
        assert client.get("/agents/did:roar:agent:x").status_code == 401
        assert client.delete("/agents/did:roar:agent:x").status_code == 401
        assert client.post("/agents", json=_agent_payload()).status_code == 401


class TestHubServerIntegration(unittest.TestCase):
    """Integration tests for the full hub workflow."""

    def test_register_lookup_search_unregister(self):
        """Full lifecycle: register, lookup, search, unregister."""
        client = _make_app()

        # Register
        resp = client.post(
            "/agents",
            json=_agent_payload(
                did="did:roar:agent:lifecycle-1",
                display_name="lifecycle",
                capabilities=["analyze"],
                skills=["analysis"],
                channels=["http"],
                endpoints={"http": "http://localhost:9000"},
            ),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["skills"] == ["analysis"]
        assert data["channels"] == ["http"]
        assert data["endpoints"] == {"http": "http://localhost:9000"}

        # Lookup
        resp = client.get("/agents/did:roar:agent:lifecycle-1")
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "lifecycle"

        # Search
        resp = client.get("/agents", params={"q": "analyze"})
        assert resp.json()["count"] == 1

        # Unregister
        resp = client.delete("/agents/did:roar:agent:lifecycle-1")
        assert resp.status_code == 200

        # Verify gone
        resp = client.get("/agents/did:roar:agent:lifecycle-1")
        assert resp.status_code == 404

        # Search returns empty
        resp = client.get("/agents", params={"q": "analyze"})
        assert resp.json()["count"] == 0


if __name__ == "__main__":
    unittest.main()
