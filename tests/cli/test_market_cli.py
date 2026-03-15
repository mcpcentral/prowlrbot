# -*- coding: utf-8 -*-
"""Tests for marketplace CLI commands: bundles, install-bundle, detail, seed."""

import tempfile
from unittest.mock import patch

from click.testing import CliRunner

from prowlrbot.marketplace.models import (
    Bundle,
    MarketplaceCategory,
    MarketplaceListing,
)
from prowlrbot.marketplace.store import MarketplaceStore


def _tmp_store():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    return MarketplaceStore(db_path=tmp.name)


def _seeded_store():
    store = _tmp_store()
    store.publish_listing(
        MarketplaceListing(
            id="skill-a",
            author_id="prowlrbot",
            title="Skill Alpha",
            description="First skill",
            category=MarketplaceCategory.skills,
            status="approved",
        ),
    )
    store.publish_listing(
        MarketplaceListing(
            id="skill-b",
            author_id="prowlrbot",
            title="Skill Beta",
            description="Second skill",
            category=MarketplaceCategory.skills,
            status="approved",
        ),
    )
    store.create_bundle(
        Bundle(
            id="test-bundle",
            name="Test Bundle",
            description="A test bundle",
            emoji="rocket",
            color="#3b82f6",
            listing_ids=["skill-a", "skill-b"],
        ),
    )
    return store


def test_bundles_lists_bundles():
    """prowlr market bundles shows available bundles."""
    from prowlrbot.cli.market_cmd import market_bundles

    store = _seeded_store()
    runner = CliRunner()
    with patch("prowlrbot.cli.market_cmd._get_store", return_value=store):
        result = runner.invoke(market_bundles)
    assert result.exit_code == 0
    assert "Test Bundle" in result.output
    assert "test-bundle" in result.output
    store.close()


def test_bundles_empty():
    """prowlr market bundles with no bundles shows message."""
    from prowlrbot.cli.market_cmd import market_bundles

    store = _tmp_store()
    runner = CliRunner()
    with patch("prowlrbot.cli.market_cmd._get_store", return_value=store):
        result = runner.invoke(market_bundles)
    assert result.exit_code == 0
    assert "No bundles available" in result.output
    store.close()


def test_install_bundle_installs_all():
    """prowlr market install-bundle installs all listings in bundle."""
    from prowlrbot.cli.market_cmd import market_install_bundle

    store = _seeded_store()
    runner = CliRunner()
    with patch("prowlrbot.cli.market_cmd._get_store", return_value=store):
        result = runner.invoke(market_install_bundle, ["test-bundle"])
    assert result.exit_code == 0
    assert "Skill Alpha" in result.output
    assert "Skill Beta" in result.output
    assert "Installed 2/2" in result.output
    store.close()


def test_install_bundle_not_found():
    """prowlr market install-bundle with bad ID shows error."""
    from prowlrbot.cli.market_cmd import market_install_bundle

    store = _tmp_store()
    runner = CliRunner()
    with patch("prowlrbot.cli.market_cmd._get_store", return_value=store):
        result = runner.invoke(market_install_bundle, ["nonexistent"])
    assert result.exit_code == 0
    assert "not found" in result.output
    store.close()


def test_detail_shows_listing_info():
    """prowlr market detail shows full listing details."""
    from prowlrbot.cli.market_cmd import market_detail

    store = _seeded_store()
    runner = CliRunner()
    with patch("prowlrbot.cli.market_cmd._get_store", return_value=store):
        result = runner.invoke(market_detail, ["skill-a"])
    assert result.exit_code == 0
    assert "Skill Alpha" in result.output
    assert "VERIFIED" in result.output or "OFFICIAL" in result.output
    store.close()


def test_detail_not_found():
    """prowlr market detail with bad ID shows error."""
    from prowlrbot.cli.market_cmd import market_detail

    store = _tmp_store()
    runner = CliRunner()
    with patch("prowlrbot.cli.market_cmd._get_store", return_value=store):
        result = runner.invoke(market_detail, ["nonexistent"])
    assert result.exit_code == 0
    assert "not found" in result.output
    store.close()


def test_seed_creates_bundles():
    """prowlr market seed creates launch bundles."""
    from prowlrbot.cli.market_cmd import market_seed

    store = _tmp_store()
    db_path = store.db_path
    runner = CliRunner()
    with patch("prowlrbot.cli.market_cmd._get_store", return_value=store):
        result = runner.invoke(market_seed)
    assert result.exit_code == 0
    assert "Seeded 4 bundles" in result.output

    # Verify bundles were created (reopen since seed calls close)
    verify_store = MarketplaceStore(db_path=db_path)
    bundles = verify_store.list_bundles()
    assert len(bundles) == 4
    verify_store.close()


def test_seed_idempotent():
    """Running seed twice doesn't create duplicates."""
    from prowlrbot.cli.market_cmd import market_seed

    store1 = _tmp_store()
    db_path = store1.db_path
    runner = CliRunner()
    with patch("prowlrbot.cli.market_cmd._get_store", return_value=store1):
        runner.invoke(market_seed)

    # Second run with fresh store on same db
    store2 = MarketplaceStore(db_path=db_path)
    with patch("prowlrbot.cli.market_cmd._get_store", return_value=store2):
        result = runner.invoke(market_seed)
    assert result.exit_code == 0
    assert "Seeded 0 bundles" in result.output

    verify_store = MarketplaceStore(db_path=db_path)
    bundles = verify_store.list_bundles()
    assert len(bundles) == 4
    verify_store.close()
