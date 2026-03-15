# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime

import click

from ..constant import WORKING_DIR
from ..migrations.manager import MigrationManager
from ..migrations.registry import register_all

DB_NAME = "prowlrbot.db"


def _get_manager() -> MigrationManager:
    db_path = WORKING_DIR / DB_NAME
    manager = MigrationManager(db_path)
    register_all(manager)
    return manager


@click.group("migrate")
def migrate_group() -> None:
    """Database schema migrations."""


@migrate_group.command("up")
@click.option(
    "--to",
    "target",
    type=int,
    default=None,
    help="Apply migrations up to this version (inclusive). Default: all pending.",
)
def migrate_up(target: int | None) -> None:
    """Apply pending database migrations."""
    manager = _get_manager()

    pending = manager.get_pending()
    if target is not None:
        pending = [m for m in pending if m.version <= target]

    if not pending:
        click.echo("No pending migrations.")
        return

    click.echo(
        click.style(
            f"Applying {len(pending)} migration(s)...",
            fg="cyan",
        ),
    )

    applied = manager.migrate_up(target_version=target)
    for m in applied:
        click.echo(click.style(f"  v{m.version}", fg="green") + f"  {m.name}")

    click.echo(
        click.style(
            f"Done. Current version: v{manager.get_current_version()}",
            fg="green",
            bold=True,
        ),
    )


@migrate_group.command("down")
@click.option(
    "--to",
    "target",
    type=int,
    required=True,
    help="Roll back to this version (exclusive — migrations above this are removed).",
)
def migrate_down(target: int) -> None:
    """Roll back database migrations."""
    manager = _get_manager()
    current = manager.get_current_version()

    if target >= current:
        click.echo(f"Already at v{current}; nothing to roll back.")
        return

    click.echo(
        click.style(
            f"Rolling back from v{current} down to v{target}...",
            fg="yellow",
        ),
    )

    rolled_back = manager.migrate_down(target_version=target)
    for m in rolled_back:
        click.echo(click.style(f"  v{m.version}", fg="red") + f"  {m.name}")

    click.echo(
        click.style(
            f"Done. Current version: v{manager.get_current_version()}",
            fg="green",
            bold=True,
        ),
    )


@migrate_group.command("status")
def migrate_status() -> None:
    """Show current migration state."""
    manager = _get_manager()
    info = manager.status()

    click.echo(click.style("Migration Status", fg="cyan", bold=True))
    click.echo(f"  Database:        {WORKING_DIR / DB_NAME}")
    click.echo(f"  Current version: v{info['current_version']}")
    click.echo(f"  Pending:         {info['pending_count']}")
    click.echo(f"  Applied:         {len(info['applied'])}")

    pending = manager.get_pending()
    if pending:
        click.echo()
        click.echo(click.style("Pending migrations:", fg="yellow"))
        for m in pending:
            click.echo(f"    v{m.version}  {m.name}")


@migrate_group.command("history")
def migrate_history() -> None:
    """Show applied migration history."""
    manager = _get_manager()
    history = manager.get_history()

    if not history:
        click.echo("No migrations have been applied yet.")
        return

    click.echo(click.style("Applied Migrations", fg="cyan", bold=True))
    click.echo(f"  {'Version':<10} {'Name':<25} {'Applied At'}")
    click.echo(f"  {'-------':<10} {'----':<25} {'----------'}")

    for m in history:
        ts = ""
        if m.applied_at is not None:
            ts = datetime.datetime.fromtimestamp(
                m.applied_at,
                tz=datetime.timezone.utc,
            ).strftime("%Y-%m-%d %H:%M:%S UTC")
        click.echo(f"  v{m.version:<9} {m.name:<25} {ts}")
