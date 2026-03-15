# -*- coding: utf-8 -*-
"""SQLite-backed activity log for dashboard events."""

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from prowlrbot.dashboard.events import EventType


class ActivityLog:
    """Persistent activity log using SQLite."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT NOT NULL DEFAULT '{}',
                timestamp REAL NOT NULL
            )
        """,
        )
        self._conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_activity_session
            ON activity_log(session_id, timestamp DESC)
        """,
        )
        self._conn.commit()

    def record(
        self,
        session_id: str,
        event_type: EventType,
        data: Dict[str, Any],
    ) -> int:
        """Record an activity event. Returns the event ID."""
        cursor = self._conn.execute(
            "INSERT INTO activity_log (session_id, event_type, event_data, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, str(event_type), json.dumps(data), time.time()),
        )
        self._conn.commit()
        return cursor.lastrowid

    def query(
        self,
        session_id: str,
        event_type: Optional[EventType] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query events for a session."""
        sql = "SELECT * FROM activity_log WHERE session_id = ?"
        params: list = [session_id]

        if event_type:
            sql += " AND event_type = ?"
            params.append(str(event_type))

        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        rows = self._conn.execute(sql, params).fetchall()
        return [
            {
                "id": row["id"],
                "session_id": row["session_id"],
                "event_type": row["event_type"],
                "data": json.loads(row["event_data"]),
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]

    def cleanup(self, max_age_days: int = 30) -> int:
        """Delete events older than max_age_days. Returns count deleted."""
        cutoff = time.time() - (max_age_days * 86400)
        cursor = self._conn.execute(
            "DELETE FROM activity_log WHERE timestamp < ?",
            (cutoff,),
        )
        self._conn.commit()
        return cursor.rowcount

    def close(self):
        self._conn.close()
