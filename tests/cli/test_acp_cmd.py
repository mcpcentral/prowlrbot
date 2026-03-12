# -*- coding: utf-8 -*-
"""Tests for prowlr acp CLI command."""
from click.testing import CliRunner
from prowlrbot.cli.acp_cmd import acp_cmd


def test_acp_cmd_help():
    runner = CliRunner()
    result = runner.invoke(acp_cmd, ["--help"])
    assert result.exit_code == 0
    assert "ACP" in result.output or "stdio" in result.output


def test_acp_cmd_debug_flag_in_help():
    runner = CliRunner()
    result = runner.invoke(acp_cmd, ["--help"])
    assert "--debug" in result.output


def test_acp_cmd_registered():
    """acp must be registered in the main CLI."""
    from prowlrbot.cli.main import cli

    assert "acp" in cli.commands
