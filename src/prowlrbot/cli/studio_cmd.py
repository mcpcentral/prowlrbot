# -*- coding: utf-8 -*-
"""Prowlr-Studio management commands."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click


@click.group("studio")
def studio_cmd() -> None:
    """Manage Prowlr-Studio workspace."""
    pass


@studio_cmd.command("start")
@click.option("--host", default="127.0.0.1", help="Studio backend host")
@click.option("--port", default=3211, type=int, help="Studio backend port")
@click.option("--dev", is_flag=True, help="Start in development mode")
def start_cmd(host: str, port: int, dev: bool) -> None:
    """Start Prowlr-Studio backend and frontend."""
    studio_dir = _find_studio_dir()
    if not studio_dir:
        click.echo("Error: Prowlr-Studio not found. Install with: prowlr studio install")
        sys.exit(1)

    click.echo(f"Starting Prowlr-Studio on {host}:{port}...")

    from prowlrbot.config.utils import load_config

    config = load_config()
    api_port = getattr(config, "port", 8088)

    env = {
        "HOST": host,
        "PORT": str(port),
        "AUTH_PROVIDER": "prowlrbot",
        "PROWLRBOT_API_URL": f"http://127.0.0.1:{api_port}",
    }

    if dev:
        cmd = ["bun", "run", "dev"]
    else:
        cmd = ["bun", "run", "start"]

    try:
        import os

        subprocess.run(cmd, cwd=str(studio_dir), env={**dict(os.environ), **env})
    except FileNotFoundError:
        click.echo("Error: 'bun' not found. Install Bun: https://bun.sh")
        sys.exit(1)


@studio_cmd.command("status")
def status_cmd() -> None:
    """Show Prowlr-Studio status."""
    studio_dir = _find_studio_dir()
    if studio_dir:
        click.echo(f"Studio directory: {studio_dir}")
        click.echo("Studio: installed")
    else:
        click.echo("Studio: not installed")

    import urllib.request

    try:
        urllib.request.urlopen("http://127.0.0.1:3211/api/v1/health", timeout=2)
        click.echo("Studio backend: running (port 3211)")
    except Exception:
        click.echo("Studio backend: not running")


@studio_cmd.command("install")
@click.option("--dir", "install_dir", default=None, help="Installation directory")
def install_cmd(install_dir: str | None) -> None:
    """Install Prowlr-Studio from GitHub."""
    target = Path(install_dir) if install_dir else Path.home() / ".prowlrbot" / "studio"
    if target.exists() and any(target.iterdir()):
        click.echo(f"Studio already exists at {target}")
        return

    click.echo(f"Installing Prowlr-Studio to {target}...")
    target.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            ["git", "clone", "https://github.com/ProwlrBot/prowrl-studio.git", str(target)],
            check=True,
        )
        subprocess.run(["bun", "install"], cwd=str(target), check=True)
        click.echo(f"Prowlr-Studio installed to {target}")
        click.echo("Start with: prowlr studio start")
    except subprocess.CalledProcessError as e:
        click.echo(f"Installation failed: {e}")
        sys.exit(1)


def _find_studio_dir() -> Path | None:
    """Find Prowlr-Studio installation directory."""
    import os

    candidates = [
        Path.home() / ".prowlrbot" / "studio",
        Path.cwd() / "prowrl-studio",
    ]
    if os.environ.get("PROWLRBOT_DEV"):
        candidates.append(Path("/tmp/prowrl-studio-full"))
    for path in candidates:
        if (path / "package.json").exists():
            return path
    return None
