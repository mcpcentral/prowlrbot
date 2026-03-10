# -*- coding: utf-8 -*-
"""Tests for per-agent configuration model."""

from prowlrbot.agents.agent_config import (
    AgentConfig,
    AvatarConfig,
    SoulConfig,
    MemoryConfig,
    ToolPermissions,
    ToolsConfig,
    AutonomyConfig,
    AgentVerseConfig,
)


def test_default_agent_config():
    config = AgentConfig(name="Test Agent")
    assert config.name == "Test Agent"
    assert config.avatar.base == "robot"
    assert config.soul.tone == "helpful"
    assert config.memory.type == "persistent"
    assert config.autonomy.default_level == "guide"


def test_avatar_config():
    avatar = AvatarConfig(base="cat", color="#FF6B35", accessories=["hat"])
    assert avatar.base == "cat"
    assert avatar.color == "#FF6B35"
    assert len(avatar.accessories) == 1


def test_soul_config():
    soul = SoulConfig(
        personality="Analytical and thorough",
        tone="professional",
    )
    assert soul.personality == "Analytical and thorough"


def test_tools_config_with_permissions():
    tools = ToolsConfig(
        enabled=["shell", "file_io"],
        disabled=["browser"],
        permissions={
            "shell": ToolPermissions(
                allowed_commands=["ls", "grep"],
                blocked_commands=["rm"],
            )
        },
    )
    assert "shell" in tools.enabled
    assert "browser" in tools.disabled
    assert "ls" in tools.permissions["shell"].allowed_commands


def test_autonomy_config():
    autonomy = AutonomyConfig(
        default_level="delegate",
        escalation_triggers=["file deletion"],
    )
    assert autonomy.default_level == "delegate"


def test_agent_config_to_dict():
    config = AgentConfig(name="Test", avatar=AvatarConfig(base="owl"))
    d = config.model_dump()
    assert d["name"] == "Test"
    assert d["avatar"]["base"] == "owl"


def test_agent_config_from_dict():
    data = {
        "name": "Research Bot",
        "avatar": {"base": "fox", "color": "#00FF00"},
        "soul": {"personality": "Curious researcher"},
        "model": {"preferred": "claude-opus-4-6"},
    }
    config = AgentConfig(**data)
    assert config.name == "Research Bot"
    assert config.avatar.base == "fox"
    assert config.soul.personality == "Curious researcher"


def test_agentverse_config():
    av = AgentVerseConfig(
        visible=True,
        home_zone="workshop",
        guild="research_guild",
    )
    assert av.visible is True
    assert av.home_zone == "workshop"
