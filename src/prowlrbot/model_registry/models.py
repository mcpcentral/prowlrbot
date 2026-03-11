# -*- coding: utf-8 -*-
"""Data models for the model registry."""

from __future__ import annotations

import uuid
from prowlrbot.compat import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ModelType(StrEnum):
    """Supported model types."""

    chat = "chat"
    embedding = "embedding"
    image = "image"
    audio = "audio"
    code = "code"
    multimodal = "multimodal"


class ModelCapability(StrEnum):
    """Capabilities a model may support."""

    text_generation = "text_generation"
    function_calling = "function_calling"
    vision = "vision"
    streaming = "streaming"
    json_mode = "json_mode"
    system_prompt = "system_prompt"
    tool_use = "tool_use"


class ModelEntry(BaseModel):
    """A single model registered in the registry."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    provider: str
    model_type: ModelType = ModelType.chat
    capabilities: list[ModelCapability] = Field(default_factory=list)
    context_window: int = 4096
    max_output_tokens: int = 4096
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    is_local: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    added_at: float = 0.0
    last_used: float = 0.0


class ModelComparison(BaseModel):
    """Side-by-side comparison of multiple models."""

    models: list[ModelEntry]
    comparison_matrix: dict[str, Any]
