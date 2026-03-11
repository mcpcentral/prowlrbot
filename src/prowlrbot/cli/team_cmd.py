# -*- coding: utf-8 -*-
"""Team CLI commands — create, list, add/remove members, start teams."""

from __future__ import annotations

import json
from pathlib import Path

import click

from ..constant import WORKING_DIR
from ..dashboard.agent_teams import (
    AgentTeam,
    CoordinationMode,
    TeamMember,
    TeamRole,
    TeamStore,
)
from ..external_agents.manager import ExternalAgentManager


def _get_store() -> TeamStore:
    return TeamStore(db_path=WORKING_DIR / "teams.db")


def _get_agent_mgr() -> ExternalAgentManager:
    return ExternalAgentManager(db_path=WORKING_DIR / "external_agents.db")


# ── Team group ───────────────────────────────────────────────────────────────


@click.group(name="team", help="Build and manage multi-agent teams")
def team_group():
    """Agent team management."""
    pass


# ── Create ───────────────────────────────────────────────────────────────────


@team_group.command(name="create")
@click.argument("name", required=False)
@click.option("--config", "config_path", type=click.Path(exists=True), help="Create from team.yaml config")
@click.option("--coordination", "-c", type=click.Choice(["round_robin", "hierarchical", "consensus", "auction"]), default="hierarchical")
@click.option("--description", "-d", default="")
def team_create(name: str | None, config_path: str | None, coordination: str, description: str):
    """Create a new agent team. Interactive wizard if no name provided."""
    store = _get_store()

    # Auto-detect: if name looks like a file path, treat as config
    if not config_path and name and Path(name).exists() and Path(name).suffix in (".json", ".yaml", ".yml"):
        config_path = name
        name = None

    # Config file mode
    if config_path:
        _create_from_config(store, Path(config_path))
        return

    # Interactive mode
    if not name:
        click.echo()
        click.echo("  ╔══════════════════════════════════════╗")
        click.echo("  ║   Team Builder                       ║")
        click.echo("  ╚══════════════════════════════════════╝")
        click.echo()
        name = click.prompt("  Team name", type=str)
        description = click.prompt("  Description (optional)", default="")
        click.echo()
        click.echo("  Coordination modes:")
        click.echo("    1) hierarchical — Director routes tasks to specialists")
        click.echo("    2) round_robin  — Tasks distributed evenly")
        click.echo("    3) consensus    — Agents vote on approach")
        click.echo("    4) auction      — Agents bid on tasks by capability")
        click.echo()
        choice = click.prompt("  Select mode [1-4]", type=int, default=1)
        coord_map = {1: "hierarchical", 2: "round_robin", 3: "consensus", 4: "auction"}
        coordination = coord_map.get(choice, "hierarchical")

    team = AgentTeam(
        name=name,
        description=description,
        coordination=CoordinationMode(coordination),
    )
    created = store.create_team(team)

    click.echo()
    click.echo(f"  Created team: {created.name}")
    click.echo(f"  ID:           {created.id}")
    click.echo(f"  Coordination: {created.coordination}")
    click.echo()

    # Offer to add members
    if click.confirm("  Add agents to this team now?", default=True):
        _interactive_add_members(store, created.id)

    store.close()


def _create_from_config(store: TeamStore, path: Path) -> None:
    """Create a team from a YAML/JSON config file."""
    text = path.read_text()
    if path.suffix in (".yaml", ".yml"):
        try:
            import yaml
            data = yaml.safe_load(text)
        except ImportError:
            click.echo("Error: PyYAML required for YAML configs. Install with: pip install pyyaml")
            return
    else:
        data = json.loads(text)

    members = []
    for m in data.get("agents", data.get("members", [])):
        members.append(TeamMember(
            agent_id=m.get("name", m.get("agent_id", "")),
            role=TeamRole(m.get("role", "specialist")),
            personality=m.get("personality", ""),
            skills=m.get("skills", []),
            model_preference=m.get("model_preference", ""),
        ))

    team = AgentTeam(
        name=data.get("name", path.stem),
        description=data.get("description", ""),
        coordination=CoordinationMode(data.get("coordination", {}).get("pattern", data.get("coordination", "hierarchical"))),
        fallback_strategy=data.get("fallback_strategy", "escalate"),
        members=members,
    )
    created = store.create_team(team)
    click.echo(f"  Created team '{created.name}' with {len(members)} member(s)")
    store.close()


