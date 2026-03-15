# -*- coding: utf-8 -*-
"""Session replay recorder and player."""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from prowlrbot.compat import StrEnum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EventType(StrEnum):
    USER_MESSAGE = "user_message"
    AGENT_RESPONSE = "agent_response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    THINKING = "thinking"
    ERROR = "error"
    STATE_CHANGE = "state_change"
    FILE_CHANGE = "file_change"


class ReplayEvent(BaseModel):
    """A single event in a session replay."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    event_type: EventType
    timestamp: float = 0.0
    offset_ms: int = 0  # milliseconds from session start
    content: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    agent_id: str = ""


class ReplaySession(BaseModel):
    """A recorded session for replay."""

    id: str = Field(default_factory=lambda: f"replay_{uuid.uuid4().hex[:8]}")
    session_id: str  # original session ID
    agent_id: str = ""
    title: str = ""
    duration_ms: int = 0
    event_count: int = 0
    created_at: float = 0.0


class ReplaySessionDetail(ReplaySession):
    """Session with all events."""

    events: List[ReplayEvent] = Field(default_factory=list)


class SessionRecorder:
    """Records and retrieves session replays."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
        self._active_sessions: Dict[
            str,
            float,
        ] = {}  # session_id -> start_time

    def _create_tables(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS replay_sessions (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                agent_id TEXT DEFAULT '',
                title TEXT DEFAULT '',
                duration_ms INTEGER DEFAULT 0,
                event_count INTEGER DEFAULT 0,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS replay_events (
                id TEXT PRIMARY KEY,
                replay_session_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                timestamp REAL NOT NULL,
                offset_ms INTEGER DEFAULT 0,
                content TEXT DEFAULT '',
                metadata TEXT DEFAULT '{}',
                agent_id TEXT DEFAULT '',
                FOREIGN KEY (replay_session_id) REFERENCES replay_sessions(id)
            );
            CREATE INDEX IF NOT EXISTS idx_replay_events_session
                ON replay_events(replay_session_id);
            CREATE INDEX IF NOT EXISTS idx_replay_sessions_session
                ON replay_sessions(session_id);
        """,
        )
        self._conn.commit()

    def start_recording(
        self,
        session_id: str,
        agent_id: str = "",
        title: str = "",
    ) -> ReplaySession:
        """Start recording a new session."""
        now = time.time()
        replay = ReplaySession(
            session_id=session_id,
            agent_id=agent_id,
            title=title or f"Session {session_id}",
            created_at=now,
        )
        self._conn.execute(
            "INSERT INTO replay_sessions "
            "(id, session_id, agent_id, title, duration_ms, event_count, created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                replay.id,
                replay.session_id,
                replay.agent_id,
                replay.title,
                0,
                0,
                replay.created_at,
            ),
        )
        self._conn.commit()
        self._active_sessions[replay.id] = now
        return replay

    def record_event(
        self,
        replay_session_id: str,
        event_type: EventType,
        content: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        agent_id: str = "",
    ) -> ReplayEvent:
        """Record an event in the session."""
        now = time.time()
        start = self._active_sessions.get(replay_session_id, now)
        offset_ms = int((now - start) * 1000)

        event = ReplayEvent(
            event_type=event_type,
            timestamp=now,
            offset_ms=offset_ms,
            content=content,
            metadata=metadata or {},
            agent_id=agent_id,
        )

        self._conn.execute(
            "INSERT INTO replay_events "
            "(id, replay_session_id, event_type, timestamp, offset_ms, "
            "content, metadata, agent_id) VALUES (?,?,?,?,?,?,?,?)",
            (
                event.id,
                replay_session_id,
                event.event_type,
                event.timestamp,
                event.offset_ms,
                event.content,
                json.dumps(event.metadata),
                event.agent_id,
            ),
        )
        self._conn.execute(
            "UPDATE replay_sessions SET event_count = event_count + 1, "
            "duration_ms = ? WHERE id = ?",
            (offset_ms, replay_session_id),
        )
        self._conn.commit()
        return event

    def stop_recording(
        self,
        replay_session_id: str,
    ) -> Optional[ReplaySession]:
        """Stop recording a session."""
        self._active_sessions.pop(replay_session_id, None)
        return self.get_session(replay_session_id)

    def get_session(self, replay_session_id: str) -> Optional[ReplaySession]:
        row = self._conn.execute(
            "SELECT * FROM replay_sessions WHERE id = ?",
            (replay_session_id,),
        ).fetchone()
        if not row:
            return None
        return ReplaySession(
            id=row["id"],
            session_id=row["session_id"],
            agent_id=row["agent_id"],
            title=row["title"],
            duration_ms=row["duration_ms"],
            event_count=row["event_count"],
            created_at=row["created_at"],
        )

    def get_session_detail(
        self,
        replay_session_id: str,
    ) -> Optional[ReplaySessionDetail]:
        """Get session with all events for playback."""
        session = self.get_session(replay_session_id)
        if not session:
            return None

        rows = self._conn.execute(
            "SELECT * FROM replay_events WHERE replay_session_id = ? "
            "ORDER BY offset_ms ASC",
            (replay_session_id,),
        ).fetchall()

        events = [
            ReplayEvent(
                id=r["id"],
                event_type=EventType(r["event_type"]),
                timestamp=r["timestamp"],
                offset_ms=r["offset_ms"],
                content=r["content"],
                metadata=json.loads(r["metadata"]) if r["metadata"] else {},
                agent_id=r["agent_id"],
            )
            for r in rows
        ]

        return ReplaySessionDetail(**session.model_dump(), events=events)

    def get_events_in_range(
        self,
        replay_session_id: str,
        start_ms: int = 0,
        end_ms: int = 0,
    ) -> List[ReplayEvent]:
        """Get events within a time range (for timeline scrubbing)."""
        query = (
            "SELECT * FROM replay_events WHERE replay_session_id = ? "
            "AND offset_ms >= ?"
        )
        params: list = [replay_session_id, start_ms]
        if end_ms > 0:
            query += " AND offset_ms <= ?"
            params.append(end_ms)
        query += " ORDER BY offset_ms ASC"

        rows = self._conn.execute(query, params).fetchall()
        return [
            ReplayEvent(
                id=r["id"],
                event_type=EventType(r["event_type"]),
                timestamp=r["timestamp"],
                offset_ms=r["offset_ms"],
                content=r["content"],
                metadata=json.loads(r["metadata"]) if r["metadata"] else {},
                agent_id=r["agent_id"],
            )
            for r in rows
        ]

    def list_sessions(self, limit: int = 50) -> List[ReplaySession]:
        rows = self._conn.execute(
            "SELECT * FROM replay_sessions ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            ReplaySession(
                id=r["id"],
                session_id=r["session_id"],
                agent_id=r["agent_id"],
                title=r["title"],
                duration_ms=r["duration_ms"],
                event_count=r["event_count"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def delete_session(self, replay_session_id: str) -> bool:
        self._conn.execute(
            "DELETE FROM replay_events WHERE replay_session_id = ?",
            (replay_session_id,),
        )
        cursor = self._conn.execute(
            "DELETE FROM replay_sessions WHERE id = ?",
            (replay_session_id,),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def close(self) -> None:
        self._conn.close()
