# -*- coding: utf-8 -*-
"""CLI commands for data export and privacy controls."""

from __future__ import annotations

import json
import shutil
import tarfile
import time
from pathlib import Path

import click

from ..constant import WORKING_DIR, SECRET_DIR


@click.group(
    "export",
    help="Export and manage your ProwlrBot data (GDPR-friendly).",
)
def export_group() -> None:
    pass


@export_group.command("all")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output file. Defaults to ~/prowlrbot-export-<timestamp>.tar.gz",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["tar.gz", "json"]),
    default="tar.gz",
    help="Export format.",
)
def export_all(output: str | None, fmt: str) -> None:
    """Export all user data (config, chats, skills, memory)."""
    timestamp = time.strftime("%Y-%m-%dT%H-%M-%S")

    if fmt == "json":
        out_path = (
            Path(output)
            if output
            else Path.home() / f"prowlrbot-export-{timestamp}.json"
        )
        data = _collect_export_data()
        out_path.write_text(
            json.dumps(data, indent=2, default=str),
            encoding="utf-8",
        )
    else:
        out_path = (
            Path(output)
            if output
            else Path.home() / f"prowlrbot-export-{timestamp}.tar.gz"
        )
        with tarfile.open(str(out_path), "w:gz") as tar:
            if WORKING_DIR.is_dir():
                tar.add(str(WORKING_DIR), arcname="prowlrbot")

    size_kb = out_path.stat().st_size / 1024
    click.echo(f"Exported to: {out_path} ({size_kb:.0f} KB)")


@export_group.command("chats")
@click.option("--output", "-o", type=click.Path(), default=None)
def export_chats(output: str | None) -> None:
    """Export chat history only."""
    chats_dir = WORKING_DIR / "chats"
    if not chats_dir.is_dir():
        click.echo("No chat history found.")
        return

    timestamp = time.strftime("%Y-%m-%dT%H-%M-%S")
    out_path = (
        Path(output) if output else Path.home() / f"prowlrbot-chats-{timestamp}.json"
    )

    chats = []
    for f in chats_dir.glob("*.json"):
        try:
            chats.append(json.loads(f.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass

    out_path.write_text(
        json.dumps(chats, indent=2, default=str),
        encoding="utf-8",
    )
    click.echo(f"Exported {len(chats)} chat(s) to: {out_path}")


@export_group.command("config")
def export_config() -> None:
    """Print current configuration (secrets redacted)."""
    config_path = WORKING_DIR / "config.json"
    if not config_path.is_file():
        click.echo("No config.json found.")
        return

    data = json.loads(config_path.read_text(encoding="utf-8"))
    # Redact any keys that look like secrets
    _redact_secrets(data)
    click.echo(json.dumps(data, indent=2))


@export_group.command("retention")
@click.option(
    "--days",
    type=int,
    default=30,
    help="Delete data older than N days.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without deleting.",
)
def apply_retention(days: int, dry_run: bool) -> None:
    """Apply data retention policy — delete data older than N days."""
    import time as _time

    cutoff = _time.time() - (days * 86400)
    deleted = 0

    # Clean old chat files
    chats_dir = WORKING_DIR / "chats"
    if chats_dir.is_dir():
        for f in chats_dir.glob("*.json"):
            if f.stat().st_mtime < cutoff:
                if dry_run:
                    click.echo(f"  [dry-run] Would delete: {f.name}")
                else:
                    f.unlink()
                deleted += 1

    action = "Would delete" if dry_run else "Deleted"
    click.echo(f"{action} {deleted} file(s) older than {days} days.")


def _collect_export_data() -> dict:
    """Collect all exportable data into a dict."""
    data: dict = {
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data": {},
    }

    # Config (redacted)
    config_path = WORKING_DIR / "config.json"
    if config_path.is_file():
        try:
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
            _redact_secrets(cfg)
            data["data"]["config"] = cfg
        except (json.JSONDecodeError, OSError):
            pass

    # Chats
    chats_dir = WORKING_DIR / "chats"
    if chats_dir.is_dir():
        chats = []
        for f in sorted(chats_dir.glob("*.json")):
            try:
                chats.append(json.loads(f.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                pass
        data["data"]["chats"] = chats

    # Skills listing
    skills_dir = WORKING_DIR / "active_skills"
    if skills_dir.is_dir():
        data["data"]["skills"] = [d.name for d in skills_dir.iterdir() if d.is_dir()]

    return data


def _redact_secrets(obj: dict) -> None:
    """Recursively redact values that look like secrets."""
    secret_keys = {"token", "key", "secret", "password", "api_key", "apikey"}
    for k, v in obj.items():
        if isinstance(v, dict):
            _redact_secrets(v)
        elif isinstance(v, str) and any(s in k.lower() for s in secret_keys):
            if len(v) > 4:
                obj[k] = v[:4] + "****"
