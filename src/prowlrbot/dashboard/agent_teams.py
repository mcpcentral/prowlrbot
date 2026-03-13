# -*- coding: utf-8 -*-
"""Agent teams orchestration — models and SQLite-backed store."""

import json
import sqlite3
import time
import uuid
from prowlrbot.compat import StrEnum
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


class TeamRole(StrEnum):
    """Role a member plays within a team."""

    DIRECTOR = "director"
    SPECIALIST = "specialist"
    OBSERVER = "observer"


class CoordinationMode(StrEnum):
    """How the team coordinates task execution."""

    ROUND_ROBIN = "round_robin"
    HIERARCHICAL = "hierarchical"
    CONSENSUS = "consensus"
    AUCTION = "auction"


class TeamMember(BaseModel):
    """A single agent's membership within a team."""

    agent_id: str = Field(description="ID of the agent")
    role: TeamRole = Field(default=TeamRole.SPECIALIST, description="Member role")
    personality: str = Field(
        default="", description="Personality overlay for this team context"
    )
    skills: List[str] = Field(
        default_factory=list, description="Skills this member contributes"
    )
    model_preference: str = Field(
        default="", description="Preferred model ID for this member"
    )


class AgentTeam(BaseModel):
    """An orchestrated team of agents."""

    id: str = Field(default="", description="Team ID (auto-generated if empty)")
    name: str = Field(description="Team display name")
    description: str = Field(default="", description="What this team does")
    members: List[TeamMember] = Field(default_factory=list, description="Team members")
    coordination: CoordinationMode = Field(
        default=CoordinationMode.HIERARCHICAL, description="Coordination strategy"
    )
    fallback_strategy: str = Field(
        default="escalate",
        description="What to do when the team fails: escalate, retry, degrade",
    )
    created_at: float = Field(default_factory=time.time, description="Unix timestamp")


class TeamStore:
    """SQLite-backed persistent storage for agent teams."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                coordination TEXT NOT NULL DEFAULT 'hierarchical',
                fallback_strategy TEXT NOT NULL DEFAULT 'escalate',
                created_at REAL NOT NULL
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS team_members (
                team_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'specialist',
                personality TEXT NOT NULL DEFAULT '',
                skills TEXT NOT NULL DEFAULT '[]',
                model_preference TEXT NOT NULL DEFAULT '',
                PRIMARY KEY (team_id, agent_id),
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            )
        """)
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.commit()

    def _row_to_team(self, row: sqlite3.Row, members: List[TeamMember]) -> AgentTeam:
        return AgentTeam(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            coordination=CoordinationMode(row["coordination"]),
            fallback_strategy=row["fallback_strategy"],
            created_at=row["created_at"],
            members=members,
        )

    def _fetch_members(self, team_id: str) -> List[TeamMember]:
        rows = self._conn.execute(
            "SELECT * FROM team_members WHERE team_id = ?", (team_id,)
        ).fetchall()
        return [
            TeamMember(
                agent_id=r["agent_id"],
                role=TeamRole(r["role"]),
                personality=r["personality"],
                skills=json.loads(r["skills"]),
                model_preference=r["model_preference"],
            )
            for r in rows
        ]

    def _upsert_members(self, team_id: str, members: List[TeamMember]):
        self._conn.execute("DELETE FROM team_members WHERE team_id = ?", (team_id,))
        for m in members:
            self._conn.execute(
                "INSERT INTO team_members (team_id, agent_id, role, personality, skills, model_preference) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    team_id,
                    m.agent_id,
                    str(m.role),
                    m.personality,
                    json.dumps(m.skills),
                    m.model_preference,
                ),
            )

    def create_team(self, team: AgentTeam) -> AgentTeam:
        """Create a new team. Generates an ID if not set."""
        if not team.id:
            team.id = str(uuid.uuid4())[:8]
        self._conn.execute(
            "INSERT INTO teams (id, name, description, coordination, fallback_strategy, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                team.id,
                team.name,
                team.description,
                str(team.coordination),
                team.fallback_strategy,
                team.created_at,
            ),
        )
        self._upsert_members(team.id, team.members)
        self._conn.commit()
        return team

    def get_team(self, team_id: str) -> Optional[AgentTeam]:
        """Get a team by ID, or None if not found."""
        row = self._conn.execute(
            "SELECT * FROM teams WHERE id = ?", (team_id,)
        ).fetchone()
        if not row:
            return None
        members = self._fetch_members(team_id)
        return self._row_to_team(row, members)

    def list_teams(self) -> List[AgentTeam]:
        """List all teams ordered by creation time."""
        rows = self._conn.execute(
            "SELECT * FROM teams ORDER BY created_at DESC"
        ).fetchall()
        return [self._row_to_team(r, self._fetch_members(r["id"])) for r in rows]

    def update_team(self, team_id: str, team: AgentTeam) -> bool:
        """Update an existing team. Returns False if not found."""
        existing = self._conn.execute(
            "SELECT id FROM teams WHERE id = ?", (team_id,)
        ).fetchone()
        if not existing:
            return False
        self._conn.execute(
            "UPDATE teams SET name = ?, description = ?, coordination = ?, fallback_strategy = ? WHERE id = ?",
            (
                team.name,
                team.description,
                str(team.coordination),
                team.fallback_strategy,
                team_id,
            ),
        )
        self._upsert_members(team_id, team.members)
        self._conn.commit()
        return True

    def delete_team(self, team_id: str) -> bool:
        """Delete a team. Returns False if not found."""
        existing = self._conn.execute(
            "SELECT id FROM teams WHERE id = ?", (team_id,)
        ).fetchone()
        if not existing:
            return False
        self._conn.execute("DELETE FROM team_members WHERE team_id = ?", (team_id,))
        self._conn.execute("DELETE FROM teams WHERE id = ?", (team_id,))
        self._conn.commit()
        return True

    def add_member(self, team_id: str, member: TeamMember) -> bool:
        """Add a member to a team. Returns False if team not found."""
        existing = self._conn.execute(
            "SELECT id FROM teams WHERE id = ?", (team_id,)
        ).fetchone()
        if not existing:
            return False
        self._conn.execute(
            "INSERT OR REPLACE INTO team_members (team_id, agent_id, role, personality, skills, model_preference) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                team_id,
                member.agent_id,
                str(member.role),
                member.personality,
                json.dumps(member.skills),
                member.model_preference,
            ),
        )
        self._conn.commit()
        return True

    def remove_member(self, team_id: str, agent_id: str) -> bool:
        """Remove a member from a team. Returns False if not found."""
        cursor = self._conn.execute(
            "DELETE FROM team_members WHERE team_id = ? AND agent_id = ?",
            (team_id, agent_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def close(self):
        self._conn.close()
