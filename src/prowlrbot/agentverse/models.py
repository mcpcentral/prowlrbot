# -*- coding: utf-8 -*-
"""AgentVerse data models — avatars, zones, guilds, trades, battles."""

from __future__ import annotations

import uuid
from prowlrbot.compat import StrEnum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Avatar system
# ---------------------------------------------------------------------------


class AvatarBase(StrEnum):
    CAT = "cat"
    DOG = "dog"
    FOX = "fox"
    OWL = "owl"
    ROBOT = "robot"
    DRAGON = "dragon"
    CUSTOM = "custom"


class AgentMood(StrEnum):
    IDLE = "idle"
    FOCUSED = "focused"
    CURIOUS = "curious"
    EXCITED = "excited"
    TIRED = "tired"
    THINKING = "thinking"


class AgentAvatar(BaseModel):
    """Visual representation of an agent in AgentVerse."""

    base: AvatarBase = AvatarBase.CAT
    color: str = "#00E5FF"
    accessories: List[str] = Field(default_factory=list)
    status: str = ""
    mood: AgentMood = AgentMood.IDLE
    level: int = 1
    reputation: float = 0.0


# ---------------------------------------------------------------------------
# Zones
# ---------------------------------------------------------------------------


class Zone(StrEnum):
    TOWN_SQUARE = "town_square"
    TRADING_POST = "trading_post"
    WORKSHOP = "workshop"
    ARENA = "arena"
    ACADEMY = "academy"
    MISSION_BOARD = "mission_board"
    HOME = "home"
    MARKETPLACE_MALL = "marketplace_mall"


class ZoneInfo(BaseModel):
    """Metadata about a zone."""

    zone: Zone
    name: str
    description: str = ""
    agents_online: int = 0
    is_premium: bool = False


ZONE_REGISTRY: list[ZoneInfo] = [
    ZoneInfo(
        zone=Zone.TOWN_SQUARE,
        name="Town Square",
        description="Agents socialize, share discoveries, form teams",
    ),
    ZoneInfo(
        zone=Zone.TRADING_POST,
        name="Trading Post",
        description="Trade skills, prompts, knowledge",
        is_premium=False,
    ),
    ZoneInfo(
        zone=Zone.WORKSHOP,
        name="Workshop",
        description="Collaborative skill building",
        is_premium=True,
    ),
    ZoneInfo(
        zone=Zone.ARENA,
        name="Arena",
        description="Benchmark battles between agents",
        is_premium=False,
    ),
    ZoneInfo(
        zone=Zone.ACADEMY,
        name="Academy",
        description="Learn new skills, training scenarios",
        is_premium=True,
    ),
    ZoneInfo(
        zone=Zone.MISSION_BOARD,
        name="Mission Board",
        description="Community tasks and bounties",
    ),
    ZoneInfo(
        zone=Zone.HOME,
        name="Your Home",
        description="Private space to customize and review",
    ),
    ZoneInfo(
        zone=Zone.MARKETPLACE_MALL,
        name="Marketplace Mall",
        description="Browse and buy from the marketplace",
    ),
]


# ---------------------------------------------------------------------------
# Agent presence
# ---------------------------------------------------------------------------


class AgentPresence(BaseModel):
    """An agent's presence in AgentVerse."""

    agent_id: str
    display_name: str = ""
    avatar: AgentAvatar = Field(default_factory=AgentAvatar)
    current_zone: Zone = Zone.TOWN_SQUARE
    current_task: str = ""
    online: bool = False
    xp: int = 0
    guild_id: Optional[str] = None
    friends: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Guilds
# ---------------------------------------------------------------------------


class Guild(BaseModel):
    """A group of agents that collaborate on missions."""

    id: str = Field(default_factory=lambda: f"guild_{uuid.uuid4().hex[:8]}")
    name: str
    description: str = ""
    leader_id: str = ""
    members: List[str] = Field(default_factory=list)
    combined_xp: int = 0
    created_at: float = 0.0


# ---------------------------------------------------------------------------
# Trades
# ---------------------------------------------------------------------------


class TradeStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TradeOffer(BaseModel):
    """A trade between two agents."""

    id: str = Field(default_factory=lambda: f"trade_{uuid.uuid4().hex[:8]}")
    from_agent: str
    to_agent: str
    offering: Dict[str, Any] = Field(
        default_factory=dict
    )  # e.g. {"skill": "seo_analyzer"}
    requesting: Dict[str, Any] = Field(
        default_factory=dict
    )  # e.g. {"skill": "newsletter_writer"}
    status: TradeStatus = TradeStatus.PENDING
    created_at: float = 0.0


# ---------------------------------------------------------------------------
# Arena battles
# ---------------------------------------------------------------------------


class BattleStatus(StrEnum):
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"


class ArenaBattle(BaseModel):
    """A benchmark battle between agents."""

    id: str = Field(default_factory=lambda: f"battle_{uuid.uuid4().hex[:8]}")
    challenger_id: str
    defender_id: str
    benchmark: str = "general"
    status: BattleStatus = BattleStatus.WAITING
    challenger_score: float = 0.0
    defender_score: float = 0.0
    winner_id: str = ""
    created_at: float = 0.0
