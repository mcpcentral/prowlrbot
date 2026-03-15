# -*- coding: utf-8 -*-
"""Security tests for ProwlrHub HTTP bridge — auth, path validation, input limits."""

import os
import pytest
from fastapi.testclient import TestClient
from prowlrbot.hub.bridge import create_bridge_app


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Create a bridge app with an ephemeral database and rate limiting disabled."""
    db_path = str(tmp_path / "test_bridge.db")
    monkeypatch.setenv("PROWLR_HUB_DB", db_path)
    monkeypatch.setenv("PROWLR_NO_RATE_LIMIT", "1")
    monkeypatch.delenv("PROWLR_HUB_SECRET", raising=False)
    return create_bridge_app()


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def auth_app(tmp_path, monkeypatch):
    """Create a bridge app with auth enabled and rate limiting disabled."""
    db_path = str(tmp_path / "test_bridge_auth.db")
    monkeypatch.setenv("PROWLR_HUB_DB", db_path)
    monkeypatch.setenv("PROWLR_NO_RATE_LIMIT", "1")
    monkeypatch.setenv("PROWLR_HUB_SECRET", "test-secret-token-123")
    return create_bridge_app()


@pytest.fixture
def auth_client(auth_app):
    return TestClient(auth_app)


# --- Authentication (FINDING-02) ---


class TestAuthentication:
    def test_open_mode_no_secret(self, client):
        """Without PROWLR_HUB_SECRET, all endpoints are accessible."""
        resp = client.get("/health")
        assert resp.status_code == 200
        resp = client.get("/api/agents")
        assert resp.status_code == 200

    def test_auth_required_when_secret_set(self, auth_client):
        """With PROWLR_HUB_SECRET, endpoints require Bearer token."""
        resp = auth_client.get("/api/agents")
        assert resp.status_code == 401

    def test_auth_wrong_token(self, auth_client):
        resp = auth_client.get(
            "/api/agents",
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert resp.status_code == 403

    def test_auth_correct_token(self, auth_client):
        resp = auth_client.get(
            "/api/agents",
            headers={"Authorization": "Bearer test-secret-token-123"},
        )
        assert resp.status_code == 200

    def test_health_always_accessible(self, auth_client):
        """Health endpoint should work without auth for monitoring."""
        resp = auth_client.get("/health")
        assert resp.status_code == 200

    def test_status_page_always_accessible(self, auth_client):
        """Root status page should work without auth."""
        resp = auth_client.get("/")
        assert resp.status_code == 200

    def test_auth_register_requires_token(self, auth_client):
        resp = auth_client.post("/register", json={"name": "rogue-agent"})
        assert resp.status_code == 401

    def test_auth_register_with_token(self, auth_client):
        resp = auth_client.post(
            "/register",
            json={"name": "legit-agent"},
            headers={"Authorization": "Bearer test-secret-token-123"},
        )
        assert resp.status_code == 200


# --- Path Traversal (FINDING-05) ---


class TestPathTraversal:
    def _register_agent(self, client):
        resp = client.post("/register", json={"name": "test-agent"})
        data = resp.json()
        return data["agent_id"], data["session_id"]

    def _session_headers(self, session_id):
        return {"X-Session-Token": session_id}

    def test_absolute_path_rejected(self, client):
        agent_id, sid = self._register_agent(client)
        resp = client.post(
            f"/lock/{agent_id}",
            json={"path": "/etc/passwd"},
            headers=self._session_headers(sid),
        )
        assert resp.status_code == 400

    def test_traversal_path_rejected(self, client):
        agent_id, sid = self._register_agent(client)
        resp = client.post(
            f"/lock/{agent_id}",
            json={"path": "../../etc/passwd"},
            headers=self._session_headers(sid),
        )
        assert resp.status_code == 400

    def test_null_byte_rejected(self, client):
        agent_id, sid = self._register_agent(client)
        resp = client.post(
            f"/lock/{agent_id}",
            json={"path": "src/foo\x00.py"},
            headers=self._session_headers(sid),
        )
        assert resp.status_code == 400

    def test_normal_path_accepted(self, client):
        agent_id, sid = self._register_agent(client)
        resp = client.post(
            f"/lock/{agent_id}",
            json={"path": "src/main.py"},
            headers=self._session_headers(sid),
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_nested_path_accepted(self, client):
        agent_id, sid = self._register_agent(client)
        resp = client.post(
            f"/lock/{agent_id}",
            json={"path": "src/hub/engine.py"},
            headers=self._session_headers(sid),
        )
        assert resp.status_code == 200

    def test_backslash_absolute_rejected(self, client):
        agent_id, sid = self._register_agent(client)
        resp = client.post(
            f"/lock/{agent_id}",
            json={"path": "\\windows\\system32"},
            headers=self._session_headers(sid),
        )
        assert resp.status_code == 400


# --- Input Validation (FINDING-11) ---


class TestInputValidation:
    def _register(self, client):
        data = client.post("/register", json={"name": "test"}).json()
        return data["agent_id"], data["session_id"]

    def test_register_name_too_long(self, client):
        resp = client.post("/register", json={"name": "a" * 200})
        assert resp.status_code == 422  # Pydantic validation error

    def test_register_empty_name(self, client):
        resp = client.post("/register", json={"name": ""})
        assert resp.status_code == 422

    def test_broadcast_message_too_long(self, client):
        agent_id, sid = self._register(client)
        resp = client.post(
            f"/broadcast/{agent_id}",
            json={"message": "x" * 5000},
            headers={"X-Session-Token": sid},
        )
        assert resp.status_code == 422

    def test_broadcast_empty_message(self, client):
        agent_id, sid = self._register(client)
        resp = client.post(
            f"/broadcast/{agent_id}",
            json={"message": ""},
            headers={"X-Session-Token": sid},
        )
        assert resp.status_code == 422

    def test_finding_key_too_long(self, client):
        agent_id, sid = self._register(client)
        resp = client.post(
            f"/findings/{agent_id}",
            json={"key": "k" * 300, "value": "v"},
            headers={"X-Session-Token": sid},
        )
        assert resp.status_code == 422

    def test_lock_path_too_long(self, client):
        agent_id, sid = self._register(client)
        resp = client.post(
            f"/lock/{agent_id}",
            json={"path": "a/" * 600},
            headers={"X-Session-Token": sid},
        )
        assert resp.status_code == 422

    def test_invalid_priority_rejected(self, client):
        agent_id, sid = self._register(client)
        resp = client.post(
            f"/claim/{agent_id}",
            json={"title": "test task", "priority": "URGENT!!!"},
            headers={"X-Session-Token": sid},
        )
        assert resp.status_code == 400


# --- Limit Clamping (FINDING-06) ---


class TestLimitClamping:
    def test_events_limit_clamped(self, client):
        """Requesting limit=999999 should not crash or return unbounded results."""
        resp = client.get("/api/events?limit=999999")
        assert resp.status_code == 200

    def test_events_negative_limit(self, client):
        resp = client.get("/api/events?limit=-1")
        assert resp.status_code == 200

    def test_events_default_limit(self, client):
        resp = client.get("/api/events")
        assert resp.status_code == 200


# --- CORS (FINDING-10) ---


class TestCORS:
    def test_cors_allowed_origin(self, client):
        resp = client.options(
            "/api/agents",
            headers={
                "Origin": "http://localhost:8088",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert (
            resp.headers.get("access-control-allow-origin") == "http://localhost:8088"
        )

    def test_cors_disallowed_origin(self, client):
        resp = client.options(
            "/api/agents",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Should not reflect the evil origin
        assert resp.headers.get("access-control-allow-origin") != "http://evil.com"

    def test_cors_methods_restricted(self, client):
        resp = client.options(
            "/api/agents",
            headers={
                "Origin": "http://localhost:8088",
                "Access-Control-Request-Method": "GET",
            },
        )
        allowed = resp.headers.get("access-control-allow-methods", "")
        assert "DELETE" not in allowed
        assert "PUT" not in allowed


# --- Security Headers (FINDING-19) ---


class TestSecurityHeaders:
    def test_x_content_type_options(self, client):
        resp = client.get("/health")
        assert resp.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self, client):
        resp = client.get("/health")
        assert resp.headers.get("x-frame-options") == "DENY"

    def test_referrer_policy(self, client):
        resp = client.get("/health")
        assert resp.headers.get("referrer-policy") == "no-referrer"


# --- API Endpoints ---


class TestAPIEndpoints:
    def test_api_agents_returns_list(self, client):
        resp = client.get("/api/agents")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_api_board_returns_list(self, client):
        resp = client.get("/api/board")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_api_events_returns_list(self, client):
        resp = client.get("/api/events")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_api_context_returns_list(self, client):
        resp = client.get("/api/context")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_api_conflicts_returns_list(self, client):
        resp = client.get("/api/conflicts")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# --- Session Token Verification (FINDING-07) ---


class TestSessionTokenVerification:
    def _register(self, client):
        data = client.post("/register", json={"name": "session-test"}).json()
        return data["agent_id"], data["session_id"]

    def test_register_returns_session_id(self, client):
        resp = client.post("/register", json={"name": "verify-me"})
        data = resp.json()
        assert "session_id" in data
        assert len(data["session_id"]) > 0

    def test_missing_session_token_rejected(self, client):
        agent_id, _ = self._register(client)
        resp = client.post(
            f"/broadcast/{agent_id}",
            json={"message": "no token"},
        )
        assert resp.status_code == 401

    def test_wrong_session_token_rejected(self, client):
        agent_id, _ = self._register(client)
        resp = client.post(
            f"/broadcast/{agent_id}",
            json={"message": "wrong token"},
            headers={"X-Session-Token": "totally-wrong-token"},
        )
        assert resp.status_code == 403

    def test_valid_session_token_accepted(self, client):
        agent_id, sid = self._register(client)
        resp = client.post(
            f"/broadcast/{agent_id}",
            json={"message": "valid token"},
            headers={"X-Session-Token": sid},
        )
        assert resp.status_code == 200

    def test_session_token_prevents_impersonation(self, client):
        """Agent A's session token should not work for Agent B's endpoints."""
        agent_a, sid_a = self._register(client)
        agent_b, sid_b = self._register(client)
        # Use agent A's session token on agent B's endpoint
        resp = client.post(
            f"/broadcast/{agent_b}",
            json={"message": "impersonation attempt"},
            headers={"X-Session-Token": sid_a},
        )
        assert resp.status_code == 403

    def test_nonexistent_agent_returns_404(self, client):
        resp = client.post(
            "/broadcast/agent-nonexistent",
            json={"message": "ghost"},
            headers={"X-Session-Token": "any-token"},
        )
        assert resp.status_code == 404

    def test_lock_requires_session(self, client):
        agent_id, _ = self._register(client)
        resp = client.post(f"/lock/{agent_id}", json={"path": "src/test.py"})
        assert resp.status_code == 401

    def test_claim_requires_session(self, client):
        agent_id, _ = self._register(client)
        resp = client.post(f"/claim/{agent_id}", json={"title": "task"})
        assert resp.status_code == 401

    def test_heartbeat_requires_session(self, client):
        agent_id, _ = self._register(client)
        resp = client.post(f"/heartbeat/{agent_id}")
        assert resp.status_code == 401


# --- Rate Limiting (FINDING-13) ---


class TestRateLimiting:
    @pytest.fixture
    def rate_limited_app(self, tmp_path, monkeypatch):
        """Create a bridge app with rate limiting ENABLED."""
        db_path = str(tmp_path / "test_ratelimit.db")
        monkeypatch.setenv("PROWLR_HUB_DB", db_path)
        monkeypatch.delenv("PROWLR_HUB_SECRET", raising=False)
        monkeypatch.delenv("PROWLR_NO_RATE_LIMIT", raising=False)
        return create_bridge_app()

    @pytest.fixture
    def rate_limited_client(self, rate_limited_app):
        return TestClient(rate_limited_app)

    def test_register_rate_limited(self, rate_limited_client):
        """Exceeding 10 registrations per minute should return 429."""
        for i in range(11):
            resp = rate_limited_client.post(
                "/register",
                json={"name": f"agent-{i}"},
            )
            if resp.status_code == 429:
                assert "rate limit" in resp.json()["detail"].lower()
                return
        pytest.fail("Expected 429 rate limit after 11 rapid registrations")

    def test_read_endpoints_have_higher_limit(self, rate_limited_client):
        """GET endpoints allow 60/min — should not be exhausted in a few calls."""
        for _ in range(5):
            resp = rate_limited_client.get("/api/agents")
            assert resp.status_code == 200


# --- CSRF Protection (FINDING-18) ---


class TestCSRFProtection:
    def test_cross_origin_post_blocked_in_open_mode(self, client):
        """POST from evil origin should be blocked when no auth is configured."""
        resp = client.post(
            "/register",
            json={"name": "csrf-test"},
            headers={"Origin": "http://evil.com"},
        )
        assert resp.status_code == 403
        assert "cross-origin" in resp.json()["detail"].lower()

    def test_same_origin_post_allowed(self, client):
        """POST from allowed origin should work."""
        resp = client.post(
            "/register",
            json={"name": "legit-agent"},
            headers={"Origin": "http://localhost:8088"},
        )
        assert resp.status_code == 200

    def test_no_origin_post_allowed(self, client):
        """POST without Origin header should work (curl, MCP clients)."""
        resp = client.post("/register", json={"name": "curl-agent"})
        assert resp.status_code == 200

    def test_csrf_not_enforced_when_auth_enabled(self, auth_client):
        """When auth is enabled, Bearer token acts as CSRF protection."""
        resp = auth_client.post(
            "/register",
            json={"name": "auth-agent"},
            headers={
                "Authorization": "Bearer test-secret-token-123",
                "Origin": "http://evil.com",
            },
        )
        assert resp.status_code == 200
