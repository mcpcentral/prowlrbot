# -*- coding: utf-8 -*-
"""Tests for marketplace CLI commands."""

import pytest
from click.testing import CliRunner
from prowlrbot.cli.market_cmd import market_group


@pytest.fixture
def runner():
    return CliRunner()


def test_market_search(runner):
    result = runner.invoke(market_group, ["search", "skills"])
    assert result.exit_code == 0


def test_market_list(runner):
    result = runner.invoke(market_group, ["list"])
    assert result.exit_code == 0


def test_market_update(runner):
    result = runner.invoke(market_group, ["update"])
    assert result.exit_code == 0
    output = result.output.lower()
    assert "synced" in output or "up to date" in output
