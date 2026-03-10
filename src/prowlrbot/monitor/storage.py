# -*- coding: utf-8 -*-
"""SQLite-backed state storage for monitor snapshots."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dataclasses import dataclass


@dataclass
class MonitorSnapshot:
    """A stored snapshot of monitor content."""

    monitor_name: str
    content: str
    checked_at: str  # ISO-8601


class MonitorStorage:
    """Persists last-seen content per monitor in SQLite."""

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        if db_path is None:
            from prowlrbot.constant import WORKING_DIR

            db_path = WORKING_DIR / "monitors.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._init_db()

    def _init_db(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS monitor_state (
                monitor_name TEXT PRIMARY KEY,
                content      TEXT NOT NULL,
                checked_at   TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def save(self, monitor_name: str, content: str) -> None:
        """Save (upsert) the latest content for a monitor."""
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """
            INSERT INTO monitor_state (monitor_name, content, checked_at)
            VALUES (?, ?, ?)
            ON CONFLICT(monitor_name) DO UPDATE SET
                content = excluded.content,
                checked_at = excluded.checked_at
            """,
            (monitor_name, content, now),
        )
        self._conn.commit()

    def load(self, monitor_name: str) -> Optional[MonitorSnapshot]:
        """Load the last snapshot for a monitor, or None if never seen."""
        row = self._conn.execute(
            "SELECT monitor_name, content, checked_at FROM monitor_state WHERE monitor_name = ?",
            (monitor_name,),
        ).fetchone()
        if row is None:
            return None
        return MonitorSnapshot(monitor_name=row[0], content=row[1], checked_at=row[2])

    def delete(self, monitor_name: str) -> bool:
        """Delete a monitor's stored state. Returns True if a row was deleted."""
        cur = self._conn.execute(
            "DELETE FROM monitor_state WHERE monitor_name = ?",
            (monitor_name,),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def list_monitors(self) -> list[str]:
        """Return names of all monitors with stored state."""
        rows = self._conn.execute(
            "SELECT monitor_name FROM monitor_state ORDER BY monitor_name"
        ).fetchall()
        return [r[0] for r in rows]

    def close(self) -> None:
        self._conn.close()
