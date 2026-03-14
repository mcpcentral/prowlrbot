# -*- coding: utf-8 -*-
"""CLI commands for auth (e.g. set admin password from .env)."""

from __future__ import annotations

import os
from pathlib import Path

import click

from ..auth.store import UserStore


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
        env_path = Path.cwd() / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass


@click.command("set-admin-password")
@click.option(
    "--username",
    default=None,
    help="Admin username (default: PROWLRBOT_ADMIN_USERNAME or 'admin').",
)
@click.option(
    "--password",
    default=None,
    help="New password (default: PROWLRBOT_ADMIN_PASSWORD from .env).",
)
def set_admin_password_cmd(username: str | None, password: str | None) -> None:
    """Set the admin user's password from .env or options.

    Use this after setting PROWLRBOT_ADMIN_PASSWORD in .env so console login works.
    Loads .env from the current directory, then updates the admin user's stored
    password to match.
    """
    _load_dotenv()
    username = username or os.environ.get("PROWLRBOT_ADMIN_USERNAME", "admin")
    password = password or os.environ.get("PROWLRBOT_ADMIN_PASSWORD", "").strip()
    if not password:
        raise click.UsageError(
            "No password provided. Set PROWLRBOT_ADMIN_PASSWORD in .env or pass --password."
        )
    if len(password) < 12:
        raise click.UsageError("Password must be at least 12 characters.")
    store = UserStore()
    if store.update_password(username, password):
        click.echo(f"Password updated for user '{username}'.")
    else:
        raise click.ClickException(f"User '{username}' not found. Create the admin first (e.g. run the app once).")
