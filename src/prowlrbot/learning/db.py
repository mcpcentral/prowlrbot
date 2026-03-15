# -*- coding: utf-8 -*-
"""Learning Engine database — stores corrections, preferences, and patterns.

Uses SQLite with FTS5 for fast full-text search across learnings.
Each learning is tagged by category, source, and project for contextual retrieval.
Supports decay-weighted scoring so recent, high-confidence learnings surface first.

Module-level convenience functions (``init_db``, ``add_learning``,
``query_learnings``, ``search_learnings``) provide a functional API that
mirrors the class-based ``LearningDB`` for simpler scripting use-cases
(e.g. hook scripts that open/close a connection per invocation).
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Max items returned by any list query
_MAX_LIMIT = 200

# Decay half-life in days — a learning's relevance halves every 30 days
_DECAY_HALF_LIFE_DAYS = 30.0

# Default DB location
DEFAULT_DB_PATH = os.path.join(
    os.path.expanduser("~/.prowlrbot"),
    "learnings.db",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS learnings (
    learning_id TEXT PRIMARY KEY,
    project     TEXT NOT NULL DEFAULT '',
    category    TEXT NOT NULL,  -- correction, preference, pattern, insight, failure
    source      TEXT NOT NULL,  -- agent_id or 'user'
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,
    metadata    TEXT DEFAULT '{}',
    confidence  REAL DEFAULT 1.0,
    times_used  INTEGER DEFAULT 0,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_learnings_category ON learnings(category);
CREATE INDEX IF NOT EXISTS idx_learnings_source ON learnings(source);
CREATE INDEX IF NOT EXISTS idx_learnings_project ON learnings(project);

CREATE VIRTUAL TABLE IF NOT EXISTS learnings_fts USING fts5(
    title, content, category,
    content=learnings,
    content_rowid=rowid
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS learnings_ai AFTER INSERT ON learnings BEGIN
    INSERT INTO learnings_fts(rowid, title, content, category)
    VALUES (new.rowid, new.title, new.content, new.category);
END;

CREATE TRIGGER IF NOT EXISTS learnings_ad AFTER DELETE ON learnings BEGIN
    INSERT INTO learnings_fts(learnings_fts, rowid, title, content, category)
    VALUES ('delete', old.rowid, old.title, old.content, old.category);
END;

CREATE TRIGGER IF NOT EXISTS learnings_au AFTER UPDATE ON learnings BEGIN
    INSERT INTO learnings_fts(learnings_fts, rowid, title, content, category)
    VALUES ('delete', old.rowid, old.title, old.content, old.category);
    INSERT INTO learnings_fts(rowid, title, content, category)
    VALUES (new.rowid, new.title, new.content, new.category);
END;

CREATE TABLE IF NOT EXISTS preferences (
    pref_id     TEXT PRIMARY KEY,
    project     TEXT NOT NULL DEFAULT '',
    scope       TEXT NOT NULL DEFAULT 'global',  -- global, project, agent
    key         TEXT NOT NULL,
    value       TEXT NOT NULL,
    source      TEXT NOT NULL DEFAULT 'user',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    UNIQUE(project, scope, key)
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id  TEXT PRIMARY KEY,
    agent_id    TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    ended_at    TEXT,
    summary     TEXT DEFAULT '',
    learnings_captured INTEGER DEFAULT 0
);
"""

# Migration: add 'project' column to existing DBs that lack it.
_MIGRATIONS = [
    "ALTER TABLE learnings ADD COLUMN project TEXT NOT NULL DEFAULT ''",
]


def _sanitize_fts_query(query: str) -> str:
    """Escape FTS5 special characters and wrap as phrase query."""
    sanitized = re.sub(r'[*"(){}[\]^~:!\\]', " ", query)
    sanitized = sanitized.strip()
    if not sanitized:
        return '""'
    return '"' + sanitized.replace('"', "") + '"'


