# -*- coding: utf-8 -*-
"""Privacy controls API — settings, retention, anonymization, GDPR."""

from __future__ import annotations

import sqlite3
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from ...auth.middleware import get_current_user, require_role
from ...auth.models import Role, User
from ...auth.privacy import PrivacyManager, PrivacySettings
from ...constant import WORKING_DIR

router = APIRouter(prefix="/privacy", tags=["privacy"])

_manager = PrivacyManager(config_path=WORKING_DIR / "privacy.json")


# ------------------------------------------------------------------
# Settings
# ------------------------------------------------------------------


@router.get("/settings", response_model=PrivacySettings)
async def get_privacy_settings() -> PrivacySettings:
    """Return the current privacy settings."""
    return _manager.get_settings()


@router.put("/settings", response_model=PrivacySettings)
async def update_privacy_settings(
    settings: PrivacySettings,
    _user: User = Depends(require_role(Role.admin)),
) -> PrivacySettings:
    """Update and persist privacy settings."""
    _manager.update_settings(settings)
    return _manager.get_settings()


# ------------------------------------------------------------------
# Data retention
# ------------------------------------------------------------------


@router.post("/retention/apply")
async def apply_retention(
    days: int = Query(
        default=90,
        ge=1,
        description="Retain data newer than N days",
    ),
    dry_run: bool = Query(
        default=True,
        description="Preview without deleting",
    ),
    _user: User = Depends(require_role(Role.admin)),
) -> Dict[str, Any]:
    """Apply data retention policy across all databases.

    With *dry_run=True* (default) no data is modified — the response
    shows what *would* be removed.
    """
    total_deleted = 0
    results: Dict[str, int] = {}

    for db_file in WORKING_DIR.glob("*.db"):
        if dry_run:
            # For dry-run, use a read-only approach: count rows that
            # would be deleted without actually removing them.
            import time

            cutoff = time.time() - (days * 86400)
            try:
                conn = sqlite3.connect(str(db_file))
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'",
                )
                tables = [row[0] for row in cursor.fetchall()]
                db_total = 0
                for table in tables:
                    cursor.execute(
                        f"PRAGMA table_info([{table}])",
                    )  # noqa: S608
                    columns = [row[1] for row in cursor.fetchall()]
                    ts_cols = [
                        c
                        for c in columns
                        if c
                        in (
                            "created_at",
                            "timestamp",
                            "updated_at",
                            "sent_at",
                        )
                    ]
                    for col in ts_cols:
                        cursor.execute(
                            f"SELECT COUNT(*) FROM [{table}] "  # noqa: S608
                            f"WHERE [{col}] < ?",
                            (cutoff,),
                        )
                        count = cursor.fetchone()[0]
                        db_total += count
                        break
                conn.close()
                if db_total > 0:
                    results[db_file.name] = db_total
                    total_deleted += db_total
            except sqlite3.Error:
                continue
        else:
            deleted = _manager.apply_retention(db_file, days=days)
            if deleted > 0:
                results[db_file.name] = deleted
                total_deleted += deleted

    return {
        "dry_run": dry_run,
        "days": days,
        "total_deleted": total_deleted,
        "databases": results,
    }


# ------------------------------------------------------------------
# Anonymization
# ------------------------------------------------------------------


@router.post("/anonymize")
async def anonymize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Anonymize PII fields in the provided data dictionary."""
    return _manager.anonymize_data(data)


# ------------------------------------------------------------------
# GDPR data export
# ------------------------------------------------------------------


@router.get("/export/{user_id}")
async def export_user_data(
    user_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    if current_user.role != Role.admin and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Can only export your own data",
        )
    """Export all data associated with a user (GDPR data portability)."""
    result = _manager.export_user_data(user_id, working_dir=WORKING_DIR)
    return result


# ------------------------------------------------------------------
# GDPR right to be forgotten
# ------------------------------------------------------------------


@router.delete("/data/{user_id}")
async def delete_user_data(
    user_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    if current_user.role != Role.admin and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Can only delete your own data",
        )
    """Delete all data associated with a user (right to be forgotten).

    Iterates over every ``.db`` file in the working directory and
    attempts to remove rows where ``user_id``, ``agent_id``,
    ``owner_id``, or ``username`` matches *user_id*.  Also removes
    matching records from JSON data files.
    """
    records_deleted: Dict[str, int] = {}

    # --- SQLite databases ---------------------------------------------
    for db_file in WORKING_DIR.glob("*.db"):
        try:
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            db_total = 0
            for table in tables:
                cursor.execute(f"PRAGMA table_info([{table}])")  # noqa: S608
                columns = [row[1] for row in cursor.fetchall()]
                id_cols = [
                    c
                    for c in columns
                    if c in ("user_id", "agent_id", "owner_id", "username", "sub")
                ]
                for col in id_cols:
                    cursor.execute(
                        f"DELETE FROM [{table}] " f"WHERE [{col}] = ?",  # noqa: S608
                        (user_id,),
                    )
                    db_total += cursor.rowcount
            conn.commit()
            conn.close()
            if db_total > 0:
                records_deleted[db_file.name] = db_total
        except sqlite3.Error:
            continue

    # --- JSON data files ----------------------------------------------
    import json

    for json_file in WORKING_DIR.glob("*.json"):
        if json_file.name in ("config.json", "privacy.json", "settings.json"):
            continue
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                continue
            original = len(data)
            filtered = [
                item
                for item in data
                if not isinstance(item, dict)
                or user_id
                not in (
                    item.get("user_id", ""),
                    item.get("agent_id", ""),
                    item.get("owner_id", ""),
                    item.get("username", ""),
                )
            ]
            removed = original - len(filtered)
            if removed > 0:
                json_file.write_text(
                    json.dumps(filtered, indent=2),
                    encoding="utf-8",
                )
                records_deleted[json_file.name] = removed
        except (json.JSONDecodeError, OSError):
            continue

    total = sum(records_deleted.values())
    return {
        "user_id": user_id,
        "total_deleted": total,
        "records_deleted": records_deleted,
    }
