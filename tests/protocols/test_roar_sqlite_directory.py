# -*- coding: utf-8 -*-
"""Tests for SQLite-backed agent directory."""

from __future__ import annotations

import os
import tempfile
import unittest

from prowlrbot.protocols.roar import AgentCard, AgentIdentity, DiscoveryEntry
from prowlrbot.protocols.sdk.discovery.sqlite_directory import (
    SQLiteAgentDirectory,
)


def _make_card(
    name: str,
    capabilities: list = None,
    skills: list = None,
) -> AgentCard:
    identity = AgentIdentity(
        display_name=name,
        capabilities=capabilities or [],
    )
    return AgentCard(
        identity=identity,
        description=f"{name} agent",
        skills=skills or [],
        endpoints={"http": f"http://localhost:8089/{name}"},
    )


class TestSQLiteAgentDirectory(unittest.TestCase):
    """Tests for SQLiteAgentDirectory persistence and CRUD."""

    def setUp(self):
        self._tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmpfile.close()
        self.db_path = self._tmpfile.name
        self.directory = SQLiteAgentDirectory(db_path=self.db_path)

    def tearDown(self):
        self.directory.close()
        os.unlink(self.db_path)

    def test_register_and_lookup(self):
        card = _make_card("planner")
        entry = self.directory.register(card)
        assert entry is not None
        assert entry.agent_card.identity.display_name == "planner"

        found = self.directory.lookup(card.identity.did)
        assert found is not None
        assert found.agent_card.identity.display_name == "planner"

    def test_lookup_missing(self):
        found = self.directory.lookup("did:roar:agent:nonexistent-12345678")
        assert found is None

    def test_unregister(self):
        card = _make_card("removable")
        self.directory.register(card)
        assert self.directory.unregister(card.identity.did) is True
        assert self.directory.lookup(card.identity.did) is None

    def test_unregister_missing(self):
        assert self.directory.unregister("did:roar:agent:nope-12345678") is False

    def test_search_by_capability(self):
        card1 = _make_card("reviewer", capabilities=["code-review", "testing"])
        card2 = _make_card("deployer", capabilities=["deploy", "monitoring"])
        self.directory.register(card1)
        self.directory.register(card2)

        results = self.directory.search("code-review")
        assert len(results) == 1
        assert results[0].agent_card.identity.display_name == "reviewer"

    def test_search_no_results(self):
        card = _make_card("agent", capabilities=["coding"])
        self.directory.register(card)
        results = self.directory.search("nonexistent")
        assert len(results) == 0

    def test_list_all(self):
        self.directory.register(_make_card("agent-1"))
        self.directory.register(_make_card("agent-2"))
        self.directory.register(_make_card("agent-3"))
        assert len(self.directory.list_all()) == 3

    def test_list_all_empty(self):
        assert len(self.directory.list_all()) == 0

    def test_register_replaces_existing(self):
        card = _make_card("updatable")
        self.directory.register(card)
        # Re-register with same DID but different description
        card2 = AgentCard(
            identity=card.identity,
            description="updated description",
            skills=["new-skill"],
        )
        self.directory.register(card2)

        found = self.directory.lookup(card.identity.did)
        assert found is not None
        assert found.agent_card.description == "updated description"
        assert len(self.directory.list_all()) == 1

    def test_persistence_across_connections(self):
        """Data survives closing and reopening the database."""
        card = _make_card("persistent")
        self.directory.register(card)
        did = card.identity.did
        self.directory.close()

        # Reopen
        directory2 = SQLiteAgentDirectory(db_path=self.db_path)
        found = directory2.lookup(did)
        assert found is not None
        assert found.agent_card.identity.display_name == "persistent"
        assert found.agent_card.description == "persistent agent"
        directory2.close()

    def test_card_fields_preserved(self):
        """All AgentCard fields round-trip through SQLite."""
        identity = AgentIdentity(
            display_name="full-card",
            agent_type="tool",
            capabilities=["analyze", "report"],
            version="2.0",
        )
        card = AgentCard(
            identity=identity,
            description="A fully specified card",
            skills=["skill-a", "skill-b"],
            channels=["http", "ws"],
            endpoints={"http": "http://example.com", "ws": "ws://example.com"},
            metadata={"tier": "premium"},
        )
        self.directory.register(card)

        found = self.directory.lookup(card.identity.did)
        assert found is not None
        fc = found.agent_card
        assert fc.identity.agent_type == "tool"
        assert fc.identity.capabilities == ["analyze", "report"]
        assert fc.identity.version == "2.0"
        assert fc.description == "A fully specified card"
        assert fc.skills == ["skill-a", "skill-b"]
        assert fc.channels == ["http", "ws"]
        assert fc.endpoints == {
            "http": "http://example.com",
            "ws": "ws://example.com",
        }
        assert fc.metadata == {"tier": "premium"}


if __name__ == "__main__":
    unittest.main()
