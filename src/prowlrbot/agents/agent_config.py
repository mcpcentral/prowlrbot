# -*- coding: utf-8 -*-
"""Per-agent configuration model."""

from typing import Dict, List

from pydantic import BaseModel, Field


class AvatarConfig(BaseModel):
    """Agent avatar configuration for dashboard and AgentVerse."""

    base: str = Field(
        default="robot",
        description="Base avatar: cat, dog, fox, owl, robot, dragon, custom",
    )
    color: str = Field(default="#6B5CE7", description="Primary color hex")
    accessories: List[str] = Field(
        default_factory=list,
        description="Avatar accessories",
    )
    mood: str = Field(
        default="neutral",
        description="Current mood (auto-derived or manual)",
    )
    level: int = Field(default=1, description="XP level from completed tasks")
    reputation: float = Field(
        default=0.0,
        description="Community reputation score",
    )


class SoulConfig(BaseModel):
    """Agent personality and behavioral configuration."""

    personality: str = Field(
        default="Helpful and knowledgeable",
        description="Core personality traits",
    )
    tone: str = Field(default="helpful", description="Communication tone")
    language: str = Field(default="en", description="Primary language")
    soul_file: str = Field(
        default="SOUL.md",
        description="Personality document filename",
    )
    profile_file: str = Field(
        default="PROFILE.md",
        description="Background and knowledge areas",
    )
    agents_file: str = Field(
        default="AGENTS.md",
        description="Behavioral instructions",
    )


class MemoryConfig(BaseModel):
    """Agent memory configuration."""

    type: str = Field(
        default="persistent",
        description="Memory type: persistent, session-only, shared",
    )
    max_tokens: int = Field(
        default=50000,
        description="Memory budget before compaction",
    )
    compaction_strategy: str = Field(
        default="summarize",
        description="Strategy: summarize, prune, archive",
    )
    shared_with: List[str] = Field(
        default_factory=list,
        description="Agent IDs sharing this memory pool",
    )
    knowledge_bases: List[str] = Field(
        default_factory=list,
        description="Marketplace knowledge base IDs",
    )


class ToolPermissions(BaseModel):
    """Per-tool permission configuration."""

    allowed_commands: List[str] = Field(default_factory=list)
    blocked_commands: List[str] = Field(default_factory=list)
    allowed_paths: List[str] = Field(default_factory=list)
    blocked_paths: List[str] = Field(default_factory=list)


class ToolsConfig(BaseModel):
    """Agent tools configuration."""

    enabled: List[str] = Field(
        default_factory=lambda: [
            "shell",
            "file_io",
            "browser",
            "memory_search",
            "send_file",
        ],
    )
    disabled: List[str] = Field(default_factory=list)
    custom_tools: List[str] = Field(
        default_factory=list,
        description="Marketplace tool IDs",
    )
    permissions: Dict[str, ToolPermissions] = Field(default_factory=dict)


class ModelConfig(BaseModel):
    """Agent model/inference configuration."""

    preferred: str = Field(default="", description="Preferred model ID")
    fallback_chain: List[str] = Field(
        default_factory=list,
        description="Fallback model chain",
    )
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=4096)


class AutonomyConfig(BaseModel):
    """Agent autonomy level configuration."""

    default_level: str = Field(
        default="guide",
        description="Default: watch, guide, delegate, autonomous",
    )
    escalation_triggers: List[str] = Field(
        default_factory=lambda: ["file deletion", "external API calls"],
        description="Actions that trigger escalation to human",
    )
    auto_checkpoint: bool = Field(
        default=True,
        description="Auto-create checkpoints at key moments",
    )


class AgentVerseConfig(BaseModel):
    """Agent presence in AgentVerse virtual world."""

    visible: bool = Field(default=False, description="Show in AgentVerse")
    home_zone: str = Field(default="town_square", description="Default zone")
    guild: str = Field(default="", description="Guild membership")
    trading_enabled: bool = Field(default=False)
    battle_enabled: bool = Field(default=False)


class AgentConfig(BaseModel):
    """Complete per-agent configuration."""

    name: str = Field(description="Agent display name")
    avatar: AvatarConfig = Field(default_factory=AvatarConfig)
    soul: SoulConfig = Field(default_factory=SoulConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    skills: List[str] = Field(
        default_factory=list,
        description="Enabled skill IDs",
    )
    model: ModelConfig = Field(default_factory=ModelConfig)
    autonomy: AutonomyConfig = Field(default_factory=AutonomyConfig)
    channels: List[str] = Field(default_factory=lambda: ["console"])
    agentverse: AgentVerseConfig = Field(default_factory=AgentVerseConfig)
