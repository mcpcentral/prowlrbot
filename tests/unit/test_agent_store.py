# -*- coding: utf-8 -*-
"""Tests for agent configuration storage."""

import pytest

from prowlrbot.agents.agent_store import AgentStore
from prowlrbot.agents.agent_config import AgentConfig, AvatarConfig


@pytest.fixture
def store(tmp_path):
    return AgentStore(base_dir=tmp_path / "agents")


def test_create_agent(store):
    config = AgentConfig(name="Test Bot")
    agent_id = store.create(config)
    assert agent_id is not None
    assert len(agent_id) > 0


def test_get_agent(store):
    config = AgentConfig(name="Test Bot", avatar=AvatarConfig(base="cat"))
    agent_id = store.create(config)
    retrieved = store.get(agent_id)
    assert retrieved is not None
    assert retrieved.name == "Test Bot"
    assert retrieved.avatar.base == "cat"


def test_list_agents(store):
    store.create(AgentConfig(name="Agent A"))
    store.create(AgentConfig(name="Agent B"))
    agents = store.list()
    assert len(agents) == 2


def test_update_agent(store):
    config = AgentConfig(name="Original")
    agent_id = store.create(config)
    config.name = "Updated"
    store.update(agent_id, config)
    retrieved = store.get(agent_id)
    assert retrieved.name == "Updated"


def test_delete_agent(store):
    agent_id = store.create(AgentConfig(name="Temp"))
    assert store.delete(agent_id) is True
    assert store.get(agent_id) is None


def test_get_nonexistent_returns_none(store):
    assert store.get("nonexistent-id") is None


def test_delete_nonexistent_returns_false(store):
    assert store.delete("nonexistent-id") is False
