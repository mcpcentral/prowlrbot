# -*- coding: utf-8 -*-
"""Tests for marketplace API endpoint fixes."""

import importlib.util
import sys
import tempfile
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from prowlrbot.marketplace.models import (
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
    # Seed some listings
    for i, title in enumerate(["Alpha Tool", "Zeta Agent", "Beta Skill"]):
        s.publish_listing(
            MarketplaceListing(
                author_id="test",
                title=title,
                description=f"Description {i}",
                category=MarketplaceCategory.skills,
                downloads=100 - i * 30,
                rating=4.0 + i * 0.3,
                ratings_count=i + 1,
                status="approved",
            ),
        )
    yield s
    s.close()


@pytest.fixture
def client(store):
    marketplace_mod = _load_marketplace_module()
    app = FastAPI()
    app.include_router(marketplace_mod.router)
    # Patch _get_store directly on the module object
    original = marketplace_mod._get_store

    def _fake_get_store():
        return store

    marketplace_mod._get_store = _fake_get_store
    try:
        yield TestClient(app)
    finally:
        marketplace_mod._get_store = original


def test_sort_alpha(client):
    """sort=alpha returns listings in A-Z order."""
    resp = client.get("/marketplace/listings?sort=alpha")
    assert resp.status_code == 200
    titles = [l["title"] for l in resp.json()]
    assert titles == sorted(titles)


def test_sort_newest(client):
    """sort=newest returns listings newest first."""
    resp = client.get("/marketplace/listings?sort=newest")
    assert resp.status_code == 200
    dates = [l["created_at"] for l in resp.json()]
    assert dates == sorted(dates, reverse=True)


def test_q_alias_for_query(client):
    """Frontend sends q= but backend should accept it."""
    resp = client.get("/marketplace/listings?q=Alpha")
    assert resp.status_code == 200
    assert any("Alpha" in l["title"] for l in resp.json())