def _clamp_limit(limit: int) -> int:
    return max(1, min(limit, _MAX_LIMIT))


def _decay_score(
    created_iso: str,
    half_life_days: float = _DECAY_HALF_LIFE_DAYS,
) -> float:
    """Compute an exponential decay factor in [0, 1] based on age.

    Args:
        created_iso: ISO-8601 timestamp string.
        half_life_days: Number of days for the score to halve.

    Returns:
        Decay multiplier between 0.0 and 1.0.
    """
    try:
        created = datetime.fromisoformat(created_iso)
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(tz=timezone.utc) - created).total_seconds() / 86400.0
        return math.exp(-math.log(2) * age_days / half_life_days)
    except (ValueError, TypeError):
        return 0.5  # Fallback for unparseable timestamps


def _apply_migrations(conn: sqlite3.Connection) -> None:
    """Run idempotent schema migrations."""
    for sql in _MIGRATIONS:
        try:
            conn.execute(sql)
        except sqlite3.OperationalError:
            # Column already exists or migration already applied.
            pass
    conn.commit()


# -----------------------------------------------------------------------
# Class-based API
# -----------------------------------------------------------------------


class LearningDB:
    """SQLite-backed learning storage with FTS5 search.

    Thread-safe: all write operations are serialized via a lock.

    Args:
        db_path: Filesystem path for the SQLite database file.
            Defaults to ``~/.prowlrbot/learnings.db``.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            base = os.path.expanduser("~/.prowlrbot")
            os.makedirs(base, exist_ok=True)
            db_path = os.path.join(base, "learnings.db")

        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        _apply_migrations(self._conn)
        self._lock = threading.Lock()

    @property
    def connection(self) -> sqlite3.Connection:
        """Expose the underlying connection for advanced use."""
        return self._conn

    # ------------------------------------------------------------------
    # Learnings — write
    # ------------------------------------------------------------------

    def add_learning(
        self,
        category: str,
        source: str,
        title: str,
        content: str,
        *,
        project: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
    ) -> str:
        """Store a new learning. Returns the learning_id.

        Args:
            category: One of correction, preference, pattern, insight, failure.
            source: Agent id or 'user'.
            title: Short descriptive title.
            content: Full content of the learning.
            project: Project scope (empty string = global).
            metadata: Arbitrary JSON-serialisable metadata dict.
            confidence: Confidence score in [0, 1].

        Returns:
            The generated ``learning_id``.
        """
        learning_id = f"learn-{uuid.uuid4().hex[:12]}"
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._lock:
            self._conn.execute(
                """INSERT INTO learnings
                   (learning_id, project, category, source, title, content,
                    metadata, confidence, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    learning_id,
                    project,
                    category,
                    source,
                    title,
                    content,
                    json.dumps(metadata or {}),
                    confidence,
                    now,
                    now,
                ),
            )
            self._conn.commit()
        return learning_id

    # ------------------------------------------------------------------
    # Learnings — read / search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        *,
        category: Optional[str] = None,
        project: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Full-text search across learnings.

        Query is sanitized for FTS5 safety. Results ordered by FTS5 rank.

        Args:
            query: Search terms.
            category: Optional category filter.
            project: Optional project filter.
            limit: Max results.

        Returns:
            List of matching learning dicts.
        """
        safe_query = _sanitize_fts_query(query)
        limit = _clamp_limit(limit)

        conditions = ["learnings_fts MATCH ?"]
        params: list[Any] = [safe_query]

        if category:
            conditions.append("l.category = ?")
            params.append(category)
        if project is not None:
            conditions.append("l.project = ?")
            params.append(project)

        where = " AND ".join(conditions)
        params.append(limit)

        rows = self._conn.execute(
            f"""SELECT l.* FROM learnings l
               JOIN learnings_fts f ON l.rowid = f.rowid
               WHERE {where}
               ORDER BY rank LIMIT ?""",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def query_learnings(
        self,
        project: str = "",
        *,
        category: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Query learnings ranked by ``confidence * decay_score``.

        Args:
            project: Project scope (empty = global).
            category: Optional category filter.
            limit: Max results.

        Returns:
            List of learning dicts with an added ``relevance`` key,
            sorted by descending relevance.
        """
        limit = _clamp_limit(limit)

        conditions = ["project = ?"]
        params: list[Any] = [project]

        if category:
            conditions.append("category = ?")
            params.append(category)

        where = " AND ".join(conditions)

        # Fetch more than needed so decay scoring can rerank.
        fetch_limit = min(limit * 3, _MAX_LIMIT)
        params.append(fetch_limit)

        rows = self._conn.execute(
            f"SELECT * FROM learnings WHERE {where} ORDER BY updated_at DESC LIMIT ?",
            params,
        ).fetchall()

        scored = []
        for r in rows:
            d = dict(r)
            decay = _decay_score(d["created_at"])
            d["relevance"] = d["confidence"] * decay
            scored.append(d)

        scored.sort(key=lambda x: x["relevance"], reverse=True)
        return scored[:limit]

    def get_recent(
        self,
        limit: int = 20,
        *,
        category: Optional[str] = None,
        project: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get most recent learnings, optionally filtered by category and project.

        Args:
            limit: Max results.
            category: Optional category filter.
            project: Optional project filter.

        Returns:
            List of learning dicts, newest first.
        """
        limit = _clamp_limit(limit)

        conditions: list[str] = []
        params: list[Any] = []

        if category:
            conditions.append("category = ?")
            params.append(category)
        if project is not None:
            conditions.append("project = ?")
            params.append(project)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.append(limit)

        rows = self._conn.execute(
            f"SELECT * FROM learnings {where} ORDER BY updated_at DESC LIMIT ?",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def get_by_source(
        self,
        source: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get learnings from a specific agent or user."""
        limit = _clamp_limit(limit)
        rows = self._conn.execute(
            "SELECT * FROM learnings WHERE source = ? ORDER BY updated_at DESC LIMIT ?",
            (source, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get(self, learning_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single learning by id.

        Args:
            learning_id: The learning identifier.

        Returns:
            Learning dict, or ``None`` if not found.
        """
        row = self._conn.execute(
            "SELECT * FROM learnings WHERE learning_id = ?",
            (learning_id,),
        ).fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # Learnings — update / delete
    # ------------------------------------------------------------------

    def increment_usage(self, learning_id: str) -> None:
        """Track that a learning was used in context injection."""
        with self._lock:
            self._conn.execute(
                "UPDATE learnings SET times_used = times_used + 1, updated_at = ? WHERE learning_id = ?",
                (datetime.now(tz=timezone.utc).isoformat(), learning_id),
            )
            self._conn.commit()

    def update_confidence(self, learning_id: str, confidence: float) -> None:
        """Update the confidence score for a learning.

        Args:
            learning_id: The learning identifier.
            confidence: New confidence value in [0, 1].
        """
        confidence = max(0.0, min(1.0, confidence))
        with self._lock:
            self._conn.execute(
                "UPDATE learnings SET confidence = ?, updated_at = ? WHERE learning_id = ?",
                (
                    confidence,
                    datetime.now(tz=timezone.utc).isoformat(),
                    learning_id,
                ),
            )
            self._conn.commit()

    def delete_learning(self, learning_id: str) -> bool:
        """Remove a learning."""
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM learnings WHERE learning_id = ?",
                (learning_id,),
            )
            self._conn.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Preferences
    # ------------------------------------------------------------------

    def set_preference(
        self,
        key: str,
        value: str,
        *,
        project: str = "",
        scope: str = "global",
        source: str = "user",
    ) -> str:
        """Set or update a preference. Returns the pref_id.

        Args:
            key: Preference key (e.g. "formatter", "indent_style").
            value: Preference value.
            project: Project scope.
            scope: One of global, project, agent.
            source: Who set this preference.

        Returns:
            The preference id.
        """
        pref_id = f"pref-{uuid.uuid4().hex[:12]}"
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._lock:
            self._conn.execute(
                """INSERT INTO preferences
                   (pref_id, project, scope, key, value, source, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(project, scope, key) DO UPDATE SET
                       value = excluded.value,
                       source = excluded.source,
                       updated_at = excluded.updated_at""",
                (pref_id, project, scope, key, value, source, now, now),
            )
            self._conn.commit()
        return pref_id

    def get_preference(
        self,
        key: str,
        *,
        project: str = "",
        scope: str = "global",
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a single preference.

        Args:
            key: Preference key.
            project: Project scope.
            scope: Scope level.

        Returns:
            Preference dict, or ``None`` if not found.
        """
        row = self._conn.execute(
            "SELECT * FROM preferences WHERE key = ? AND project = ? AND scope = ?",
            (key, project, scope),
        ).fetchone()
        return dict(row) if row else None

    def list_preferences(
        self,
        *,
        project: str = "",
        scope: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List preferences, optionally filtered by scope.

        Args:
            project: Project scope.
            scope: Optional scope filter.

        Returns:
            List of preference dicts.
        """
        if scope:
            rows = self._conn.execute(
                "SELECT * FROM preferences WHERE project = ? AND scope = ? ORDER BY key",
                (project, scope),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM preferences WHERE project = ? ORDER BY key",
                (project,),
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_preference(
        self,
        key: str,
        *,
        project: str = "",
        scope: str = "global",
    ) -> bool:
        """Delete a preference."""
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM preferences WHERE key = ? AND project = ? AND scope = ?",
                (key, project, scope),
            )
            self._conn.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def start_session(self, agent_id: str) -> str:
        """Record the start of an agent session."""
        session_id = str(uuid.uuid4())
        with self._lock:
            self._conn.execute(
                "INSERT INTO sessions (session_id, agent_id, started_at) VALUES (?, ?, ?)",
                (
                    session_id,
                    agent_id,
                    datetime.now(tz=timezone.utc).isoformat(),
                ),
            )
            self._conn.commit()
        return session_id

    def end_session(
        self,
        session_id: str,
        summary: str = "",
        learnings_captured: int = 0,
    ) -> None:
        """Record session end with summary."""
        with self._lock:
            self._conn.execute(
                "UPDATE sessions SET ended_at = ?, summary = ?, learnings_captured = ? WHERE session_id = ?",
                (
                    datetime.now(tz=timezone.utc).isoformat(),
                    summary,
                    learnings_captured,
                    session_id,
                ),
            )
            self._conn.commit()

    # ------------------------------------------------------------------
    # Statistics / summary
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        """Return learning engine statistics."""
        total = self._conn.execute(
            "SELECT COUNT(*) FROM learnings",
        ).fetchone()[0]
        by_cat = self._conn.execute(
            "SELECT category, COUNT(*) as cnt FROM learnings GROUP BY category",
        ).fetchall()
        by_project = self._conn.execute(
            "SELECT project, COUNT(*) as cnt FROM learnings WHERE project != '' GROUP BY project",
        ).fetchall()
        sessions = self._conn.execute(
            "SELECT COUNT(*) FROM sessions",
        ).fetchone()[0]
        prefs = self._conn.execute(
            "SELECT COUNT(*) FROM preferences",
        ).fetchone()[0]
        return {
            "total_learnings": total,
            "by_category": {r["category"]: r["cnt"] for r in by_cat},
            "by_project": {r["project"]: r["cnt"] for r in by_project},
            "total_sessions": sessions,
            "total_preferences": prefs,
        }

    def summary(self, project: str = "", limit: int = 10) -> str:
        """Return a human-readable summary of top learnings for a project.

        Args:
            project: Project scope.
            limit: Max learnings to include.

        Returns:
            Formatted string summary.
        """
        learnings = self.query_learnings(project, limit=limit)
        if not learnings:
            return "No learnings recorded yet."

        lines = [
            f"Top {len(learnings)} learnings (project={project or 'global'}):",
        ]
        for i, l in enumerate(learnings, 1):
            lines.append(
                f"  {i}. [{l['category']}] {l['title']} "
                f"(confidence={l['confidence']:.2f}, relevance={l['relevance']:.3f})",
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying database connection."""
        self._conn.close()


# -----------------------------------------------------------------------
# Module-level convenience functions (functional API)
# -----------------------------------------------------------------------


def init_db(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Initialize the learning database and return a raw connection.

    This is the functional counterpart to ``LearningDB.__init__``. Useful for
    scripts that want a plain ``sqlite3.Connection`` instead of the full class.

    Args:
        db_path: Path to the SQLite file. Defaults to ``~/.prowlrbot/learnings.db``.

    Returns:
        A configured ``sqlite3.Connection`` with schema applied.
    """
    path = db_path or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)

    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_SCHEMA)
    conn.commit()
    _apply_migrations(conn)
    logger.info("Learning DB initialized at %s", path)
    return conn


def add_learning(
    conn: sqlite3.Connection,
    project: str,
    category: str,
    content: str,
    *,
    title: str = "",
    source: str = "hook",
    metadata: Optional[Dict[str, Any]] = None,
    confidence: float = 1.0,
) -> str:
    """Insert a learning via a raw connection. Returns the learning_id.

    Args:
        conn: SQLite connection from ``init_db``.
        project: Project name / scope.
        category: Learning category (correction, failure, pattern, etc.).
        content: Full content of the learning.
        title: Short title (defaults to first 80 chars of content).
        source: Source identifier.
        metadata: Optional JSON metadata dict.
        confidence: Confidence score in [0, 1].

    Returns:
        The generated ``learning_id`` (``learn-...``).
    """
    learning_id = f"learn-{uuid.uuid4().hex[:12]}"
    now = datetime.now(tz=timezone.utc).isoformat()
    if not title:
        title = content[:80].replace("\n", " ").strip()
    conn.execute(
        """INSERT INTO learnings
           (learning_id, project, category, source, title, content,
            metadata, confidence, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            learning_id,
            project,
            category,
            source,
            title,
            content,
            json.dumps(metadata or {}),
            confidence,
            now,
            now,
        ),
    )
    conn.commit()
    return learning_id


def query_learnings(
    conn: sqlite3.Connection,
    project: str = "",
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Query learnings ranked by ``confidence * decay_score``.

    Args:
        conn: SQLite connection from ``init_db``.
        project: Project scope.
        limit: Max results.

    Returns:
        List of learning dicts with ``relevance`` key added.
    """
    limit = _clamp_limit(limit)
    fetch_limit = min(limit * 3, _MAX_LIMIT)

    rows = conn.execute(
        "SELECT * FROM learnings WHERE project = ? ORDER BY updated_at DESC LIMIT ?",
        (project, fetch_limit),
    ).fetchall()

    scored = []
    for r in rows:
        d = dict(r)
        decay = _decay_score(d["created_at"])
        d["relevance"] = d["confidence"] * decay
        scored.append(d)

    scored.sort(key=lambda x: x["relevance"], reverse=True)
    return scored[:limit]


def search_learnings(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """FTS5 search across all learnings.

    Args:
        conn: SQLite connection from ``init_db``.
        query: Search terms (sanitized internally).
        limit: Max results.

    Returns:
        List of matching learning dicts.
    """
    safe_query = _sanitize_fts_query(query)
    limit = _clamp_limit(limit)

    rows = conn.execute(
        """SELECT l.* FROM learnings l
           JOIN learnings_fts f ON l.rowid = f.rowid
           WHERE learnings_fts MATCH ?
           ORDER BY rank LIMIT ?""",
        (safe_query, limit),
    ).fetchall()
    return [dict(r) for r in rows]
