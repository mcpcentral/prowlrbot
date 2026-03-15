# -*- coding: utf-8 -*-
"""Notification center — stores and manages notifications."""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from prowlrbot.compat import StrEnum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class NotificationType(StrEnum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    ALERT = "alert"
    SYSTEM = "system"


class NotificationPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(BaseModel):
    """A single notification."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str
    message: str = ""
    notification_type: NotificationType = NotificationType.INFO
    priority: NotificationPriority = NotificationPriority.NORMAL
    source: str = ""  # which module generated it
    agent_id: str = ""
    read: bool = False
    dismissed: bool = False
    action_url: str = ""  # optional deep link
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = 0.0
    read_at: float = 0.0


class NotificationStats(BaseModel):
    """Notification statistics."""

    total: int = 0
    unread: int = 0
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_priority: Dict[str, int] = Field(default_factory=dict)


class NotificationCenter:
    """Manages notifications with SQLite storage."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                message TEXT DEFAULT '',
                notification_type TEXT DEFAULT 'info',
                priority TEXT DEFAULT 'normal',
                source TEXT DEFAULT '',
                agent_id TEXT DEFAULT '',
                read INTEGER DEFAULT 0,
                dismissed INTEGER DEFAULT 0,
                action_url TEXT DEFAULT '',
                metadata TEXT DEFAULT '{}',
                created_at REAL NOT NULL,
                read_at REAL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_notif_read ON notifications(read);
            CREATE INDEX IF NOT EXISTS idx_notif_type ON notifications(notification_type);
            CREATE INDEX IF NOT EXISTS idx_notif_created ON notifications(created_at);
        """,
        )
        self._conn.commit()

    def send(self, notification: Notification) -> Notification:
        """Send a new notification."""
        if not notification.created_at:
            notification.created_at = time.time()
        self._conn.execute(
            "INSERT INTO notifications "
            "(id, title, message, notification_type, priority, source, agent_id, "
            "read, dismissed, action_url, metadata, created_at, read_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                notification.id,
                notification.title,
                notification.message,
                notification.notification_type,
                notification.priority,
                notification.source,
                notification.agent_id,
                0,
                0,
                notification.action_url,
                json.dumps(notification.metadata),
                notification.created_at,
                0,
            ),
        )
        self._conn.commit()
        return notification

    def get(self, notification_id: str) -> Optional[Notification]:
        row = self._conn.execute(
            "SELECT * FROM notifications WHERE id = ?",
            (notification_id,),
        ).fetchone()
        if not row:
            return None
        return self._row_to_notification(row)

    def list_notifications(
        self,
        unread_only: bool = False,
        notification_type: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        query = "SELECT * FROM notifications WHERE dismissed = 0"
        params: list = []
        if unread_only:
            query += " AND read = 0"
        if notification_type:
            query += " AND notification_type = ?"
            params.append(notification_type)
        if source:
            query += " AND source = ?"
            params.append(source)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_notification(r) for r in rows]

    def mark_read(self, notification_id: str) -> bool:
        cursor = self._conn.execute(
            "UPDATE notifications SET read = 1, read_at = ? WHERE id = ?",
            (time.time(), notification_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def mark_all_read(self) -> int:
        cursor = self._conn.execute(
            "UPDATE notifications SET read = 1, read_at = ? WHERE read = 0",
            (time.time(),),
        )
        self._conn.commit()
        return cursor.rowcount

    def dismiss(self, notification_id: str) -> bool:
        cursor = self._conn.execute(
            "UPDATE notifications SET dismissed = 1 WHERE id = ?",
            (notification_id,),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def get_stats(self) -> NotificationStats:
        total = self._conn.execute(
            "SELECT COUNT(*) as c FROM notifications WHERE dismissed = 0",
        ).fetchone()["c"]
        unread = self._conn.execute(
            "SELECT COUNT(*) as c FROM notifications WHERE read = 0 AND dismissed = 0",
        ).fetchone()["c"]

        by_type: Dict[str, int] = {}
        for row in self._conn.execute(
            "SELECT notification_type, COUNT(*) as c FROM notifications "
            "WHERE dismissed = 0 GROUP BY notification_type",
        ).fetchall():
            by_type[row["notification_type"]] = row["c"]

        by_priority: Dict[str, int] = {}
        for row in self._conn.execute(
            "SELECT priority, COUNT(*) as c FROM notifications "
            "WHERE dismissed = 0 GROUP BY priority",
        ).fetchall():
            by_priority[row["priority"]] = row["c"]

        return NotificationStats(
            total=total,
            unread=unread,
            by_type=by_type,
            by_priority=by_priority,
        )

    def cleanup(self, older_than_days: int = 30) -> int:
        """Remove old dismissed notifications."""
        cutoff = time.time() - (older_than_days * 86400)
        cursor = self._conn.execute(
            "DELETE FROM notifications WHERE dismissed = 1 AND created_at < ?",
            (cutoff,),
        )
        self._conn.commit()
        return cursor.rowcount

    @staticmethod
    def _row_to_notification(row: sqlite3.Row) -> Notification:
        return Notification(
            id=row["id"],
            title=row["title"],
            message=row["message"],
            notification_type=NotificationType(row["notification_type"]),
            priority=NotificationPriority(row["priority"]),
            source=row["source"],
            agent_id=row["agent_id"],
            read=bool(row["read"]),
            dismissed=bool(row["dismissed"]),
            action_url=row["action_url"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=row["created_at"],
            read_at=row["read_at"],
        )

    def close(self) -> None:
        self._conn.close()
