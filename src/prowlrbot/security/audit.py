# -*- coding: utf-8 -*-
"""Append-only audit trail backed by SQLite.

The audit log is intentionally append-only: there is no ``UPDATE`` or
``DELETE`` (except time-based cleanup of very old records).  This makes
the log suitable as a tamper-evident record of security-relevant events.
"""

import json
import logging
import sqlite3
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from prowlrbot.constant import WORKING_DIR

logger = logging.getLogger(__name__)

AUDIT_DB_PATH = WORKING_DIR / "audit.db"


class AuditResult(str, Enum):
    """Possible outcomes for an audited action."""

    SUCCESS = "success"
    DENIED = "denied"
    ERROR = "error"


class AuditEntry(BaseModel):
    """A single audit-trail record."""

    id: Optional[int] = None
    timestamp: float = Field(default_factory=time.time)
    actor: str = Field(
        ...,
        description="Who performed the action (user, agent, system)",
    )
    action: str = Field(
        ...,
        description="What was done (e.g. login, config_change)",
    )
    target: str = Field(default="", description="The resource acted upon")
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: str = Field(default="")
    result: str = Field(default=AuditResult.SUCCESS)

    @property
    def timestamp_iso(self) -> str:
        """Return the timestamp as an ISO-8601 string (UTC)."""
        return datetime.fromtimestamp(
            self.timestamp,
            tz=timezone.utc,
        ).isoformat()


class AuditLog:
    """SQLite-backed, append-only audit log.

    The database is stored at ``WORKING_DIR/audit.db`` by default.  All
    write operations go through a single ``INSERT``; there are no UPDATE
    statements.  ``cleanup`` removes entries older than a configurable
    threshold to keep the database from growing unboundedly.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else AUDIT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrent read performance.
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()
        # Auto-cleanup on startup to prevent unbounded growth
        try:
            self.cleanup(older_than_days=90)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _create_tables(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp  REAL    NOT NULL,
                actor      TEXT    NOT NULL,
                action     TEXT    NOT NULL,
                target     TEXT    NOT NULL DEFAULT '',
                details    TEXT    NOT NULL DEFAULT '{}',
                ip_address TEXT    NOT NULL DEFAULT '',
                result     TEXT    NOT NULL DEFAULT 'success'
            )
        """,
        )
        self._conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audit_actor
            ON audit_log(actor, timestamp DESC)
        """,
        )
        self._conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audit_action
            ON audit_log(action, timestamp DESC)
        """,
        )
        self._conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp
            ON audit_log(timestamp DESC)
        """,
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def log(
        self,
        actor: str,
        action: str,
        target: str = "",
        details: Optional[Dict[str, Any]] = None,
        ip_address: str = "",
        result: str = AuditResult.SUCCESS,
    ) -> AuditEntry:
        """Append an audit entry. Returns the persisted entry."""
        entry = AuditEntry(
            actor=actor,
            action=action,
            target=target,
            details=details or {},
            ip_address=ip_address,
            result=result,
        )
        cursor = self._conn.execute(
            """
            INSERT INTO audit_log
                (timestamp, actor, action, target, details, ip_address, result)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.timestamp,
                entry.actor,
                entry.action,
                entry.target,
                json.dumps(entry.details),
                entry.ip_address,
                entry.result,
            ),
        )
        self._conn.commit()
        entry.id = cursor.lastrowid
        logger.info(
            "audit | %s | %s | %s | %s | %s",
            entry.actor,
            entry.action,
            entry.target,
            entry.result,
            entry.ip_address,
        )
        return entry

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def query(
        self,
        actor: Optional[str] = None,
        action: Optional[str] = None,
        target: Optional[str] = None,
        result: Optional[str] = None,
        since: Optional[float] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Query audit entries with optional filters.

        Results are ordered newest-first.
        """
        clauses: list[str] = []
        params: list[Any] = []

        if actor is not None:
            clauses.append("actor = ?")
            params.append(actor)
        if action is not None:
            clauses.append("action = ?")
            params.append(action)
        if target is not None:
            clauses.append("target = ?")
            params.append(target)
        if result is not None:
            clauses.append("result = ?")
            params.append(result)
        if since is not None:
            clauses.append("timestamp >= ?")
            params.append(since)

        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM audit_log{where} ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_entry(row) for row in rows]

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export(self, format: str = "json") -> str:
        """Export the full audit log.

        Parameters
        ----------
        format:
            ``"json"`` (default) returns a JSON array of all entries.

        Returns
        -------
        str
            The serialised audit log.
        """
        rows = self._conn.execute(
            "SELECT * FROM audit_log ORDER BY timestamp ASC",
        ).fetchall()
        entries = [self._row_to_entry(row) for row in rows]

        if format == "json":
            return json.dumps(
                [entry.model_dump() for entry in entries],
                indent=2,
                default=str,
            )

        raise ValueError(f"Unsupported export format: {format!r}")

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def cleanup(self, older_than_days: int = 365) -> int:
        """Delete entries older than *older_than_days*. Returns count deleted."""
        cutoff = time.time() - (older_than_days * 86400)
        cursor = self._conn.execute(
            "DELETE FROM audit_log WHERE timestamp < ?",
            (cutoff,),
        )
        self._conn.commit()
        deleted = cursor.rowcount
        if deleted:
            logger.info(
                "audit cleanup: removed %d entries older than %d days",
                deleted,
                older_than_days,
            )
        return deleted

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> AuditEntry:
        return AuditEntry(
            id=row["id"],
            timestamp=row["timestamp"],
            actor=row["actor"],
            action=row["action"],
            target=row["target"],
            details=json.loads(row["details"]),
            ip_address=row["ip_address"],
            result=row["result"],
        )

    def close(self) -> None:
        self._conn.close()
