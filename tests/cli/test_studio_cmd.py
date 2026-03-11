# -*- coding: utf-8 -*-
"""Tests for studio CLI commands."""

import pytest
from click.testing import CliRunner
from prowlrbot.cli.main import cli


def test_studio_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["studio", "--help"])
    assert result.exit_code == 0
    assert "Prowlr-Studio" in result.output


def test_studio_status():
    runner = CliRunner()
    result = runner.invoke(cli, ["studio", "status"])
    assert result.exit_code == 0
    assert "Studio" in result.output


def test_studio_start_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["studio", "start", "--help"])
    assert result.exit_code == 0
    assert "--host" in result.output
    assert "--port" in result.output


def test_studio_install_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["studio", "install", "--help"])
    assert result.exit_code == 0
    assert "--dir" in result.output
