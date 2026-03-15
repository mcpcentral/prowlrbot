# -*- coding: utf-8 -*-
"""Tests for Bundle model and store CRUD."""

import tempfile

from prowlrbot.marketplace.models import (
    Bundle,
    MarketplaceCategory,
    MarketplaceListing,
)
from prowlrbot.marketplace.store import MarketplaceStore


def _tmp_store():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    return MarketplaceStore(db_path=tmp.name)


def test_bundle_model():
    b = Bundle(
        id="security-starter",
        name="Security Starter",
        description="OWASP audit, JWT review",
        emoji="shield",
        color="#00e5ff",
        listing_ids=["skill-1", "skill-2"],
    )
    assert b.id == "security-starter"
    assert len(b.listing_ids) == 2


def test_create_and_get_bundle():
    store = _tmp_store()
    b = Bundle(
        id="test-bundle",
        name="Test Bundle",
        description="A test",
        listing_ids=["a", "b", "c"],
    )
    store.create_bundle(b)
    fetched = store.get_bundle("test-bundle")
    assert fetched is not None
    assert fetched.name == "Test Bundle"
    assert fetched.listing_ids == ["a", "b", "c"]
    store.close()


def test_list_bundles():
    store = _tmp_store()
    store.create_bundle(
        Bundle(id="b1", name="B1", description="x", listing_ids=[]),
    )
    store.create_bundle(
        Bundle(id="b2", name="B2", description="y", listing_ids=[]),
    )
    bundles = store.list_bundles()
    assert len(bundles) == 2
    store.close()


def test_increment_bundle_install_count():
    store = _tmp_store()
    store.create_bundle(
        Bundle(id="b1", name="B1", description="x", listing_ids=[]),
    )
    store.increment_bundle_installs("b1")
    fetched = store.get_bundle("b1")
    assert fetched is not None
    assert fetched.install_count == 1
    store.close()
