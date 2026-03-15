# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import sqlite3
import time
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Migration(BaseModel):
    """A single schema migration."""

    version: int
    name: str
    up_sql: str
    down_sql: str
    applied_at: Optional[float] = None


class MigrationManager:
    """Manages SQLite schema migrations with up/down support."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._migrations: dict[int, Migration] = {}
        self._ensure_table()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _ensure_table(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS _migrations (
                    version  INTEGER PRIMARY KEY,
                    name     TEXT    NOT NULL,
                    applied_at REAL NOT NULL
                )
                """,
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(
        self,
        version: int,
        name: str,
        up_sql: str,
        down_sql: str,
    ) -> None:
        """Register a migration. Does not apply it."""
        self._migrations[version] = Migration(
            version=version,
            name=name,
            up_sql=up_sql,
            down_sql=down_sql,
        )

    def get_current_version(self) -> int:
        """Return the highest applied migration version, or 0."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT MAX(version) AS v FROM _migrations",
            ).fetchone()
            return row["v"] if row and row["v"] is not None else 0

    def get_pending(self) -> list[Migration]:
        """Return registered migrations that have not been applied yet."""
        current = self.get_current_version()
        return sorted(
            [m for m in self._migrations.values() if m.version > current],
            key=lambda m: m.version,
        )

    def migrate_up(self, target_version: int | None = None) -> list[Migration]:
        """Apply pending migrations up to *target_version* (inclusive).

        Returns the list of migrations that were applied.
        """
        pending = self.get_pending()
        if target_version is not None:
            pending = [m for m in pending if m.version <= target_version]

        applied: list[Migration] = []
        for migration in pending:
            logger.info(
                "Applying migration v%d: %s",
                migration.version,
                migration.name,
            )
            with self._connect() as conn:
                conn.executescript(migration.up_sql)
                conn.execute(
                    "INSERT INTO _migrations (version, name, applied_at) "
                    "VALUES (?, ?, ?)",
                    (migration.version, migration.name, time.time()),
                )
            applied.append(migration)
            logger.info("Applied migration v%d", migration.version)

        return applied

    def migrate_down(self, target_version: int) -> list[Migration]:
        """Roll back applied migrations down to *target_version* (exclusive).

        Migrations with version > target_version are rolled back in
        descending order.  Returns the list of rolled-back migrations.
        """
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT version, name FROM _migrations "
                "WHERE version > ? ORDER BY version DESC",
                (target_version,),
            ).fetchall()

        rolled_back: list[Migration] = []
        for row in rows:
            ver = row["version"]
            migration = self._migrations.get(ver)
            if migration is None:
                logger.warning(
                    "Migration v%d (%s) is applied but not registered; "
                    "skipping rollback",
                    ver,
                    row["name"],
                )
                continue

            logger.info(
                "Rolling back migration v%d: %s",
                migration.version,
                migration.name,
            )
            with self._connect() as conn:
                conn.executescript(migration.down_sql)
                conn.execute(
                    "DELETE FROM _migrations WHERE version = ?",
                    (migration.version,),
                )
            rolled_back.append(migration)
            logger.info("Rolled back migration v%d", migration.version)

        return rolled_back

    def get_history(self) -> list[Migration]:
        """Return all applied migrations with their timestamps."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT version, name, applied_at FROM _migrations "
                "ORDER BY version ASC",
            ).fetchall()

        result: list[Migration] = []
        for row in rows:
            ver = row["version"]
            registered = self._migrations.get(ver)
            result.append(
                Migration(
                    version=ver,
                    name=row["name"],
                    up_sql=registered.up_sql if registered else "",
                    down_sql=registered.down_sql if registered else "",
                    applied_at=row["applied_at"],
                ),
            )
        return result

    def status(self) -> dict:
        """Return a summary dict with current state."""
        current = self.get_current_version()
        pending = self.get_pending()
        history = self.get_history()
        return {
            "current_version": current,
            "pending_count": len(pending),
            "applied": [
                {
                    "version": m.version,
                    "name": m.name,
                    "applied_at": m.applied_at,
                }
                for m in history
            ],
        }
