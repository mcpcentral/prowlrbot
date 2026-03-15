# -*- coding: utf-8 -*-
"""Tests for marketplace install actually delivering skill files."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from prowlrbot.marketplace.models import (
    MarketplaceCategory,
    MarketplaceListing,
)
from prowlrbot.marketplace.store import MarketplaceStore


def _tmp_store():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    return MarketplaceStore(db_path=tmp.name)


def test_cli_install_creates_skill_directory():
    """CLI install should create skill files in customized_skills dir."""
    from click.testing import CliRunner
    from prowlrbot.cli.market_cmd import market_install

    store = _tmp_store()
    store.publish_listing(
        MarketplaceListing(
            id="test-pdf",
            author_id="prowlrbot",
            title="PDF Processor",
            description="Process PDFs",
            category=MarketplaceCategory.skills,
            status="approved",
        ),
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)

        with (
            patch("prowlrbot.cli.market_cmd._get_store", return_value=store),
            patch("prowlrbot.cli.market_cmd.WORKING_DIR", working_dir),
        ):
            runner = CliRunner()
            result = runner.invoke(market_install, ["test-pdf"])
            assert result.exit_code == 0

        # Should have created a manifest in the install location
        assert (working_dir / "marketplace" / "test-pdf"[:12]).exists()
    store.close()
