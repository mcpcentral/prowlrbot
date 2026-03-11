# -*- coding: utf-8 -*-
"""AutoResearch data models."""

from __future__ import annotations

import uuid
from prowlrbot.compat import StrEnum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ResearchStatus(StrEnum):
    PLANNING = "planning"
    GATHERING = "gathering"
    ANALYZING = "analyzing"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"


class SourceType(StrEnum):
    WEB = "web"
    PAPER = "paper"
    CODE = "code"
    DOCUMENT = "document"
    API = "api"
    MANUAL = "manual"


class Source(BaseModel):
    """A single research source."""

    id: str = Field(default_factory=lambda: f"src_{uuid.uuid4().hex[:8]}")
    source_type: SourceType = SourceType.WEB
    url: str = ""
    title: str = ""
    content: str = ""
    summary: str = ""
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    gathered_at: float = 0.0


class ResearchFinding(BaseModel):
    """A key finding from analysis."""

    claim: str
    evidence: List[str] = Field(default_factory=list)  # source IDs
    confidence: float = 0.0  # 0-1
    category: str = ""


class ResearchProject(BaseModel):
    """A research project with topic, sources, and findings."""

    id: str = Field(default_factory=lambda: f"research_{uuid.uuid4().hex[:8]}")
    topic: str
    objective: str = ""
    search_queries: List[str] = Field(default_factory=list)
    sources: List[Source] = Field(default_factory=list)
    findings: List[ResearchFinding] = Field(default_factory=list)
    synthesis: str = ""  # Final synthesized report
    status: ResearchStatus = ResearchStatus.PLANNING
    max_sources: int = 20
    created_at: float = 0.0
    updated_at: float = 0.0


class ResearchSummary(BaseModel):
    """Brief summary of a research project."""

    id: str
    topic: str
    status: ResearchStatus
    source_count: int = 0
    finding_count: int = 0
    created_at: float = 0.0
