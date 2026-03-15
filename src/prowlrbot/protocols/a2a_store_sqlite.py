# -*- coding: utf-8 -*-
"""SQLite-backed task store for A2A protocol.

Replaces the in-memory A2ATaskStore with durable SQLite storage.
Tasks, messages, artifacts, and status history are persisted across
restarts. Complex fields are JSON-serialized.

Usage::

    store = SQLiteA2ATaskStore()  # default ~/.prowlrbot/a2a_tasks.db
    task = store.create(A2ATask(from_agent="agent-a", to_agent="agent-b"))
    store.update_status(task.id, TaskStatus.WORKING)
    store.append_message(task.id, Message(role="agent", parts=[...]))
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from typing import Dict, List, Optional

from .a2a_server import (
    A2ATask,
    Artifact,
    Message,
    Part,
    StatusEntry,
    TaskStatus,
)

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = os.path.join(
    os.path.expanduser("~"),
    ".prowlrbot",
    "a2a_tasks.db",
)


class SQLiteA2ATaskStore:
    """SQLite-backed task store for A2A coordination.

    Same interface as the in-memory ``A2ATaskStore`` but persists
    all data to disk. Thread-safe via ``check_same_thread=False``.

    Args:
        db_path: Path to the SQLite database file. Defaults to
            ``~/.prowlrbot/a2a_tasks.db``.
    """

    def __init__(self, db_path: str = _DEFAULT_DB_PATH) -> None:
        self._db_path = db_path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        # Enable WAL mode for safe concurrent reads during writes
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()

    def _create_tables(self) -> None:
        """Create tables on first use."""
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                from_agent TEXT NOT NULL DEFAULT '',
                to_agent TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'submitted',
                metadata_json TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS task_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                parts_json TEXT NOT NULL DEFAULT '[]',
                metadata_json TEXT NOT NULL DEFAULT '{}',
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            );

            CREATE TABLE IF NOT EXISTS task_artifacts (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                name TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                parts_json TEXT NOT NULL DEFAULT '[]',
                metadata_json TEXT NOT NULL DEFAULT '{}',
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            );

            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                status TEXT NOT NULL,
                timestamp REAL NOT NULL,
                message TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            );
            """,
        )
        self._conn.commit()

    def create(self, task: A2ATask) -> A2ATask:
        """Create and store a new task, recording the initial status.

        Args:
            task: The task to create.

        Returns:
            The created task with initial history recorded.
        """
        now = time.time()
        task.history.append(StatusEntry(status=task.status, timestamp=now))

        with self._lock:
            self._conn.execute(
                "INSERT INTO tasks (id, from_agent, to_agent, status, metadata_json) VALUES (?, ?, ?, ?, ?)",
                (
                    task.id,
                    task.from_agent,
                    task.to_agent,
                    task.status,
                    json.dumps(task.metadata),
                ),
            )

            for msg in task.messages:
                self._insert_message(task.id, msg)

            for artifact in task.artifacts:
                self._insert_artifact(task.id, artifact)

            self._conn.execute(
                "INSERT INTO task_history (task_id, status, timestamp, message) VALUES (?, ?, ?, ?)",
                (task.id, task.status, now, None),
            )

            self._conn.commit()
        logger.debug("Created task %s in SQLite store", task.id)
        return task

    def get(self, task_id: str) -> Optional[A2ATask]:
        """Retrieve a task by ID.

        Args:
            task_id: The task ID.

        Returns:
            The task if found, None otherwise.
        """
        row = self._conn.execute(
            "SELECT id, from_agent, to_agent, status, metadata_json FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
        if row is None:
            return None
        return self._build_task(row)

    def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        message: Optional[str] = None,
    ) -> Optional[A2ATask]:
        """Transition a task to a new status with history tracking.

        Args:
            task_id: The task ID.
            status: The new status.
            message: Optional message describing the transition.

        Returns:
            The updated task, or None if not found.
        """
        with self._lock:
            row = self._conn.execute(
                "SELECT id FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
            if row is None:
                return None

            now = time.time()
            self._conn.execute(
                "UPDATE tasks SET status = ? WHERE id = ?",
                (status, task_id),
            )
            self._conn.execute(
                "INSERT INTO task_history (task_id, status, timestamp, message) VALUES (?, ?, ?, ?)",
                (task_id, status, now, message),
            )
            self._conn.commit()
        return self.get(task_id)

    def append_message(self, task_id: str, msg: Message) -> Optional[A2ATask]:
        """Append a message to an existing task.

        Args:
            task_id: The task ID.
            msg: The message to append.

        Returns:
            The updated task, or None if not found.
        """
        with self._lock:
            row = self._conn.execute(
                "SELECT id FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
            if row is None:
                return None

            self._insert_message(task_id, msg)
            self._conn.commit()
        return self.get(task_id)

    def append_artifact(
        self,
        task_id: str,
        artifact: Artifact,
    ) -> Optional[A2ATask]:
        """Append an output artifact to a task.

        Args:
            task_id: The task ID.
            artifact: The artifact to append.

        Returns:
            The updated task, or None if not found.
        """
        with self._lock:
            row = self._conn.execute(
                "SELECT id FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
            if row is None:
                return None

            self._insert_artifact(task_id, artifact)
            self._conn.commit()
        return self.get(task_id)

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[A2ATask]:
        """List all tasks, optionally filtered by status.

        Args:
            status: Filter by task status (None = all tasks).

        Returns:
            List of matching tasks.
        """
        if status:
            rows = self._conn.execute(
                "SELECT id, from_agent, to_agent, status, metadata_json FROM tasks WHERE status = ?",
                (status,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT id, from_agent, to_agent, status, metadata_json FROM tasks",
            ).fetchall()
        return [self._build_task(row) for row in rows]

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    # -- internal helpers -----------------------------------------------------

    def _insert_message(self, task_id: str, msg: Message) -> None:
        """Insert a message row."""
        parts_json = json.dumps([p.model_dump() for p in msg.parts])
        self._conn.execute(
            "INSERT INTO task_messages (task_id, role, parts_json, metadata_json) VALUES (?, ?, ?, ?)",
            (task_id, msg.role, parts_json, json.dumps(msg.metadata)),
        )

    def _insert_artifact(self, task_id: str, artifact: Artifact) -> None:
        """Insert an artifact row."""
        parts_json = json.dumps([p.model_dump() for p in artifact.parts])
        self._conn.execute(
            "INSERT INTO task_artifacts (id, task_id, name, description, parts_json, metadata_json) VALUES (?, ?, ?, ?, ?, ?)",
            (
                artifact.id,
                task_id,
                artifact.name,
                artifact.description,
                parts_json,
                json.dumps(artifact.metadata),
            ),
        )

    def _build_task(self, row: sqlite3.Row) -> A2ATask:
        """Build a full A2ATask from a tasks row plus related data."""
        task_id = row["id"]

        # Load messages
        msg_rows = self._conn.execute(
            "SELECT role, parts_json, metadata_json FROM task_messages WHERE task_id = ? ORDER BY id",
            (task_id,),
        ).fetchall()
        messages = []
        for mr in msg_rows:
            parts = [Part(**p) for p in json.loads(mr["parts_json"])]
            messages.append(
                Message(
                    role=mr["role"],
                    parts=parts,
                    metadata=json.loads(mr["metadata_json"]),
                ),
            )

        # Load artifacts
        art_rows = self._conn.execute(
            "SELECT id, name, description, parts_json, metadata_json FROM task_artifacts WHERE task_id = ? ORDER BY id",
            (task_id,),
        ).fetchall()
        artifacts = []
        for ar in art_rows:
            parts = [Part(**p) for p in json.loads(ar["parts_json"])]
            artifacts.append(
                Artifact(
                    id=ar["id"],
                    name=ar["name"],
                    description=ar["description"],
                    parts=parts,
                    metadata=json.loads(ar["metadata_json"]),
                ),
            )

        # Load history
        hist_rows = self._conn.execute(
            "SELECT status, timestamp, message FROM task_history WHERE task_id = ? ORDER BY id",
            (task_id,),
        ).fetchall()
        history = [
            StatusEntry(
                status=TaskStatus(hr["status"]),
                timestamp=hr["timestamp"],
                message=hr["message"],
            )
            for hr in hist_rows
        ]

        return A2ATask(
            id=task_id,
            from_agent=row["from_agent"],
            to_agent=row["to_agent"],
            status=TaskStatus(row["status"]),
            messages=messages,
            artifacts=artifacts,
            history=history,
            metadata=json.loads(row["metadata_json"]),
        )
