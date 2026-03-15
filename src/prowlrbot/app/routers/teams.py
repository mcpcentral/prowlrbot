# -*- coding: utf-8 -*-
"""Agent teams API — CRUD for team orchestration."""

from fastapi import APIRouter, HTTPException

from prowlrbot.constant import WORKING_DIR
from prowlrbot.dashboard.agent_teams import AgentTeam, TeamMember, TeamStore

router = APIRouter(prefix="/teams", tags=["teams"])

_DB_PATH = WORKING_DIR / "teams.db"
_store: TeamStore | None = None


def _get_store() -> TeamStore:
    global _store
    if _store is None:
        _store = TeamStore(_DB_PATH)
    return _store


# ── Team CRUD ────────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=AgentTeam,
    summary="Create a team",
    description="Create a new agent team",
)
async def create_team(team: AgentTeam) -> AgentTeam:
    """Create a new agent team."""
    try:
        return _get_store().create_team(team)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "",
    response_model=list[AgentTeam],
    summary="List teams",
    description="List all agent teams",
)
async def list_teams() -> list[AgentTeam]:
    """List all agent teams."""
    return _get_store().list_teams()


@router.get(
    "/{team_id}",
    response_model=AgentTeam,
    summary="Get a team",
    description="Get a team by ID",
)
async def get_team(team_id: str) -> AgentTeam:
    """Get a single team by ID."""
    team = _get_store().get_team(team_id)
    if team is None:
        raise HTTPException(
            status_code=404,
            detail=f"Team {team_id} not found",
        )
    return team


@router.put(
    "/{team_id}",
    response_model=AgentTeam,
    summary="Update a team",
    description="Update an existing agent team",
)
async def update_team(team_id: str, team: AgentTeam) -> AgentTeam:
    """Update an existing team."""
    if not _get_store().update_team(team_id, team):
        raise HTTPException(
            status_code=404,
            detail=f"Team {team_id} not found",
        )
    updated = _get_store().get_team(team_id)
    return updated


@router.delete(
    "/{team_id}",
    response_model=dict,
    summary="Delete a team",
    description="Delete an agent team",
)
async def delete_team(team_id: str) -> dict:
    """Delete a team."""
    if not _get_store().delete_team(team_id):
        raise HTTPException(
            status_code=404,
            detail=f"Team {team_id} not found",
        )
    return {"deleted": True}


# ── Member management ────────────────────────────────────────────────────────


@router.post(
    "/{team_id}/members",
    response_model=dict,
    summary="Add a member",
    description="Add an agent to a team",
)
async def add_member(team_id: str, member: TeamMember) -> dict:
    """Add a member to a team."""
    if not _get_store().add_member(team_id, member):
        raise HTTPException(
            status_code=404,
            detail=f"Team {team_id} not found",
        )
    return {"added": True}


@router.delete(
    "/{team_id}/members/{agent_id}",
    response_model=dict,
    summary="Remove a member",
    description="Remove an agent from a team",
)
async def remove_member(team_id: str, agent_id: str) -> dict:
    """Remove a member from a team."""
    if not _get_store().remove_member(team_id, agent_id):
        raise HTTPException(
            status_code=404,
            detail=f"Member {agent_id} not found in team {team_id}",
        )
    return {"removed": True}