def _interactive_add_members(store: TeamStore, team_id: str) -> None:
    """Interactively add agents to a team."""
    mgr = _get_agent_mgr()
    agents = mgr.list_agents()

    if agents:
        click.echo()
        click.echo("  Available agents:")
        for i, a in enumerate(agents, 1):
            click.echo(f"    {i}) {a.name} ({a.backend_type})")
        click.echo()

    while True:
        agent_id = click.prompt("  Agent ID or name (blank to finish)", default="", show_default=False)
        if not agent_id:
            break

        # Allow selection by number if agents exist
        if agents and agent_id.isdigit():
            idx = int(agent_id) - 1
            if 0 <= idx < len(agents):
                agent_id = agents[idx].id

        click.echo("  Roles: director, specialist, observer")
        role = click.prompt("  Role", default="specialist")

        member = TeamMember(
            agent_id=agent_id,
            role=TeamRole(role) if role in ("director", "specialist", "observer") else TeamRole.SPECIALIST,
        )
        store.add_member(team_id, member)
        click.echo(f"  Added {agent_id} as {member.role}")
        click.echo()

    mgr.close()


# ── List ─────────────────────────────────────────────────────────────────────


@team_group.command(name="list")
def team_list():
    """List all teams."""
    store = _get_store()
    teams = store.list_teams()

    if not teams:
        click.echo("No teams created. Run 'prowlr team create' to build one.")
        store.close()
        return

    click.echo()
    click.echo(f"  {'ID':<10} {'Name':<20} {'Members':<9} {'Coordination':<15}")
    click.echo(f"  {'─'*10} {'─'*20} {'─'*9} {'─'*15}")
    for t in teams:
        click.echo(f"  {t.id:<10} {t.name:<20} {len(t.members):<9} {t.coordination:<15}")
    click.echo()
    store.close()


# ── Info ─────────────────────────────────────────────────────────────────────


@team_group.command(name="info")
@click.argument("team_id")
def team_info(team_id: str):
    """Show team details and members."""
    store = _get_store()
    team = store.get_team(team_id)

    if not team:
        click.echo(f"Team '{team_id}' not found.")
        store.close()
        return

    click.echo()
    click.echo(f"  Name:         {team.name}")
    click.echo(f"  ID:           {team.id}")
    click.echo(f"  Description:  {team.description or '—'}")
    click.echo(f"  Coordination: {team.coordination}")
    click.echo(f"  Fallback:     {team.fallback_strategy}")
    click.echo()

    if team.members:
        click.echo(f"  Members ({len(team.members)}):")
        for m in team.members:
            skills = ", ".join(m.skills) if m.skills else "—"
            click.echo(f"    [{m.role}] {m.agent_id} (skills: {skills})")
    else:
        click.echo("  No members yet. Use 'prowlr team add-member' to add agents.")
    click.echo()
    store.close()


# ── Add member ───────────────────────────────────────────────────────────────


@team_group.command(name="add-member")
@click.argument("team_id")
@click.argument("agent_id")
@click.option("--role", "-r", type=click.Choice(["director", "specialist", "observer"]), default="specialist")
@click.option("--skills", "-s", multiple=True, help="Skills this member contributes")
def team_add_member(team_id: str, agent_id: str, role: str, skills: tuple):
    """Add an agent to a team."""
    store = _get_store()
    member = TeamMember(
        agent_id=agent_id,
        role=TeamRole(role),
        skills=list(skills),
    )
    if store.add_member(team_id, member):
        click.echo(f"Added {agent_id} as {role} to team {team_id}")
    else:
        click.echo(f"Team '{team_id}' not found.")
    store.close()


# ── Remove member ────────────────────────────────────────────────────────────


@team_group.command(name="remove-member")
@click.argument("team_id")
@click.argument("agent_id")
def team_remove_member(team_id: str, agent_id: str):
    """Remove an agent from a team."""
    store = _get_store()
    if store.remove_member(team_id, agent_id):
        click.echo(f"Removed {agent_id} from team {team_id}")
    else:
        click.echo(f"Member not found in team.")
    store.close()


# ── Delete ───────────────────────────────────────────────────────────────────


@team_group.command(name="delete")
@click.argument("team_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def team_delete(team_id: str, force: bool):
    """Delete a team."""
    store = _get_store()
    team = store.get_team(team_id)
    if not team:
        click.echo(f"Team '{team_id}' not found.")
        store.close()
        return

    if not force and not click.confirm(f"Delete team '{team.name}'?"):
        click.echo("Cancelled.")
        store.close()
        return

    store.delete_team(team_id)
    click.echo(f"Deleted team: {team.name}")
    store.close()
