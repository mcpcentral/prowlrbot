# -*- coding: utf-8 -*-
"""Long-term agent memory archive -- SQLite + FTS5 for permanent knowledge.

This module provides the persistent bottom tier of ProwlrBot's memory system.
Entries promoted from medium-term (learning) memory land here and are indexed
with FTS5 for fast full-text retrieval.  Each entry is scoped to a single
agent via ``agent_id`` and tracks access patterns for future relevance scoring.
"""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional


class ArchiveDB:
    """Persistent long-term memory archive with full-text search.

    Args:
        db_path: Filesystem path for the SQLite database file.
    """

    def __init__(self, db_path: str) -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _create_tables(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS archive (
                id            TEXT PRIMARY KEY,
                agent_id      TEXT NOT NULL,
                topic         TEXT NOT NULL,
                summary       TEXT NOT NULL,
                importance    INTEGER DEFAULT 1,
                access_count  INTEGER DEFAULT 0,
                promoted_from TEXT DEFAULT '',
                created_at    TEXT NOT NULL,
                last_accessed TEXT NOT NULL
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS archive_fts USING fts5(
                topic, summary, content=archive, content_rowid=rowid
            );

            CREATE INDEX IF NOT EXISTS idx_archive_agent
                ON archive(agent_id);
        """
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def store(
        self,
        agent_id: str,
        topic: str,
        summary: str,
        importance: int = 1,
        promoted_from: str = "",
    ) -> str:
        """Store a new entry in the archive.

        Args:
            agent_id: Owning agent identifier.
            topic: Short topic / title for the entry.
            summary: Full descriptive text (indexed by FTS5).
            importance: Numeric importance score (higher = more important).
            promoted_from: Optional id of the source entry this was promoted
                from (e.g. a learning-tier id).

        Returns:
            The generated ``entry_id``.
        """
        entry_id = f"arch_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        cursor = self._conn.execute(
            """INSERT INTO archive
               (id, agent_id, topic, summary, importance,
                promoted_from, created_at, last_accessed)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (entry_id, agent_id, topic, summary, importance, promoted_from, now, now),
        )
        rowid = cursor.lastrowid
        self._conn.execute(
            "INSERT INTO archive_fts (rowid, topic, summary) VALUES (?, ?, ?)",
            (rowid, topic, summary),
        )
        self._conn.commit()
        return entry_id

    # ------------------------------------------------------------------
    # Read / Search
    # ------------------------------------------------------------------

    def search(self, agent_id: str, query: str, limit: int = 10) -> List[Dict]:
        """Full-text search within a single agent's archive.

        Args:
            agent_id: Restrict results to this agent.
            query: FTS5 match expression (words are OR-ed by default).
            limit: Maximum number of results.

        Returns:
            List of matching entries as dicts, ordered by FTS5 rank.
        """
        # Sanitise query to plain alphanumeric tokens for safety.
        tokens = [w for w in query.split() if w.isalnum()]
        if not tokens:
            return []
        sanitized = " ".join(tokens)

        rows = self._conn.execute(
            """SELECT a.* FROM archive a
               JOIN archive_fts f ON a.rowid = f.rowid
               WHERE f.archive_fts MATCH ? AND a.agent_id = ?
               ORDER BY rank
               LIMIT ?""",
            (sanitized, agent_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get(self, entry_id: str) -> Optional[Dict]:
        """Retrieve a single entry by id.

        Args:
            entry_id: The archive entry identifier.

        Returns:
            Entry dict, or ``None`` if not found.
        """
        row = self._conn.execute(
            "SELECT * FROM archive WHERE id = ?",
            (entry_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_by_agent(
        self,
        agent_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        """List entries for an agent, newest first.

        Args:
            agent_id: Agent identifier.
            limit: Maximum entries to return.
            offset: Pagination offset.

        Returns:
            List of entry dicts.
        """
        rows = self._conn.execute(
            """SELECT * FROM archive
               WHERE agent_id = ?
               ORDER BY created_at DESC
               LIMIT ? OFFSET ?""",
            (agent_id, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Access tracking
    # ------------------------------------------------------------------

    def record_access(self, entry_id: str) -> None:
        """Increment access counter and update last-accessed timestamp.

        Args:
            entry_id: The archive entry identifier.
        """
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "UPDATE archive SET access_count = access_count + 1, last_accessed = ? WHERE id = ?",
            (now, entry_id),
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def delete(self, entry_id: str) -> bool:
        """Delete an entry from the archive (and its FTS index).

        Args:
            entry_id: The archive entry identifier.

        Returns:
            ``True`` if a row was deleted.
        """
        row = self._conn.execute(
            "SELECT rowid FROM archive WHERE id = ?",
            (entry_id,),
        ).fetchone()
        if row is None:
            return False
        rowid = row["rowid"]
        self._conn.execute("DELETE FROM archive WHERE rowid = ?", (rowid,))
        self._conn.execute(
            "INSERT INTO archive_fts(archive_fts, rowid, topic, summary) "
            "VALUES('delete', ?, '', '')",
            (rowid,),
        )
        self._conn.commit()
        return True

    def count(self, agent_id: str | None = None) -> int:
        """Return the number of entries, optionally filtered by agent.

        Args:
            agent_id: Optional agent filter.

        Returns:
            Entry count.
        """
        if agent_id is not None:
            row = self._conn.execute(
                "SELECT COUNT(*) AS cnt FROM archive WHERE agent_id = ?",
                (agent_id,),
            ).fetchone()
        else:
            row = self._conn.execute("SELECT COUNT(*) AS cnt FROM archive").fetchone()
        return row["cnt"] if row else 0

    def close(self) -> None:
        """Close the underlying database connection."""
        self._conn.close()
