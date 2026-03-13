# -*- coding: utf-8 -*-
"""AgentVerse world state — manages agent presence, zones, and interactions."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import (
    AgentAvatar,
    AgentPresence,
    ArenaBattle,
    BattleStatus,
    Guild,
    TradeOffer,
    TradeStatus,
    Zone,
    ZoneInfo,
    ZONE_REGISTRY,
)


class AgentVerseWorld:
    """Central world state for AgentVerse — SQLite backed."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                display_name TEXT DEFAULT '',
                avatar TEXT DEFAULT '{}',
                current_zone TEXT DEFAULT 'town_square',
                current_task TEXT DEFAULT '',
                online INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0,
                guild_id TEXT,
                friends TEXT DEFAULT '[]',
                last_seen REAL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS guilds (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                leader_id TEXT DEFAULT '',
                members TEXT DEFAULT '[]',
                combined_xp INTEGER DEFAULT 0,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                from_agent TEXT NOT NULL,
                to_agent TEXT NOT NULL,
                offering TEXT DEFAULT '{}',
                requesting TEXT DEFAULT '{}',
                status TEXT DEFAULT 'pending',
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS battles (
                id TEXT PRIMARY KEY,
                challenger_id TEXT NOT NULL,
                defender_id TEXT NOT NULL,
                benchmark TEXT DEFAULT 'general',
                status TEXT DEFAULT 'waiting',
                challenger_score REAL DEFAULT 0,
                defender_score REAL DEFAULT 0,
                winner_id TEXT DEFAULT '',
                created_at REAL NOT NULL
            );
        """)
        self._conn.commit()

    # ------------------------------------------------------------------
    # Agent Presence
    # ------------------------------------------------------------------

    def register_agent(self, presence: AgentPresence) -> AgentPresence:
        """Register or update an agent in AgentVerse."""
        self._conn.execute(
            "INSERT OR REPLACE INTO agents (agent_id, display_name, avatar, current_zone, "
            "current_task, online, xp, guild_id, friends, last_seen) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                presence.agent_id,
                presence.display_name,
                presence.avatar.model_dump_json(),
                presence.current_zone,
                presence.current_task,
                1 if presence.online else 0,
                presence.xp,
                presence.guild_id,
                json.dumps(presence.friends),
                time.time(),
            ),
        )
        self._conn.commit()
        return presence

    def get_agent(self, agent_id: str) -> Optional[AgentPresence]:
        row = self._conn.execute(
            "SELECT * FROM agents WHERE agent_id = ?", (agent_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_presence(row)

    def list_agents_in_zone(self, zone: Zone) -> List[AgentPresence]:
        rows = self._conn.execute(
            "SELECT * FROM agents WHERE current_zone = ? AND online = 1", (zone,)
        ).fetchall()
        return [self._row_to_presence(r) for r in rows]

    def list_online_agents(self) -> List[AgentPresence]:
        rows = self._conn.execute("SELECT * FROM agents WHERE online = 1").fetchall()
        return [self._row_to_presence(r) for r in rows]

    def move_agent(self, agent_id: str, zone: Zone) -> bool:
        cursor = self._conn.execute(
            "UPDATE agents SET current_zone = ?, last_seen = ? WHERE agent_id = ?",
            (zone, time.time(), agent_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def set_online(self, agent_id: str, online: bool) -> bool:
        cursor = self._conn.execute(
            "UPDATE agents SET online = ?, last_seen = ? WHERE agent_id = ?",
            (1 if online else 0, time.time(), agent_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def add_friend(self, agent_id: str, friend_id: str) -> bool:
        agent = self.get_agent(agent_id)
        if not agent or friend_id in agent.friends:
            return False
        agent.friends.append(friend_id)
        self._conn.execute(
            "UPDATE agents SET friends = ? WHERE agent_id = ?",
            (json.dumps(agent.friends), agent_id),
        )
        self._conn.commit()
        return True

    # ------------------------------------------------------------------
    # Zones
    # ------------------------------------------------------------------

    def get_zone_info(self) -> List[ZoneInfo]:
        """Get all zones with current agent counts."""
        zones = []
        for z in ZONE_REGISTRY:
            count = self._conn.execute(
                "SELECT COUNT(*) as c FROM agents WHERE current_zone = ? AND online = 1",
                (z.zone,),
            ).fetchone()
            zones.append(
                ZoneInfo(
                    zone=z.zone,
                    name=z.name,
                    description=z.description,
                    agents_online=count["c"] if count else 0,
                    is_premium=z.is_premium,
                )
            )
        return zones

    # ------------------------------------------------------------------
    # Guilds
    # ------------------------------------------------------------------

    def create_guild(self, guild: Guild) -> Guild:
        guild.created_at = time.time()
        self._conn.execute(
            "INSERT INTO guilds (id, name, description, leader_id, members, combined_xp, created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                guild.id,
                guild.name,
                guild.description,
                guild.leader_id,
                json.dumps(guild.members),
                guild.combined_xp,
                guild.created_at,
            ),
        )
        self._conn.commit()
        return guild

    def list_guilds(self) -> List[Guild]:
        rows = self._conn.execute(
            "SELECT * FROM guilds ORDER BY combined_xp DESC"
        ).fetchall()
        return [
            Guild(
                id=r["id"],
                name=r["name"],
                description=r["description"],
                leader_id=r["leader_id"],
                members=json.loads(r["members"]),
                combined_xp=r["combined_xp"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Trades
    # ------------------------------------------------------------------

    def create_trade(self, trade: TradeOffer) -> TradeOffer:
        trade.created_at = time.time()
        self._conn.execute(
            "INSERT INTO trades (id, from_agent, to_agent, offering, requesting, status, created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                trade.id,
                trade.from_agent,
                trade.to_agent,
                json.dumps(trade.offering),
                json.dumps(trade.requesting),
                trade.status,
                trade.created_at,
            ),
        )
        self._conn.commit()
        return trade

    def respond_trade(self, trade_id: str, accept: bool) -> bool:
        status = TradeStatus.ACCEPTED if accept else TradeStatus.REJECTED
        cursor = self._conn.execute(
            "UPDATE trades SET status = ? WHERE id = ? AND status = 'pending'",
            (status, trade_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def list_trades(self, agent_id: str) -> List[TradeOffer]:
        rows = self._conn.execute(
            "SELECT * FROM trades WHERE from_agent = ? OR to_agent = ? ORDER BY created_at DESC",
            (agent_id, agent_id),
        ).fetchall()
        return [
            TradeOffer(
                id=r["id"],
                from_agent=r["from_agent"],
                to_agent=r["to_agent"],
                offering=json.loads(r["offering"]),
                requesting=json.loads(r["requesting"]),
                status=TradeStatus(r["status"]),
                created_at=r["created_at"],
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Battles
    # ------------------------------------------------------------------

    def create_battle(self, battle: ArenaBattle) -> ArenaBattle:
        battle.created_at = time.time()
        self._conn.execute(
            "INSERT INTO battles (id, challenger_id, defender_id, benchmark, status, "
            "challenger_score, defender_score, winner_id, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (
                battle.id,
                battle.challenger_id,
                battle.defender_id,
                battle.benchmark,
                battle.status,
                battle.challenger_score,
                battle.defender_score,
                battle.winner_id,
                battle.created_at,
            ),
        )
        self._conn.commit()
        return battle

    def complete_battle(
        self, battle_id: str, challenger_score: float, defender_score: float
    ) -> Optional[ArenaBattle]:
        winner = ""
        row = self._conn.execute(
            "SELECT * FROM battles WHERE id = ?", (battle_id,)
        ).fetchone()
        if not row:
            return None
        if challenger_score > defender_score:
            winner = row["challenger_id"]
        elif defender_score > challenger_score:
            winner = row["defender_id"]
        self._conn.execute(
            "UPDATE battles SET status = ?, challenger_score = ?, defender_score = ?, winner_id = ? WHERE id = ?",
            (
                BattleStatus.COMPLETED,
                challenger_score,
                defender_score,
                winner,
                battle_id,
            ),
        )
        self._conn.commit()
        return ArenaBattle(
            id=battle_id,
            challenger_id=row["challenger_id"],
            defender_id=row["defender_id"],
            benchmark=row["benchmark"],
            status=BattleStatus.COMPLETED,
            challenger_score=challenger_score,
            defender_score=defender_score,
            winner_id=winner,
            created_at=row["created_at"],
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_presence(row: sqlite3.Row) -> AgentPresence:
        avatar_data = json.loads(row["avatar"]) if row["avatar"] else {}
        return AgentPresence(
            agent_id=row["agent_id"],
            display_name=row["display_name"],
            avatar=AgentAvatar(**avatar_data) if avatar_data else AgentAvatar(),
            current_zone=Zone(row["current_zone"]),
            current_task=row["current_task"],
            online=bool(row["online"]),
            xp=row["xp"],
            guild_id=row["guild_id"],
            friends=json.loads(row["friends"]) if row["friends"] else [],
        )

    def close(self) -> None:
        self._conn.close()
