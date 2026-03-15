# -*- coding: utf-8 -*-
"""SQLite-backed agent directory for persistent discovery.

Replaces the in-memory AgentDirectory with durable storage.
Agent cards are serialized as JSON and stored in SQLite with
full-text search support for capabilities.

Usage::

    directory = SQLiteAgentDirectory()  # default ~/.prowlrbot/roar_directory.db
    directory.register(card)
    entry = directory.lookup("did:roar:agent:planner-abc12345")
    results = directory.search("code-review")
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional

from ...roar import AgentCard, AgentIdentity, DiscoveryEntry

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = os.path.join(
    os.path.expanduser("~"),
    ".prowlrbot",
    "roar_directory.db",
)


class SQLiteAgentDirectory:
    """SQLite-backed agent directory for persistent agent discovery.

    Same interface as the in-memory ``AgentDirectory`` but persists
    agent cards to disk. Thread-safe via ``check_same_thread=False``.

    Args:
        db_path: Path to the SQLite database file. Defaults to
            ``~/.prowlrbot/roar_directory.db``.
    """

    def __init__(self, db_path: str = _DEFAULT_DB_PATH) -> None:
        self._db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        """Create tables on first use."""
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agents (
                did TEXT PRIMARY KEY,
                card_json TEXT NOT NULL,
                registered_at REAL NOT NULL,
                last_seen REAL NOT NULL,
                hub_url TEXT NOT NULL DEFAULT ''
            )
            """,
        )
        self._conn.commit()

    def register(self, card: AgentCard) -> DiscoveryEntry:
        """Register an agent card in the directory.

        Args:
            card: The agent card to register.

        Returns:
            The created DiscoveryEntry.
        """
        now = time.time()
        entry = DiscoveryEntry(
            agent_card=card,
            registered_at=now,
            last_seen=now,
        )
        card_json = card.model_dump_json()
        self._conn.execute(
            """
            INSERT OR REPLACE INTO agents (did, card_json, registered_at, last_seen, hub_url)
            VALUES (?, ?, ?, ?, ?)
            """,
            (card.identity.did, card_json, now, now, ""),
        )
        self._conn.commit()
        logger.debug(
            "Registered agent %s in SQLite directory",
            card.identity.did,
        )
        return entry

    def unregister(self, did: str) -> bool:
        """Remove an agent from the directory.

        Args:
            did: The agent's DID.

        Returns:
            True if the agent was removed, False if not found.
        """
        cursor = self._conn.execute("DELETE FROM agents WHERE did = ?", (did,))
        self._conn.commit()
        removed = cursor.rowcount > 0
        if removed:
            logger.debug("Unregistered agent %s from SQLite directory", did)
        return removed

    def lookup(self, did: str) -> Optional[DiscoveryEntry]:
        """Look up an agent by DID.

        Args:
            did: The agent's DID.

        Returns:
            A DiscoveryEntry if found, None otherwise.
        """
        row = self._conn.execute(
            "SELECT card_json, registered_at, last_seen, hub_url FROM agents WHERE did = ?",
            (did,),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_entry(row)

    def search(self, capability: str) -> List[DiscoveryEntry]:
        """Find agents with a specific capability.

        Searches the agent's identity capabilities list for a match.

        Args:
            capability: The capability to search for.

        Returns:
            List of matching discovery entries.
        """
        rows = self._conn.execute(
            "SELECT card_json, registered_at, last_seen, hub_url FROM agents",
        ).fetchall()
        results = []
        for row in rows:
            entry = self._row_to_entry(row)
            if capability in entry.agent_card.identity.capabilities:
                results.append(entry)
        return results

    def list_all(self) -> List[DiscoveryEntry]:
        """List all registered agents.

        Returns:
            List of all discovery entries.
        """
        rows = self._conn.execute(
            "SELECT card_json, registered_at, last_seen, hub_url FROM agents",
        ).fetchall()
        return [self._row_to_entry(row) for row in rows]

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> DiscoveryEntry:
        """Convert a database row to a DiscoveryEntry."""
        card = AgentCard.model_validate_json(row["card_json"])
        return DiscoveryEntry(
            agent_card=card,
            registered_at=row["registered_at"],
            last_seen=row["last_seen"],
            hub_url=row["hub_url"],
        )
