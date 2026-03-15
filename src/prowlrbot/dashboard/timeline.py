# -*- coding: utf-8 -*-
"""Timeline and checkpoints system for session state branching and replay."""

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Checkpoint(BaseModel):
    """A snapshot of session state at a point in time."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    session_id: str
    label: str
    state_snapshot: Dict[str, Any] = Field(default_factory=dict)
    parent_id: Optional[str] = None
    created_at: float = Field(default_factory=time.time)


class TimelineEntry(BaseModel):
    """A single event in the session timeline."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    session_id: str
    event_type: str
    event_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class TimelineManager:
    """SQLite-backed manager for session checkpoints and timeline entries."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS checkpoints (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                label TEXT NOT NULL,
                state_snapshot TEXT NOT NULL DEFAULT '{}',
                parent_id TEXT,
                created_at REAL NOT NULL
            )
        """,
        )
        self._conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_checkpoints_session
            ON checkpoints(session_id, created_at DESC)
        """,
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS timeline_entries (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT NOT NULL DEFAULT '{}',
                timestamp REAL NOT NULL
            )
        """,
        )
        self._conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_timeline_session
            ON timeline_entries(session_id, timestamp DESC)
        """,
        )
        self._conn.commit()

    def create_checkpoint(
        self,
        session_id: str,
        label: str,
        state_snapshot: Dict[str, Any],
        parent_id: Optional[str] = None,
    ) -> Checkpoint:
        """Create a new checkpoint for a session."""
        cp = Checkpoint(
            session_id=session_id,
            label=label,
            state_snapshot=state_snapshot,
            parent_id=parent_id,
        )
        self._conn.execute(
            "INSERT INTO checkpoints (id, session_id, label, state_snapshot, parent_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                cp.id,
                cp.session_id,
                cp.label,
                json.dumps(cp.state_snapshot),
                cp.parent_id,
                cp.created_at,
            ),
        )
        self._conn.commit()
        return cp

    def list_checkpoints(self, session_id: str) -> List[Checkpoint]:
        """List all checkpoints for a session, newest first."""
        rows = self._conn.execute(
            "SELECT * FROM checkpoints WHERE session_id = ? ORDER BY created_at DESC",
            (session_id,),
        ).fetchall()
        return [self._row_to_checkpoint(row) for row in rows]

    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Get a single checkpoint by ID."""
        row = self._conn.execute(
            "SELECT * FROM checkpoints WHERE id = ?",
            (checkpoint_id,),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_checkpoint(row)

    def fork_from_checkpoint(
        self,
        checkpoint_id: str,
        new_label: str,
    ) -> Optional[Checkpoint]:
        """Create a new checkpoint branching from an existing one.

        The new checkpoint copies the state snapshot of the parent and sets
        ``parent_id`` so the branch lineage is preserved.
        """
        parent = self.get_checkpoint(checkpoint_id)
        if parent is None:
            return None
        return self.create_checkpoint(
            session_id=parent.session_id,
            label=new_label,
            state_snapshot=parent.state_snapshot,
            parent_id=parent.id,
        )

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint. Returns True if a row was actually removed."""
        cursor = self._conn.execute(
            "DELETE FROM checkpoints WHERE id = ?",
            (checkpoint_id,),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def record_event(
        self,
        session_id: str,
        event_type: str,
        event_data: Dict[str, Any],
    ) -> TimelineEntry:
        """Record a timeline event for a session."""
        entry = TimelineEntry(
            session_id=session_id,
            event_type=event_type,
            event_data=event_data,
        )
        self._conn.execute(
            "INSERT INTO timeline_entries (id, session_id, event_type, event_data, timestamp) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                entry.id,
                entry.session_id,
                entry.event_type,
                json.dumps(entry.event_data),
                entry.timestamp,
            ),
        )
        self._conn.commit()
        return entry

    def list_events(
        self,
        session_id: str,
        limit: int = 200,
    ) -> List[TimelineEntry]:
        """List timeline events for a session, newest first."""
        rows = self._conn.execute(
            "SELECT * FROM timeline_entries WHERE session_id = ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return [self._row_to_entry(row) for row in rows]

    def export_timeline(self, session_id: str) -> Dict[str, Any]:
        """Export the full timeline (checkpoints + events) as a JSON-serializable dict."""
        checkpoints = self.list_checkpoints(session_id)
        events = self.list_events(session_id, limit=10000)
        return {
            "session_id": session_id,
            "checkpoints": [cp.model_dump(mode="json") for cp in checkpoints],
            "events": [ev.model_dump(mode="json") for ev in events],
            "exported_at": time.time(),
        }

    def close(self):
        self._conn.close()

    # -- internal helpers --

    @staticmethod
    def _row_to_checkpoint(row: sqlite3.Row) -> Checkpoint:
        return Checkpoint(
            id=row["id"],
            session_id=row["session_id"],
            label=row["label"],
            state_snapshot=json.loads(row["state_snapshot"]),
            parent_id=row["parent_id"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> TimelineEntry:
        return TimelineEntry(
            id=row["id"],
            session_id=row["session_id"],
            event_type=row["event_type"],
            event_data=json.loads(row["event_data"]),
            timestamp=row["timestamp"],
        )
