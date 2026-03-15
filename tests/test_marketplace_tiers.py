# -*- coding: utf-8 -*-
"""Tests for /marketplace/tiers endpoint."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


def test_tiers_returns_three_items():
    from prowlrbot.app.routers.marketplace import router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    resp = client.get("/marketplace/tiers")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    ids = [t["id"] for t in data]
    assert "free" in ids
    assert "pro" in ids
    assert "team" in ids


def test_tiers_have_required_fields():
    from prowlrbot.app.routers.marketplace import router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    data = client.get("/marketplace/tiers").json()
    for tier in data:
        assert "id" in tier
        assert "name" in tier
        assert "price_label" in tier
        assert "credits_per_month" in tier
        assert "features" in tier
        assert isinstance(tier["features"], list)


def test_tiers_have_color_cta_fields():
    from prowlrbot.app.routers.marketplace import router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    data = client.get("/marketplace/tiers").json()
    for tier in data:
        assert "color" in tier
        assert "cta" in tier
        assert "cta_disabled" in tier
        assert isinstance(tier["cta_disabled"], bool)


def test_credit_transactions_returns_list():
    from prowlrbot.app.routers.marketplace import router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    resp = client.get("/marketplace/credits/test_user/transactions")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
