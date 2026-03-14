# -*- coding: utf-8 -*-
"""ProwlrHub — Core coordination engine.

All business logic for the war room: room management, agent lifecycle,
atomic task claiming, file locking, and event logging. This module
has ZERO UI or transport assumptions — it only talks to SQLite.
"""

from __future__ import annotations

import json
import logging
import platform
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .db import init_db

logger = logging.getLogger(__name__)


# --- Result types ---


@dataclass
class ClaimResult:
    success: bool
    reason: str = ""
    lock_token: str = ""
    conflicts: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class LockResult:
    success: bool
    reason: str = ""
    lock_token: str = ""
    owner: str = ""


class WarRoomEngine:
    """Core war room coordination engine.

    All operations are atomic via SQLite transactions.
    Thread-safe for concurrent MCP server processes sharing the same DB.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._conn = init_db(db_path)
        self._db_path = db_path
        self._on_event = None
        self._lock = threading.RLock()

    def set_event_callback(self, callback):
        """Set a callback function called on every mutation."""
        self._on_event = callback

    def _notify(self, event_type: str, payload: dict):
        """Notify listeners of an engine event."""
        if self._on_event:
            try:
                self._on_event(
                    {
                        "type": event_type,
                        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                        **payload,
                    }
                )
            except Exception:
                pass  # Don't let notification errors break the engine

    # -- Room Management --

    def create_room(
        self,
        name: str,
        mode: str = "local",
        host_node_id: str = "",
    ) -> Dict[str, Any]:
        """Create a new war room."""
        with self._lock:
            room_id = f"room-{uuid.uuid4().hex[:12]}"
            if not host_node_id:
                host_node_id = f"node-{platform.node()}-{uuid.uuid4().hex[:8]}"

            self._conn.execute(
                "INSERT INTO rooms (room_id, name, host_node_id, mode) VALUES (?, ?, ?, ?)",
                (room_id, name, host_node_id, mode),
            )
            self._conn.commit()
            self._emit_event(room_id, "room.created", payload={"name": name, "mode": mode})
            return {
                "room_id": room_id,
                "name": name,
                "mode": mode,
                "host_node_id": host_node_id,
            }

    def get_room(self, room_id: str) -> Optional[Dict[str, Any]]:
        """Get room details."""
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM rooms WHERE room_id=?", (room_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_or_create_default_room(self) -> Dict[str, Any]:
        """Get the first room, or create a default one."""
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM rooms ORDER BY created_at ASC LIMIT 1"
            ).fetchone()
            if row:
                return dict(row)
            return self.create_room("default", mode="local")

    # -- Agent Lifecycle --

    def register_agent(
        self,
        name: str,
        room_id: str,
        capabilities: Optional[List[str]] = None,
        node_id: str = "",
    ) -> Dict[str, Any]:
        """Register a new agent in the war room."""
        with self._lock:
            agent_id = f"agent-{uuid.uuid4().hex[:12]}"
            session_id = uuid.uuid4().hex

            if not node_id:
                node_id = f"node-{platform.node()}-{uuid.uuid4().hex[:8]}"

            # Ensure node exists
            existing = self._conn.execute(
                "SELECT node_id FROM nodes WHERE node_id=?", (node_id,)
            ).fetchone()
            if not existing:
                self._conn.execute(
                    "INSERT INTO nodes (node_id, hostname, platform) VALUES (?, ?, ?)",
                    (node_id, platform.node(), platform.system().lower()),
                )

            caps = json.dumps(capabilities or [])
            self._conn.execute(
                """INSERT INTO agents (agent_id, session_id, name, node_id, room_id, capabilities)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (agent_id, session_id, name, node_id, room_id, caps),
            )
            self._conn.commit()
            self._emit_event(
                room_id,
                "agent.connected",
                agent_id=agent_id,
                payload={"name": name, "capabilities": capabilities or []},
            )
            self._notify("agent.connected", {"agent_id": agent_id, "name": name})

            return {
                "agent_id": agent_id,
                "session_id": session_id,
                "name": name,
                "room_id": room_id,
                "capabilities": capabilities or [],
            }

    def heartbeat(self, agent_id: str) -> bool:
        """Update agent heartbeat timestamp."""
        with self._lock:
            self._conn.execute(
                "UPDATE agents SET last_heartbeat=datetime('now') WHERE agent_id=?",
                (agent_id,),
            )
            self._conn.commit()
        return True

    def get_agents(self, room_id: str) -> List[Dict[str, Any]]:
        """List all agents in a room."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM agents WHERE room_id=? ORDER BY registered_at",
                (room_id,),
            ).fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d["capabilities"] = json.loads(d["capabilities"])
                result.append(d)
        return result

    def disconnect_agent(self, agent_id: str) -> None:
        """Mark an agent as disconnected and release its resources."""
        with self._lock:
            agent = self._conn.execute(
                "SELECT * FROM agents WHERE agent_id=?", (agent_id,)
            ).fetchone()
            if not agent:
                return

            room_id = agent["room_id"]

            # Release all file locks
            self._conn.execute("DELETE FROM file_locks WHERE agent_id=?", (agent_id,))

            # Release owned tasks back to pending
            self._conn.execute(
                "UPDATE tasks SET status='pending', owner_agent_id=NULL, claimed_at=NULL WHERE owner_agent_id=? AND status IN ('claimed', 'in_progress')",
                (agent_id,),
            )

            self._conn.execute(
                "UPDATE agents SET status='disconnected', current_task_id=NULL WHERE agent_id=?",
                (agent_id,),
            )
            self._conn.commit()
            self._emit_event(room_id, "agent.disconnected", agent_id=agent_id)

    def sweep_dead_agents(self, ttl_minutes: int = 5) -> int:
        """Disconnect agents that haven't sent a heartbeat within TTL."""
        from datetime import timezone

        with self._lock:
            cutoff = (datetime.now(timezone.utc) - timedelta(minutes=ttl_minutes)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            stale = self._conn.execute(
                "SELECT agent_id FROM agents WHERE last_heartbeat < ? AND status != 'disconnected'",
                (cutoff,),
            ).fetchall()
            agent_ids = [row["agent_id"] for row in stale]

        for agent_id in agent_ids:
            self.disconnect_agent(agent_id)

        return len(agent_ids)

    # -- Task Management --

    def create_task(
        self,
        room_id: str,
        title: str,
        description: str = "",
        required_capabilities: Optional[List[str]] = None,
        file_scopes: Optional[List[str]] = None,
        parent_task_id: str = "",
        blocked_by: Optional[List[str]] = None,
        priority: str = "normal",
        branch: str = "",
    ) -> Dict[str, Any]:
        """Create a new task on the mission board."""
        with self._lock:
            task_id = f"task-{uuid.uuid4().hex[:12]}"

            self._conn.execute(
                """INSERT INTO tasks
                   (task_id, room_id, title, description, required_capabilities,
                    file_scopes, parent_task_id, blocked_by, priority, branch)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task_id,
                    room_id,
                    title,
                    description,
                    json.dumps(required_capabilities or []),
                    json.dumps(file_scopes or []),
                    parent_task_id or None,
                    json.dumps(blocked_by or []),
                    priority,
                    branch,
                ),
            )
            self._conn.commit()
            self._emit_event(
                room_id,
                "task.created",
                task_id=task_id,
                payload={"title": title, "priority": priority},
            )
            return {
                "task_id": task_id,
                "title": title,
                "status": "pending",
                "priority": priority,
            }

    def get_mission_board(
        self,
        room_id: str,
        agent_capabilities: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get all tasks visible to an agent (filtered by capabilities).

        Returns tasks sorted by priority then creation time.
        """
        with self._lock:
            rows = self._conn.execute(
                """SELECT t.*, a.name as owner_name
                   FROM tasks t
                   LEFT JOIN agents a ON t.owner_agent_id = a.agent_id
                   WHERE t.room_id=?
                   ORDER BY
                     CASE t.priority
                       WHEN 'critical' THEN 0
                       WHEN 'high' THEN 1
                       WHEN 'normal' THEN 2
                       WHEN 'low' THEN 3
                     END,
                     t.created_at ASC""",
                (room_id,),
            ).fetchall()

            tasks = []
            for row in rows:
                d = dict(row)
                d["required_capabilities"] = json.loads(d["required_capabilities"])
                d["file_scopes"] = json.loads(d["file_scopes"])
                d["collaborators"] = json.loads(d["collaborators"])
                d["blocked_by"] = json.loads(d["blocked_by"])

                # Filter by capability if specified
                if agent_capabilities and d["required_capabilities"]:
                    if not any(c in agent_capabilities for c in d["required_capabilities"]):
                        continue

                # Check if blocked
                if d["blocked_by"]:
                    blockers_done = True
                    for blocker_id in d["blocked_by"]:
                        blocker = self._conn.execute(
                            "SELECT status FROM tasks WHERE task_id=?", (blocker_id,)
                        ).fetchone()
                        if blocker and blocker["status"] not in ("done", "failed"):
                            blockers_done = False
                            break
                    d["is_blocked"] = not blockers_done
                else:
                    d["is_blocked"] = False

                tasks.append(d)
        return tasks

    def claim_task(
        self,
        task_id: str,
        agent_id: str,
        room_id: str,
        branch: str = "",
    ) -> ClaimResult:
        """Atomically claim a task and lock its file scopes.

        This is the most critical operation — uses a SQLite transaction
        to ensure no two agents can claim the same task or lock the same files.
        """
        try:
            with self._lock, self._conn:
                # Check task is available
                task = self._conn.execute(
                    "SELECT * FROM tasks WHERE task_id=? AND status='pending'",
                    (task_id,),
                ).fetchone()

                if not task:
                    return ClaimResult(success=False, reason="not_available")

                file_scopes = json.loads(task["file_scopes"])

                # Check all file scopes are free (on same branch or no branch)
                conflicts = []
                for fp in file_scopes:
                    lock = self._conn.execute(
                        """SELECT * FROM file_locks
                           WHERE file_path=? AND room_id=?
                           AND (branch='' OR branch=? OR ?='')""",
                        (fp, room_id, branch, branch),
                    ).fetchone()
                    if lock:
                        conflicts.append(
                            {
                                "file": fp,
                                "owner_agent_id": lock["agent_id"],
                                "lock_token": lock["lock_token"],
                            }
                        )

                if conflicts:
                    return ClaimResult(
                        success=False, reason="files_locked", conflicts=conflicts
                    )

                # Atomic claim
                lock_token = uuid.uuid4().hex
                self._conn.execute(
                    """UPDATE tasks
                       SET status='claimed', owner_agent_id=?, claimed_at=datetime('now'), branch=?
                       WHERE task_id=?""",
                    (agent_id, branch, task_id),
                )

                # Lock all file scopes
                for fp in file_scopes:
                    self._conn.execute(
                        """INSERT OR REPLACE INTO file_locks
                           (file_path, room_id, task_id, agent_id, lock_token, branch)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (fp, room_id, task_id, agent_id, lock_token, branch),
                    )

                # Update agent status
                self._conn.execute(
                    "UPDATE agents SET status='working', current_task_id=? WHERE agent_id=?",
                    (task_id, agent_id),
                )

            self._emit_event(
                room_id,
                "task.claimed",
                agent_id=agent_id,
                task_id=task_id,
                payload={"lock_token": lock_token, "file_scopes": file_scopes},
            )
            self._notify("task.claimed", {"task_id": task_id, "agent_id": agent_id})
            return ClaimResult(success=True, lock_token=lock_token)

        except sqlite3.IntegrityError:
            logger.warning("Claim conflict for task %s by agent %s", task_id, agent_id)
            return ClaimResult(success=False, reason="conflict")

    def update_task(
        self,
        task_id: str,
        agent_id: str,
        progress_note: str = "",
        status: str = "in_progress",
    ) -> bool:
        """Update task progress."""
        with self._lock:
            self._conn.execute(
                "UPDATE tasks SET status=?, progress_note=? WHERE task_id=? AND owner_agent_id=?",
                (status, progress_note, task_id, agent_id),
            )
            self._conn.commit()

            task = self._conn.execute(
                "SELECT room_id FROM tasks WHERE task_id=?", (task_id,)
            ).fetchone()
            if task:
                self._emit_event(
                    task["room_id"],
                    "task.updated",
                    agent_id=agent_id,
                    task_id=task_id,
                    payload={"status": status, "note": progress_note},
                )
        return True

    def complete_task(
        self,
        task_id: str,
        agent_id: str,
        summary: str = "",
    ) -> bool:
        """Mark a task as done and release all associated locks."""
        with self._lock:
            task = self._conn.execute(
                "SELECT * FROM tasks WHERE task_id=? AND owner_agent_id=?",
                (task_id, agent_id),
            ).fetchone()
            if not task:
                return False

            room_id = task["room_id"]

            self._conn.execute(
                """UPDATE tasks
                   SET status='done', completed_at=datetime('now'), progress_note=?
                   WHERE task_id=?""",
                (summary, task_id),
            )
            # Release file locks for this task
            self._conn.execute(
                "DELETE FROM file_locks WHERE task_id=? AND agent_id=?",
                (task_id, agent_id),
            )
            # Update agent
            self._conn.execute(
                "UPDATE agents SET status='idle', current_task_id=NULL WHERE agent_id=?",
                (agent_id,),
            )
            self._conn.commit()

            self._emit_event(
                room_id,
                "task.completed",
                agent_id=agent_id,
                task_id=task_id,
                payload={"summary": summary},
            )
            self._notify("task.completed", {"task_id": task_id, "agent_id": agent_id})
        return True

    def fail_task(
        self,
        task_id: str,
        agent_id: str,
        reason: str = "",
    ) -> bool:
        """Mark a task as failed and release resources."""
        with self._lock:
            task = self._conn.execute(
                "SELECT * FROM tasks WHERE task_id=? AND owner_agent_id=?",
                (task_id, agent_id),
            ).fetchone()
            if not task:
                return False

            room_id = task["room_id"]

            self._conn.execute(
                "UPDATE tasks SET status='failed', progress_note=? WHERE task_id=?",
                (reason, task_id),
            )
            self._conn.execute(
                "DELETE FROM file_locks WHERE task_id=? AND agent_id=?",
                (task_id, agent_id),
            )
            self._conn.execute(
                "UPDATE agents SET status='idle', current_task_id=NULL WHERE agent_id=?",
                (agent_id,),
            )
            self._conn.commit()

            self._emit_event(
                room_id,
                "task.failed",
                agent_id=agent_id,
                task_id=task_id,
                payload={"reason": reason},
            )
            self._notify("task.failed", {"task_id": task_id, "agent_id": agent_id})
        return True

    # -- File Locking --

    def lock_file(
        self,
        file_path: str,
        agent_id: str,
        room_id: str,
        branch: str = "",
    ) -> LockResult:
        """Advisory file lock outside of a task. Atomic via transaction."""
        try:
            with self._lock, self._conn:
                existing = self._conn.execute(
                    """SELECT * FROM file_locks
                       WHERE file_path=? AND room_id=?
                       AND (branch='' OR branch=? OR ?='')""",
                    (file_path, room_id, branch, branch),
                ).fetchone()

                if existing and existing["agent_id"] != agent_id:
                    return LockResult(
                        success=False,
                        reason="already_locked",
                        owner=existing["agent_id"],
                    )

                lock_token = uuid.uuid4().hex
                self._conn.execute(
                    """INSERT OR REPLACE INTO file_locks
                       (file_path, room_id, agent_id, lock_token, branch)
                       VALUES (?, ?, ?, ?, ?)""",
                    (file_path, room_id, agent_id, lock_token, branch),
                )
            self._emit_event(
                room_id,
                "lock.acquired",
                agent_id=agent_id,
                payload={"file": file_path, "branch": branch},
            )
            self._notify(
                "lock.acquired", {"file_path": file_path, "agent_id": agent_id}
            )
            return LockResult(success=True, lock_token=lock_token)
        except sqlite3.IntegrityError:
            return LockResult(success=False, reason="conflict")

    def unlock_file(
        self,
        file_path: str,
        agent_id: str,
        room_id: str,
    ) -> bool:
        """Release a file lock."""
        with self._lock:
            result = self._conn.execute(
                "DELETE FROM file_locks WHERE file_path=? AND agent_id=? AND room_id=?",
                (file_path, agent_id, room_id),
            )
            self._conn.commit()
            if result.rowcount > 0:
                self._emit_event(
                    room_id, "lock.released", agent_id=agent_id, payload={"file": file_path}
                )
                self._notify(
                    "lock.released", {"file_path": file_path, "agent_id": agent_id}
                )
                return True
        return False

    def check_conflicts(
        self,
        file_paths: List[str],
        room_id: str,
        branch: str = "",
    ) -> List[Dict[str, Any]]:
        """Check which files are locked and by whom."""
        with self._lock:
            conflicts = []
            for fp in file_paths:
                lock = self._conn.execute(
                    """SELECT fl.*, a.name as agent_name
                       FROM file_locks fl
                       LEFT JOIN agents a ON fl.agent_id = a.agent_id
                       WHERE fl.file_path=? AND fl.room_id=?
                       AND (fl.branch='' OR fl.branch=? OR ?='')""",
                    (fp, room_id, branch, branch),
                ).fetchone()
                if lock:
                    conflicts.append(
                        {
                            "file": fp,
                            "agent_id": lock["agent_id"],
                            "agent_name": lock["agent_name"],
                            "task_id": lock["task_id"],
                            "branch": lock["branch"],
                        }
                    )
        return conflicts

    # -- Shared Context --

    def set_context(self, room_id: str, agent_id: str, key: str, value: Any) -> None:
        """Publish a finding or context to the shared store."""
        with self._lock:
            self._conn.execute(
                """INSERT OR REPLACE INTO shared_context (key, room_id, agent_id, value, updated_at)
                   VALUES (?, ?, ?, ?, datetime('now'))""",
                (key, room_id, agent_id, json.dumps(value)),
            )
            self._conn.commit()
            self._notify("finding.shared", {"key": key, "agent_id": agent_id})

    def get_context(self, room_id: str, key: str = "") -> List[Dict[str, Any]]:
        """Read shared context. Empty key returns all."""
        with self._lock:
            if key:
                rows = self._conn.execute(
                    "SELECT * FROM shared_context WHERE room_id=? AND key=?",
                    (room_id, key),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM shared_context WHERE room_id=? ORDER BY updated_at DESC",
                    (room_id,),
                ).fetchall()

            results = []
            for row in rows:
                d = dict(row)
                d["value"] = json.loads(d["value"])
                results.append(d)
        return results

    # -- Events --

    def get_events(
        self,
        room_id: str,
        limit: int = 50,
        event_type: str = "",
    ) -> List[Dict[str, Any]]:
        """Get recent events from the war room."""
        with self._lock:
            if event_type:
                rows = self._conn.execute(
                    "SELECT * FROM events WHERE room_id=? AND type=? ORDER BY timestamp DESC LIMIT ?",
                    (room_id, event_type, limit),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM events WHERE room_id=? ORDER BY timestamp DESC LIMIT ?",
                    (room_id, limit),
                ).fetchall()

            results = []
            for row in rows:
                d = dict(row)
                d["payload"] = json.loads(d["payload"])
                results.append(d)
        return results

    def broadcast_status(
        self,
        room_id: str,
        agent_id: str,
        message: str,
    ) -> None:
        """Broadcast a status message to the room."""
        self._emit_event(
            room_id,
            "agent.broadcast",
            agent_id=agent_id,
            payload={"message": message},
        )
        self._notify("agent.broadcast", {"agent_id": agent_id, "message": message})

    # -- Internal --

    def _emit_event(
        self,
        room_id: str,
        event_type: str,
        agent_id: str = "",
        task_id: str = "",
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an event to the event store. Thread-safe."""
        with self._lock:
            event_id = f"evt-{uuid.uuid4().hex[:12]}"
            self._conn.execute(
                "INSERT INTO events (event_id, type, room_id, agent_id, task_id, payload) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    event_id,
                    event_type,
                    room_id,
                    agent_id or None,
                    task_id or None,
                    json.dumps(payload or {}),
                ),
            )
            self._conn.commit()

    def purge_old_events(self, retention_days: int = 30) -> int:
        """Delete events older than retention_days. Returns count deleted."""
        with self._lock:
            cutoff = (
                datetime.now(tz=timezone.utc) - timedelta(days=retention_days)
            ).isoformat()
            result = self._conn.execute(
                "DELETE FROM events WHERE timestamp < ?",
                (cutoff,),
            )
            self._conn.commit()
            return result.rowcount

    def close(self) -> None:
        """Close the database connection."""
        with self._lock:
            self._conn.close()
