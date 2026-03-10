# -*- coding: utf-8 -*-
"""ProwlrHub — SQLite database schema and connection management.

All war room state lives in a single SQLite file. Multiple Claude Code
instances connect via separate MCP server processes, all sharing the
same database. SQLite's WAL mode + transactions provide atomic claiming.
"""
from __future__ import annotations

import os
import sqlite3
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default location: ~/.prowlrbot/warroom.db
DEFAULT_DB_PATH = os.path.expanduser("~/.prowlrbot/warroom.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS rooms (
    room_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    host_node_id TEXT NOT NULL DEFAULT '',
    mode TEXT NOT NULL DEFAULT 'local',
    auth_policy TEXT NOT NULL DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS agents (
    agent_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    node_id TEXT NOT NULL DEFAULT '',
    room_id TEXT NOT NULL,
    capabilities TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'idle',
    current_task_id TEXT,
    last_heartbeat TEXT NOT NULL DEFAULT (datetime('now')),
    registered_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);

CREATE TABLE IF NOT EXISTS nodes (
    node_id TEXT PRIMARY KEY,
    hostname TEXT NOT NULL,
    platform TEXT NOT NULL DEFAULT 'unknown',
    labels TEXT NOT NULL DEFAULT '[]',
    transport TEXT NOT NULL DEFAULT 'local',
    health TEXT NOT NULL DEFAULT 'online',
    last_seen TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    room_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    priority TEXT NOT NULL DEFAULT 'normal',
    owner_agent_id TEXT,
    collaborators TEXT NOT NULL DEFAULT '[]',
    required_capabilities TEXT NOT NULL DEFAULT '[]',
    file_scopes TEXT NOT NULL DEFAULT '[]',
    parent_task_id TEXT,
    blocked_by TEXT NOT NULL DEFAULT '[]',
    branch TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    claimed_at TEXT,
    completed_at TEXT,
    progress_note TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);

CREATE TABLE IF NOT EXISTS file_locks (
    file_path TEXT NOT NULL,
    room_id TEXT NOT NULL,
    task_id TEXT,
    agent_id TEXT NOT NULL,
    lock_token TEXT NOT NULL UNIQUE,
    branch TEXT NOT NULL DEFAULT '',
    acquired_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT,
    PRIMARY KEY (file_path, room_id, branch),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    room_id TEXT NOT NULL,
    agent_id TEXT,
    task_id TEXT,
    payload TEXT NOT NULL DEFAULT '{}',
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);

CREATE TABLE IF NOT EXISTS shared_context (
    key TEXT NOT NULL,
    room_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (key, room_id)
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status, room_id);
CREATE INDEX IF NOT EXISTS idx_tasks_owner ON tasks(owner_agent_id);
CREATE INDEX IF NOT EXISTS idx_agents_room ON agents(room_id, status);
CREATE INDEX IF NOT EXISTS idx_events_room ON events(room_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_file_locks_agent ON file_locks(agent_id);
"""


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get a SQLite connection with WAL mode enabled.

    Args:
        db_path: Path to database file. Defaults to ~/.prowlrbot/warroom.db

    Returns:
        A configured sqlite3.Connection.
    """
    path = db_path or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)

    conn = sqlite3.connect(path, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Initialize the database with schema and return connection.

    Safe to call multiple times — uses CREATE IF NOT EXISTS.
    """
    conn = get_connection(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    logger.info("ProwlrHub database initialized at %s", db_path or DEFAULT_DB_PATH)
    return conn
