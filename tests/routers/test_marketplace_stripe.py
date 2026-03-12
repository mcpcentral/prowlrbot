"""Tests for Stripe tip jar with graceful degradation."""
import importlib.util
import sys
import tempfile
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from prowlrbot.marketplace.models import MarketplaceCategory, MarketplaceListing
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
    s.publish_listing(MarketplaceListing(
        id="tippable",
        author_id="author1",
        title="Tippable Skill",
        description="test",
        category=MarketplaceCategory.skills,
    ))
    yield s
    s.close()


@pytest.fixture
def client(store):
    mod = _load_marketplace_module()
    router = mod.router
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    with patch.object(mod, "_get_store", return_value=store):
        yield TestClient(app)


def test_tip_returns_503_when_stripe_not_configured(client):
    """Without STRIPE_SECRET_KEY, tip returns 503."""
    import os
    env = {k: v for k, v in os.environ.items() if k != "STRIPE_SECRET_KEY"}
    with patch.dict("os.environ", env, clear=True):
        resp = client.post("/marketplace/listings/tippable/tip", json={"amount": 5})
        assert resp.status_code == 503


def test_tip_validates_amount_range(client):
    """Tip below $1 or above $100 is rejected."""
    with patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}):
        resp = client.post("/marketplace/listings/tippable/tip", json={"amount": 0.50})
        assert resp.status_code == 400

        resp = client.post("/marketplace/listings/tippable/tip", json={"amount": 150})
        assert resp.status_code == 400


def test_tip_not_found_listing(client):
    resp = client.post("/marketplace/listings/nonexistent/tip", json={"amount": 5})
    assert resp.status_code == 404
