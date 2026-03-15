# -*- coding: utf-8 -*-
"""Agent CLI commands — install, list, remove, health, team up external agents."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import click

from ..constant import WORKING_DIR
from ..external_agents.manager import ExternalAgentManager
from ..external_agents.models import AgentBackendType, ExternalAgentConfig


def _get_manager() -> ExternalAgentManager:
    return ExternalAgentManager(db_path=WORKING_DIR / "external_agents.db")


# ── Agent group ──────────────────────────────────────────────────────────────


@click.group(
    name="agent",
    help="Manage external agents — install, remove, list, health",
)
def agent_group():
    """External agent management."""
    pass


# ── Install (wizard) ─────────────────────────────────────────────────────────


@agent_group.command(name="install")
@click.argument("name", required=False)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True),
    help="Install from YAML/JSON config file",
)
@click.option(
    "--type",
    "backend",
    type=click.Choice(
        ["claude_code", "codex", "custom_cli", "http_api", "docker"],
    ),
    help="Agent backend type",
)
@click.option("--command", default="", help="CLI command or Docker image")
@click.option("--api-url", default="", help="HTTP API endpoint")
@click.option("--api-key", default="", help="API key for HTTP agents")
def agent_install(
    name: str | None,
    config_path: str | None,
    backend: str | None,
    command: str,
    api_url: str,
    api_key: str,
):
    """Install an external agent. Interactive wizard if no flags provided."""
    mgr = _get_manager()

    # Config file mode — auto-detect if path given as name
    if (
        not config_path
        and name
        and Path(name).exists()
        and Path(name).suffix in (".json", ".yaml", ".yml")
    ):
        config_path = name
        name = None

    if config_path:
        _install_from_config(mgr, Path(config_path))
        return

    # Interactive wizard mode
    if not name:
        click.echo()
        click.echo("  ╔══════════════════════════════════════╗")
        click.echo("  ║   Agent Install Wizard               ║")
        click.echo("  ╚══════════════════════════════════════╝")
        click.echo()
        name = click.prompt("  Agent name", type=str)

    # Auto-detect backend from agent name
    if not backend:
        _auto_backends = {
            "claude": "claude_code",
            "claude-code": "claude_code",
            "codex": "codex",
            "openai-codex": "codex",
        }
        detected = _auto_backends.get(name.lower().strip())
        if detected:
            click.echo(f"  Auto-detected backend: {detected}")
            backend = detected

    if not backend:
        click.echo()
        click.echo("  Available backends:")
        click.echo("    1) claude_code  — Claude Code CLI agent")
        click.echo("    2) codex        — OpenAI Codex CLI agent")
        click.echo("    3) custom_cli   — Any CLI tool as agent")
        click.echo("    4) http_api     — HTTP/REST API agent")
        click.echo("    5) docker       — Docker container agent")
        click.echo()
        choice = click.prompt("  Select backend [1-5]", type=int, default=1)
        backend_map = {
            1: "claude_code",
            2: "codex",
            3: "custom_cli",
            4: "http_api",
            5: "docker",
        }
        backend = backend_map.get(choice, "custom_cli")

    backend_type = AgentBackendType(backend)

    # Prompt for backend-specific config
    if (
        backend_type
        in (
            AgentBackendType.CUSTOM_CLI,
            AgentBackendType.CLAUDE_CODE,
            AgentBackendType.CODEX,
        )
        and not command
    ):
        default_cmd = {
            "claude_code": "claude",
            "codex": "codex",
            "custom_cli": "",
        }.get(
            backend,
            "",
        )
        command = click.prompt("  Command", default=default_cmd)

    if backend_type == AgentBackendType.DOCKER and not command:
        command = click.prompt("  Docker image", type=str)

    if backend_type == AgentBackendType.HTTP_API:
        if not api_url:
            api_url = click.prompt("  API URL", type=str)
        if not api_key:
            api_key = click.prompt(
                "  API Key (optional)",
                default="",
                show_default=False,
            )

    config = ExternalAgentConfig(
        name=name,
        backend_type=backend_type,
        command=command,
        api_url=api_url,
        api_key=api_key,
    )
    registered = mgr.register_agent(config)

    click.echo()
    click.echo(f"  Installed agent: {registered.name}")
    click.echo(f"  ID:      {registered.id}")
    click.echo(f"  Backend: {registered.backend_type}")

    # Run health check
    if click.confirm("  Run health check?", default=True):
        status = asyncio.run(mgr.check_agent_health(registered.id))
        if status.available:
            click.echo("  Health: OK")
        else:
            click.echo(
                f"  Health: UNAVAILABLE — {status.error or 'check failed'}",
            )

    click.echo()
    mgr.close()


def _install_from_config(mgr: ExternalAgentManager, path: Path) -> None:
    """Install agent(s) from a JSON or YAML config file."""
    text = path.read_text()
    if path.suffix in (".yaml", ".yml"):
        try:
            import yaml

            data = yaml.safe_load(text)
        except ImportError:
            click.echo(
                "Error: PyYAML required for YAML configs. Install with: pip install pyyaml",
            )
            return
    else:
        data = json.loads(text)

    # Support single agent or list
    agents = data if isinstance(data, list) else [data]
    for agent_data in agents:
        config = ExternalAgentConfig(**agent_data)
        registered = mgr.register_agent(config)
        click.echo(f"  Installed: {registered.name} ({registered.id})")

    mgr.close()


# ── List ─────────────────────────────────────────────────────────────────────


@agent_group.command(name="list")
@click.option(
    "--all",
    "show_all",
    is_flag=True,
    help="Include disabled agents",
)
def agent_list(show_all: bool):
    """List installed external agents."""
    mgr = _get_manager()
    agents = mgr.list_agents(enabled_only=not show_all)

    if not agents:
        click.echo(
            "No agents installed. Run 'prowlr agent install' to add one.",
        )
        mgr.close()
        return

    click.echo()
    click.echo(f"  {'ID':<16} {'Name':<20} {'Backend':<14} {'Enabled':<9}")
    click.echo(f"  {'─'*16} {'─'*20} {'─'*14} {'─'*9}")
    for a in agents:
        enabled = "yes" if a.enabled else "no"
        click.echo(
            f"  {a.id:<16} {a.name:<20} {a.backend_type:<14} {enabled:<9}",
        )
    click.echo()
    mgr.close()


# ── Remove ───────────────────────────────────────────────────────────────────


@agent_group.command(name="remove")
@click.argument("agent_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def agent_remove(agent_id: str, force: bool):
    """Remove an external agent."""
    mgr = _get_manager()
    agent = mgr.get_agent(agent_id)

    if not agent:
        click.echo(f"Agent '{agent_id}' not found.")
        mgr.close()
        return

    if not force and not click.confirm(
        f"Remove agent '{agent.name}' ({agent.id})?",
    ):
        click.echo("Cancelled.")
        mgr.close()
        return

    mgr.delete_agent(agent_id)
    click.echo(f"Removed agent: {agent.name}")
    mgr.close()


# ── Health ───────────────────────────────────────────────────────────────────


@agent_group.command(name="health")
@click.argument("agent_id", required=False)
def agent_health(agent_id: str | None):
    """Check health of agent(s). Checks all if no ID provided."""
    mgr = _get_manager()

    if agent_id:
        agents = [mgr.get_agent(agent_id)]
        if agents[0] is None:
            click.echo(f"Agent '{agent_id}' not found.")
            mgr.close()
            return
    else:
        agents = mgr.list_agents()

    if not agents:
        click.echo("No agents installed.")
        mgr.close()
        return

    click.echo()
    for agent in agents:
        if agent is None:
            continue
        status = asyncio.run(mgr.check_agent_health(agent.id))
        icon = "OK" if status.available else "FAIL"
        err = f" — {status.error}" if status.error else ""
        click.echo(f"  [{icon}] {agent.name} ({agent.backend_type}){err}")
    click.echo()
    mgr.close()


# ── Info ─────────────────────────────────────────────────────────────────────


@agent_group.command(name="info")
@click.argument("agent_id")
def agent_info(agent_id: str):
    """Show detailed info about an agent."""
    mgr = _get_manager()
    agent = mgr.get_agent(agent_id)

    if not agent:
        click.echo(f"Agent '{agent_id}' not found.")
        mgr.close()
        return

    click.echo()
    click.echo(f"  Name:      {agent.name}")
    click.echo(f"  ID:        {agent.id}")
    click.echo(f"  Backend:   {agent.backend_type}")
    click.echo(f"  Command:   {agent.command or '—'}")
    click.echo(f"  API URL:   {agent.api_url or '—'}")
    click.echo(f"  Timeout:   {agent.timeout_seconds}s")
    click.echo(f"  Enabled:   {'yes' if agent.enabled else 'no'}")
    if agent.environment:
        click.echo(f"  Env vars:  {len(agent.environment)} configured")
    click.echo()
    mgr.close()
