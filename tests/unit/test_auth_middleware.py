# -*- coding: utf-8 -*-
"""Tests for auth middleware integration."""

from fastapi import FastAPI, APIRouter, Depends
from fastapi.testclient import TestClient

from prowlrbot.app.auth import AuthConfig, AuthDependency, generate_api_token, hash_token


def _create_test_app(auth_config: AuthConfig) -> FastAPI:
    """Create a minimal FastAPI app with auth."""
    app = FastAPI()
    auth = AuthDependency(auth_config)

    router = APIRouter(prefix="/api")

    @router.get("/test")
    async def test_endpoint(token: str = Depends(auth)):
        return {"status": "ok"}

    @router.get("/health")
    async def health():
        return {"status": "healthy"}

    app.include_router(router)
    return app


def test_auth_enabled_rejects_no_token():
    token = generate_api_token()
    config = AuthConfig(enabled=True, token_hash=hash_token(token))
    app = _create_test_app(config)
    client = TestClient(app)

    response = client.get("/api/test")
    assert response.status_code == 401


def test_auth_enabled_accepts_valid_token():
    token = generate_api_token()
    config = AuthConfig(enabled=True, token_hash=hash_token(token))
    app = _create_test_app(config)
    client = TestClient(app)

    response = client.get("/api/test", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_auth_enabled_rejects_invalid_token():
    token = generate_api_token()
    config = AuthConfig(enabled=True, token_hash=hash_token(token))
    app = _create_test_app(config)
    client = TestClient(app)

    response = client.get("/api/test", headers={"Authorization": "Bearer wrong-token"})
    assert response.status_code == 401


def test_auth_disabled_allows_all():
    config = AuthConfig(enabled=False)
    app = _create_test_app(config)
    client = TestClient(app)

    response = client.get("/api/test")
    assert response.status_code == 200


def test_health_endpoint_bypasses_auth():
    token = generate_api_token()
    config = AuthConfig(enabled=True, token_hash=hash_token(token))
    app = _create_test_app(config)
    client = TestClient(app)

    response = client.get("/api/health")
    assert response.status_code == 200
