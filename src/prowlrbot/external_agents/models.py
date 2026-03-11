# -*- coding: utf-8 -*-
"""External agent data models."""

from __future__ import annotations

import uuid
from prowlrbot.compat import StrEnum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentBackendType(StrEnum):
    CLAUDE_CODE = "claude_code"
    CODEX = "codex"
    CUSTOM_CLI = "custom_cli"
    HTTP_API = "http_api"
    DOCKER = "docker"


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ExternalAgentConfig(BaseModel):
    """Configuration for an external agent backend."""

    id: str = Field(default_factory=lambda: f"ext_{uuid.uuid4().hex[:8]}")
    name: str
    backend_type: AgentBackendType
    command: str = ""  # CLI command or Docker image
    api_url: str = ""  # HTTP API endpoint
    api_key: str = ""  # API key (if needed)
    timeout_seconds: int = 300
    working_dir: str = ""
    environment: Dict[str, str] = Field(default_factory=dict)
    enabled: bool = True
    created_at: float = 0.0


class ExternalTask(BaseModel):
    """A task dispatched to an external agent."""

    id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    agent_id: str  # references ExternalAgentConfig.id
    prompt: str
    context: Dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus = TaskStatus.QUEUED
    result: str = ""
    error: str = ""
    started_at: float = 0.0
    completed_at: float = 0.0
    created_at: float = 0.0


class ExternalAgentStatus(BaseModel):
    """Health status of an external agent."""

    agent_id: str
    name: str
    backend_type: AgentBackendType
    available: bool = False
    last_check: float = 0.0
    error: str = ""
