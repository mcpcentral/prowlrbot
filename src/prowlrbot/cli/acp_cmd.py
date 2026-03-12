# -*- coding: utf-8 -*-
"""CLI command to start the ACP server over stdio."""

from __future__ import annotations

import asyncio
import sys

import click


@click.command(name="acp", help="Start ACP server (JSON-RPC 2.0 over stdio) for IDE integration")
@click.option("--debug", is_flag=True, default=False, help="Enable debug logging")
def acp_cmd(debug: bool) -> None:
    """Start ProwlrBot as an ACP agent for VS Code / Zed / JetBrains."""
    import logging

    if debug:
        logging.basicConfig(level=logging.DEBUG)

    from ..protocols.acp_server import ACPServer

    click.echo("ProwlrBot ACP server starting on stdio...", err=True)
    server = ACPServer()
    try:
        asyncio.run(server.run_stdio())
    except KeyboardInterrupt:
        click.echo("ACP server stopped.", err=True)
        sys.exit(0)
