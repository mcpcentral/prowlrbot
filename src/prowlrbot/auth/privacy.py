# -*- coding: utf-8 -*-
"""Privacy settings and GDPR compliance utilities.

Provides configurable privacy controls including data retention,
anonymization, and user data export for GDPR compliance.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ..constant import WORKING_DIR

logger = logging.getLogger(__name__)

# Fields considered personally identifiable for anonymization.
_PII_FIELD_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"e[-_]?mail", re.IGNORECASE),
    re.compile(r"ip[-_]?addr", re.IGNORECASE),
    re.compile(r"user[-_]?name", re.IGNORECASE),
    re.compile(r"^name$", re.IGNORECASE),
    re.compile(r"phone", re.IGNORECASE),
    re.compile(r"address", re.IGNORECASE),
]

# Default SQLite tables that contain time-stamped user data.
_DEFAULT_RETENTION_TABLES: list[tuple[str, str]] = [
    ("sessions", "created_at"),
    ("chat_messages", "timestamp"),
    ("audit_log", "timestamp"),
    ("notifications", "created_at"),
]


class PrivacySettings(BaseModel):
    """User-facing privacy configuration."""

    enable_chat_logging: bool = True
    enable_session_recording: bool = True
    data_retention_days: int = Field(default=90, ge=1)
    log_tool_calls: bool = True
    log_model_requests: bool = False  # sensitive — disabled by default
    anonymize_exports: bool = False
    gdpr_mode: bool = False


class PrivacyManager:
    """Manage privacy settings and GDPR-related operations.

    Args:
        config_path: Path to the ``privacy.json`` settings file.
            Defaults to ``~/.prowlrbot/privacy.json``.
    """

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path or (WORKING_DIR / "privacy.json")

    # ------------------------------------------------------------------
    # Settings persistence
    # ------------------------------------------------------------------

    def get_settings(self) -> PrivacySettings:
        """Load privacy settings from disk.

        Returns default settings if the file does not exist or is
        unparseable.
        """
        if not self._config_path.is_file():
            return PrivacySettings()
        try:
            with open(self._config_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return PrivacySettings(**data)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning(
                "Failed to parse privacy settings from %s: %s",
                self._config_path,
                exc,
            )
            return PrivacySettings()

    def update_settings(self, settings: PrivacySettings) -> None:
        """Persist *settings* to disk."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as fh:
            json.dump(settings.model_dump(), fh, indent=2)
        logger.info("Privacy settings saved to %s", self._config_path)

    # ------------------------------------------------------------------
    # Data retention
    # ------------------------------------------------------------------

    def apply_retention(
        self,
        db_path: Path,
        days: int | None = None,
        tables: list[tuple[str, str]] | None = None,
    ) -> int:
        """Delete records older than *days* from SQLite *db_path*.

        Args:
            db_path: Path to the SQLite database file.
            days: Number of days to retain. Uses the configured
                ``data_retention_days`` when ``None``.
            tables: List of ``(table_name, timestamp_column)`` pairs.
                Defaults to common ProwlrBot tables.

        Returns:
            Total number of rows deleted across all tables.
        """
        if days is None:
            days = self.get_settings().data_retention_days
        if tables is None:
            tables = _DEFAULT_RETENTION_TABLES

        cutoff = time.time() - (days * 86400)
        total_deleted = 0

        if not db_path.is_file():
            logger.warning("Database not found: %s", db_path)
            return 0

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Discover which tables actually exist in this database.
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}

            for table, ts_col in tables:
                if table not in existing_tables:
                    continue
                try:
                    cursor.execute(
                        f"DELETE FROM [{table}] WHERE [{ts_col}] < ?",  # noqa: S608
                        (cutoff,),
                    )
                    deleted = cursor.rowcount
                    total_deleted += deleted
                    if deleted:
                        logger.info(
                            "Deleted %d rows from %s (older than %d days)",
                            deleted,
                            table,
                            days,
                        )
                except sqlite3.OperationalError as exc:
                    logger.warning(
                        "Could not apply retention to %s.%s: %s",
                        db_path.name,
                        table,
                        exc,
                    )

            conn.commit()
            conn.close()
        except sqlite3.Error as exc:
            logger.error("Database error during retention: %s", exc)

        return total_deleted

    # ------------------------------------------------------------------
    # Anonymization
    # ------------------------------------------------------------------

    @staticmethod
    def _is_pii_field(field_name: str) -> bool:
        """Return True if *field_name* looks like personally identifiable info."""
        return any(p.search(field_name) for p in _PII_FIELD_PATTERNS)

    @staticmethod
    def _hash_value(value: str) -> str:
        """One-way hash a PII value for anonymization."""
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]

    def anonymize_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Return a copy of *data* with PII fields replaced by hashes.

        Recursively walks nested dicts. String values whose keys match
        known PII patterns (email, IP, username, name, phone, address)
        are replaced with a truncated SHA-256 hash.
        """
        result: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, dict):
                result[key] = self.anonymize_data(value)
            elif isinstance(value, list):
                result[key] = [
                    self.anonymize_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            elif isinstance(value, str) and self._is_pii_field(key):
                result[key] = self._hash_value(value)
            else:
                result[key] = value
        return result

    # ------------------------------------------------------------------
    # GDPR data export
    # ------------------------------------------------------------------

    def export_user_data(
        self,
        user_id: str,
        working_dir: Path | None = None,
    ) -> dict[str, Any]:
        """Gather all data associated with *user_id* for GDPR export.

        Searches JSON data files and SQLite databases under
        *working_dir* for records referencing the user.

        Args:
            user_id: Identifier of the user requesting their data.
            working_dir: Root directory to scan. Defaults to
                ``WORKING_DIR``.

        Returns:
            Dictionary keyed by data source with the user's records.
        """
        if working_dir is None:
            working_dir = WORKING_DIR

        export: dict[str, Any] = {
            "user_id": user_id,
            "exported_at": time.time(),
            "sources": {},
        }

        # --- JSON files -----------------------------------------------
        for json_file in working_dir.rglob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as fh:
                    content = json.load(fh)
            except (json.JSONDecodeError, OSError):
                continue

            matches = self._extract_user_records(content, user_id)
            if matches:
                rel = str(json_file.relative_to(working_dir))
                export["sources"][rel] = matches

        # --- SQLite databases -----------------------------------------
        for db_file in working_dir.rglob("*.db"):
            try:
                conn = sqlite3.connect(str(db_file))
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'",
                )
                tables = [row[0] for row in cursor.fetchall()]

                db_records: dict[str, list[dict[str, Any]]] = {}
                for table in tables:
                    try:
                        cursor.execute(
                            f"SELECT * FROM [{table}] WHERE "  # noqa: S608
                            f"user_id = ? OR username = ?",
                            (user_id, user_id),
                        )
                        rows = [dict(row) for row in cursor.fetchall()]
                        if rows:
                            db_records[table] = rows
                    except sqlite3.OperationalError:
                        # Table may not have user_id/username columns.
                        continue

                if db_records:
                    rel = str(db_file.relative_to(working_dir))
                    export["sources"][rel] = db_records

                conn.close()
            except sqlite3.Error:
                continue

        # Optionally anonymize before returning.
        settings = self.get_settings()
        if settings.anonymize_exports:
            export["sources"] = self.anonymize_data(export["sources"])

        return export

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_user_records(
        data: Any,
        user_id: str,
    ) -> list[Any]:
        """Recursively find records in *data* that reference *user_id*."""
        matches: list[Any] = []

        if isinstance(data, dict):
            # Check if this dict itself references the user.
            values = [str(v) for v in data.values() if isinstance(v, str)]
            if user_id in values:
                matches.append(data)
            else:
                # Recurse into nested structures.
                for value in data.values():
                    matches.extend(
                        PrivacyManager._extract_user_records(value, user_id),
                    )
        elif isinstance(data, list):
            for item in data:
                matches.extend(
                    PrivacyManager._extract_user_records(item, user_id),
                )

        return matches
