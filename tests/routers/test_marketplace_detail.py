# -*- coding: utf-8 -*-
"""Tests for listing detail endpoint with computed fields."""

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
    ReviewEntry,
    TipRecord,
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
    s.publish_listing(
        MarketplaceListing(
            id="test-skill",
            author_id="author1",
            title="Test Skill",
            description="A skill",
            category=MarketplaceCategory.skills,
            trust_tier="official",
            author_name="Author One",
            status="approved",
        ),
    )
    s.publish_listing(
        MarketplaceListing(
            id="related-skill",
            author_id="author1",
            title="Related Skill",
            description="Another skill",
            category=MarketplaceCategory.skills,
            tags=["testing"],
            status="approved",
        ),
    )
    s.add_review(
        ReviewEntry(
            listing_id="test-skill",
            reviewer_id="u1",
            rating=5,
            comment="Great",
        ),
    )
    s.add_tip(
        TipRecord(listing_id="test-skill", author_id="author1", amount=5.0),
    )
    s.create_bundle(
        Bundle(
            id="b1",
            name="B1",
            description="x",
            listing_ids=["test-skill"],
        ),
    )
    yield s
    s.close()


@pytest.fixture
def client(store):
    mod = _load_marketplace_module()
    app = FastAPI()
    app.include_router(mod.router)
    with patch.object(mod, "_get_store", return_value=store):
        yield TestClient(app)


def test_detail_has_computed_fields(client):
    resp = client.get("/marketplace/listings/test-skill/detail")
    assert resp.status_code == 200
    data = resp.json()
    assert data["listing"]["title"] == "Test Skill"
    assert data["install_command"] == "prowlr market install test-skill"
    assert data["tip_total"] == 5.0
    assert len(data["reviews"]) == 1
    assert "bundles" in data


def test_detail_not_found(client):
    resp = client.get("/marketplace/listings/nonexistent/detail")
    assert resp.status_code == 404
