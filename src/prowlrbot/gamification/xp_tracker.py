# -*- coding: utf-8 -*-
"""XP tracking, levels, achievements, and leaderboards — SQLite backed."""

from __future__ import annotations

import asyncio
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import (
    ACHIEVEMENTS,
    Achievement,
    LeaderboardEntry,
    LevelInfo,
    UnlockedAchievement,
    XPGain,
    level_from_xp,
)


async def _push_leaderboard_update(
    entity_id: str,
    entity_type: str,
    new_xp: int,
    category: str,
) -> None:
    """Broadcast a leaderboard_update event to all WebSocket clients. Best-effort."""
    try:
        from prowlrbot.dashboard.events import (
            DashboardEvent,
            EventType,
            get_global_event_bus,
        )

        bus = get_global_event_bus()
        if bus is None:
            return
        event = DashboardEvent(
            type=EventType.LEADERBOARD_UPDATE,
            session_id="*",  # sentinel — broadcast ignores session_id
            data={
                "entity_id": entity_id,
                "entity_type": entity_type,
                "new_xp": new_xp,
                "category": category,
            },
        )
        await bus.broadcast(event)
    except Exception:
        pass  # never let push failures affect XP recording


class XPTracker:
    """Track XP, levels, and achievements for users and agents."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS xp_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                category TEXT NOT NULL,
                reason TEXT NOT NULL,
                timestamp REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_xp_entity
            ON xp_log(entity_id, entity_type);

            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT NOT NULL,
                achievement_id TEXT NOT NULL,
                unlocked_at REAL NOT NULL,
                UNIQUE(entity_id, achievement_id)
            );
            CREATE INDEX IF NOT EXISTS idx_achievements_entity
            ON achievements(entity_id);

            CREATE TABLE IF NOT EXISTS challenge_progress (
                entity_id TEXT NOT NULL,
                challenge_id TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                period TEXT NOT NULL,
                PRIMARY KEY(entity_id, challenge_id, period)
            );
        """,
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # XP
    # ------------------------------------------------------------------

    def award_xp(
        self,
        entity_id: str,
        amount: int,
        category: str,
        reason: str,
        entity_type: str = "user",
    ) -> XPGain:
        """Award XP to a user or agent."""
        ts = time.time()
        self._conn.execute(
            "INSERT INTO xp_log (entity_id, entity_type, amount, category, reason, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (entity_id, entity_type, amount, category, reason, ts),
        )
        self._conn.commit()
        gain = XPGain(
            entity_id=entity_id,
            entity_type=entity_type,
            amount=amount,
            category=category,
            reason=reason,
            timestamp=ts,
        )
        # Fire-and-forget leaderboard push — only schedule if an async loop is running.
        # If called from sync context (no loop), skip silently; the push is best-effort.
        new_total = self.get_total_xp(entity_id, entity_type)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                _push_leaderboard_update(
                    entity_id,
                    entity_type,
                    new_total,
                    category,
                ),
            )
        except RuntimeError:
            # No running event loop — skip push (sync-only caller, e.g. tests/CLI)
            pass
        except Exception:
            pass  # never block XP recording due to push failure
        return gain

    def get_total_xp(self, entity_id: str, entity_type: str = "user") -> int:
        """Get total XP for an entity."""
        row = self._conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM xp_log "
            "WHERE entity_id = ? AND entity_type = ?",
            (entity_id, entity_type),
        ).fetchone()
        return int(row["total"]) if row else 0

    def get_level_info(
        self,
        entity_id: str,
        entity_type: str = "user",
    ) -> LevelInfo:
        """Get full level info for an entity."""
        total_xp = self.get_total_xp(entity_id, entity_type)
        level, title = level_from_xp(total_xp, entity_type)

        # Calculate XP to next level
        from .models import USER_LEVELS, AGENT_LEVELS

        levels = USER_LEVELS if entity_type == "user" else AGENT_LEVELS
        xp_to_next = 0
        for _, _, threshold in levels:
            if threshold > total_xp:
                xp_to_next = threshold - total_xp
                break

        return LevelInfo(
            entity_id=entity_id,
            entity_type=entity_type,
            total_xp=total_xp,
            level=level,
            title=title,
            xp_to_next=xp_to_next,
        )

    def get_xp_history(
        self,
        entity_id: str,
        entity_type: str = "user",
        limit: int = 50,
    ) -> List[XPGain]:
        """Get recent XP history for an entity."""
        rows = self._conn.execute(
            "SELECT * FROM xp_log WHERE entity_id = ? AND entity_type = ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (entity_id, entity_type, limit),
        ).fetchall()
        return [
            XPGain(
                entity_id=row["entity_id"],
                entity_type=row["entity_type"],
                amount=row["amount"],
                category=row["category"],
                reason=row["reason"],
                timestamp=row["timestamp"],
            )
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Leaderboards
    # ------------------------------------------------------------------

    def get_leaderboard(
        self,
        entity_type: str = "user",
        limit: int = 20,
    ) -> List[LeaderboardEntry]:
        """Get leaderboard sorted by total XP."""
        rows = self._conn.execute(
            "SELECT entity_id, entity_type, SUM(amount) AS total_xp "
            "FROM xp_log WHERE entity_type = ? "
            "GROUP BY entity_id ORDER BY total_xp DESC LIMIT ?",
            (entity_type, limit),
        ).fetchall()
        entries = []
        for i, row in enumerate(rows, 1):
            total = int(row["total_xp"])
            level, title = level_from_xp(total, entity_type)
            entries.append(
                LeaderboardEntry(
                    rank=i,
                    entity_id=row["entity_id"],
                    entity_type=row["entity_type"],
                    total_xp=total,
                    level=level,
                    title=title,
                ),
            )
        return entries

    # ------------------------------------------------------------------
    # Achievements
    # ------------------------------------------------------------------

    def unlock_achievement(
        self,
        entity_id: str,
        achievement_id: str,
    ) -> Optional[UnlockedAchievement]:
        """Unlock an achievement. Returns None if already unlocked."""
        # Check if already unlocked
        existing = self._conn.execute(
            "SELECT 1 FROM achievements WHERE entity_id = ? AND achievement_id = ?",
            (entity_id, achievement_id),
        ).fetchone()
        if existing:
            return None

        ts = time.time()
        self._conn.execute(
            "INSERT INTO achievements (entity_id, achievement_id, unlocked_at) VALUES (?, ?, ?)",
            (entity_id, achievement_id, ts),
        )
        self._conn.commit()

        # Award XP for the achievement
        ach = self.get_achievement_def(achievement_id)
        if ach and ach.xp_reward > 0:
            self.award_xp(
                entity_id,
                ach.xp_reward,
                "achievement",
                f"Unlocked: {ach.name}",
            )

        return UnlockedAchievement(
            achievement_id=achievement_id,
            entity_id=entity_id,
            unlocked_at=ts,
        )

    def get_unlocked(self, entity_id: str) -> List[UnlockedAchievement]:
        """Get all unlocked achievements for an entity."""
        rows = self._conn.execute(
            "SELECT * FROM achievements WHERE entity_id = ? ORDER BY unlocked_at DESC",
            (entity_id,),
        ).fetchall()
        return [
            UnlockedAchievement(
                achievement_id=row["achievement_id"],
                entity_id=row["entity_id"],
                unlocked_at=row["unlocked_at"],
            )
            for row in rows
        ]

    @staticmethod
    def get_achievement_def(achievement_id: str) -> Optional[Achievement]:
        """Get an achievement definition by ID."""
        for ach in ACHIEVEMENTS:
            if ach.id == achievement_id:
                return ach
        return None

    @staticmethod
    def list_achievements() -> List[Achievement]:
        """List all achievement definitions."""
        return [a for a in ACHIEVEMENTS if not a.hidden]

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cleanup(self, older_than_days: int = 365) -> int:
        """Delete XP log entries older than N days. Returns count deleted."""
        cutoff = time.time() - (older_than_days * 86400)
        cursor = self._conn.execute(
            "DELETE FROM xp_log WHERE timestamp < ?",
            (cutoff,),
        )
        self._conn.commit()
        return cursor.rowcount

    def close(self) -> None:
        self._conn.close()
