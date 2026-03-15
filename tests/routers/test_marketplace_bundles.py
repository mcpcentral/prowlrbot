# -*- coding: utf-8 -*-
"""Tests for bundle API endpoints."""

import importlib.util
import sys
import tempfile
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from prowlrbot.marketplace.models import (
    Bundle,
    MarketplaceCategory,
    MarketplaceListing,
)
from prowlrbot.marketplace.store import MarketplaceStore


def _load_marketplace_module():
    """Load marketplace router module directly, bypassing the routers __init__
    which pulls in agentscope and other heavy dependencies."""
    module_name = "prowlrbot.app.routers.marketplace"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(
        module_name,
        "src/prowlrbot/app/routers/marketplace.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def store():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    s = MarketplaceStore(db_path=tmp.name)
    # Seed listings
    for slug in ["skill-a", "skill-b", "skill-c"]:
        s.publish_listing(
            MarketplaceListing(
                id=slug,
                author_id="test",
                title=slug,
                description="test",
                category=MarketplaceCategory.skills,
                status="approved",
            ),
        )
    # Seed a bundle
    s.create_bundle(
        Bundle(
            id="test-bundle",
            name="Test Bundle",
            description="A test bundle",
            listing_ids=["skill-a", "skill-b"],
        ),
    )
    yield s
    s.close()


@pytest.fixture
def client(store):
    marketplace_mod = _load_marketplace_module()
    from prowlrbot.auth.middleware import get_current_user
    from prowlrbot.auth.models import User, Role

    app = FastAPI()
    app.include_router(marketplace_mod.router)
    app.dependency_overrides[get_current_user] = lambda: User(
        id="test-user",
        username="tester",
        role=Role.admin,
    )
    original = marketplace_mod._get_store

    def _fake_get_store():
        return store

    marketplace_mod._get_store = _fake_get_store
    try:
        yield TestClient(app)
    finally:
        marketplace_mod._get_store = original


def test_list_bundles(client):
    resp = client.get("/marketplace/bundles")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == "test-bundle"


def test_get_bundle_detail(client):
    resp = client.get("/marketplace/bundles/test-bundle")
    assert resp.status_code == 200
    data = resp.json()
    assert data["bundle"]["name"] == "Test Bundle"
    assert len(data["listings"]) == 2


def test_get_bundle_not_found(client):
    resp = client.get("/marketplace/bundles/nonexistent")
    assert resp.status_code == 404


def test_install_bundle(client):
    resp = client.post("/marketplace/bundles/test-bundle/install")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["installed"]) == 2
    assert data["total"] == 2
