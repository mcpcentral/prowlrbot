# -*- coding: utf-8 -*-
"""Data models for the graduated autonomy control system."""

import time
import uuid
from prowlrbot.compat import StrEnum
from typing import Dict, List

from pydantic import BaseModel, Field


class AutonomyLevel(StrEnum):
    """Graduated autonomy levels for agent operation.

    - **watch**: Agent suggests, human approves everything.
    - **guide**: Agent acts on routine tasks, asks for novel ones.
    - **delegate**: Agent handles most tasks, escalates edge cases.
    - **autonomous**: Full autonomy, only reports results.
    """

    WATCH = "watch"
    GUIDE = "guide"
    DELEGATE = "delegate"
    AUTONOMOUS = "autonomous"


class EscalationReason(StrEnum):
    """Reasons an action may be escalated for human review."""

    NOVEL_TASK = "novel_task"
    HIGH_RISK = "high_risk"
    COST_THRESHOLD = "cost_threshold"
    ERROR_RATE = "error_rate"
    USER_REQUEST = "user_request"
    POLICY_VIOLATION = "policy_violation"


class AutonomyPolicy(BaseModel):
    """Per-agent autonomy policy controlling what an agent may do."""

    agent_id: str
    level: AutonomyLevel = AutonomyLevel.WATCH
    max_cost_per_action: float = 0.10
    max_actions_per_hour: int = 10
    allowed_tools: List[str] = Field(
        default_factory=list,
        description="Tool names the agent may use. Empty list means all allowed.",
    )
    blocked_tools: List[str] = Field(
        default_factory=list,
        description="Tool names explicitly blocked regardless of level.",
    )
    require_approval_for: List[str] = Field(
        default_factory=list,
        description="Tool names that always require human approval.",
    )
    escalation_contacts: List[str] = Field(
        default_factory=list,
        description="Contact identifiers to notify on escalation.",
    )
    updated_at: float = Field(default=0)


class ActionDecision(BaseModel):
    """Result of evaluating whether an action is approved."""

    action: str
    approved: bool
    reason: str
    escalated: bool


class EscalationEvent(BaseModel):
    """Record of an action that was escalated for human review."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    reason: EscalationReason
    action: str
    context: Dict = Field(default_factory=dict)
    resolved: bool = False
    created_at: float = Field(default_factory=time.time)
