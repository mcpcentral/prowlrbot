# -*- coding: utf-8 -*-
"""Click commands for monitor management."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import click

from prowlrbot.constant import WORKING_DIR


def _monitors_file() -> Path:
    return WORKING_DIR / "monitors.json"


def _load_monitors() -> list[dict]:
    f = _monitors_file()
    if f.exists():
        return json.loads(f.read_text())
    return []


def _save_monitors(monitors: list[dict]) -> None:
    f = _monitors_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(monitors, indent=2))


@click.group("monitor")
def monitor_group():
    """Manage web/API monitors."""
    pass


@monitor_group.command("list")
def list_monitors():
    """List configured monitors."""
    monitors = _load_monitors()
    if not monitors:
        click.echo("No monitors configured.")
        return
    for m in monitors:
        status = "enabled" if m.get("enabled", True) else "disabled"
        click.echo(f"  {m['name']}  [{m.get('type', 'web')}]  {m.get('url', '')}  ({status}, every {m.get('interval', '5m')})")


@monitor_group.command("add")
@click.option("--name", required=True, help="Unique monitor name")
@click.option("--url", required=True, help="URL to monitor")
@click.option("--interval", default="5m", help="Check interval (e.g. 30s, 5m, 1h)")
@click.option("--type", "monitor_type", default="web", type=click.Choice(["web", "api"]), help="Monitor type")
@click.option("--css-selector", default=None, help="CSS selector to extract (web only)")
@click.option("--json-path", default=None, help="JSON path to extract (api only)")
@click.option("--expected-status", default=200, type=int, help="Expected HTTP status (api only)")
def add_monitor(name, url, interval, monitor_type, css_selector, json_path, expected_status):
    """Add a new monitor."""
    from prowlrbot.monitor.config import parse_interval

    # Validate interval
    try:
        parse_interval(interval)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

    monitors = _load_monitors()

    # Check for duplicate name
    if any(m["name"] == name for m in monitors):
        click.echo(f"Error: Monitor '{name}' already exists.", err=True)
        raise SystemExit(1)

    entry: dict = {
        "name": name,
        "type": monitor_type,
        "url": url,
        "interval": interval,
        "enabled": True,
    }
    if monitor_type == "web" and css_selector:
        entry["css_selector"] = css_selector
    if monitor_type == "api":
        entry["expected_status"] = expected_status
        if json_path:
            entry["json_path"] = json_path

    monitors.append(entry)
    _save_monitors(monitors)
    click.echo(f"Added monitor '{name}' ({monitor_type}) for {url} every {interval}.")


@monitor_group.command("remove")
@click.argument("name")
def remove_monitor(name):
    """Remove a monitor by name."""
    monitors = _load_monitors()
    new_monitors = [m for m in monitors if m["name"] != name]
    if len(new_monitors) == len(monitors):
        click.echo(f"Monitor '{name}' not found.", err=True)
        raise SystemExit(1)

    _save_monitors(new_monitors)

    # Also clean storage
    from prowlrbot.monitor.storage import MonitorStorage

    try:
        storage = MonitorStorage()
        storage.delete(name)
        storage.close()
    except Exception:
        pass

    click.echo(f"Removed monitor '{name}'.")


@monitor_group.command("run")
@click.argument("name")
def run_monitor(name):
    """Run a single monitor check now."""
    monitors = _load_monitors()
    target = next((m for m in monitors if m["name"] == name), None)
    if target is None:
        click.echo(f"Monitor '{name}' not found.", err=True)
        raise SystemExit(1)

    from prowlrbot.monitor.config import parse_monitor_configs
    from prowlrbot.monitor.engine import MonitorEngine

    configs = parse_monitor_configs([target])
    engine = MonitorEngine()
    engine.add(configs[0])

    result = asyncio.run(engine.run_once(name))
    if result.error:
        click.echo(f"Error: {result.error}", err=True)
    elif result.changed:
        click.echo(f"Change detected: {result.diff_summary}")
    else:
        click.echo("No change detected.")

    engine.storage.close()
