# -*- coding: utf-8 -*-
"""Onboarding wizard — tracks setup progress and guides users."""

from __future__ import annotations

import json
import sqlite3
import time
from prowlrbot.compat import StrEnum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class OnboardingStep(StrEnum):
    WELCOME = "welcome"
    PROVIDER_SETUP = "provider_setup"
    FIRST_AGENT = "first_agent"
    CHANNEL_CONNECT = "channel_connect"
    SKILL_INSTALL = "skill_install"
    FIRST_CHAT = "first_chat"
    CUSTOMIZE = "customize"
    COMPLETE = "complete"


STEP_ORDER = list(OnboardingStep)


class StepInfo(BaseModel):
    """Information about an onboarding step."""

    step: OnboardingStep
    title: str
    description: str
    completed: bool = False
    skipped: bool = False
    completed_at: float = 0.0


STEP_DETAILS: Dict[OnboardingStep, Dict[str, str]] = {
    OnboardingStep.WELCOME: {
        "title": "Welcome to ProwlrBot",
        "description": "Get an overview of what ProwlrBot can do.",
    },
    OnboardingStep.PROVIDER_SETUP: {
        "title": "Set Up AI Provider",
        "description": "Configure at least one AI provider (OpenAI, Anthropic, Groq, etc.).",
    },
    OnboardingStep.FIRST_AGENT: {
        "title": "Create Your First Agent",
        "description": "Set up your first AI agent with a name, personality, and skills.",
    },
    OnboardingStep.CHANNEL_CONNECT: {
        "title": "Connect a Channel",
        "description": "Connect a communication channel (Discord, Telegram, DingTalk, etc.).",
    },
    OnboardingStep.SKILL_INSTALL: {
        "title": "Install a Skill",
        "description": "Add skills to extend your agent's capabilities.",
    },
    OnboardingStep.FIRST_CHAT: {
        "title": "Send Your First Message",
        "description": "Have your first conversation with your agent.",
    },
    OnboardingStep.CUSTOMIZE: {
        "title": "Customize Your Setup",
        "description": "Personalize your agent's avatar, autonomy level, and preferences.",
    },
    OnboardingStep.COMPLETE: {
        "title": "Setup Complete",
        "description": "You're all set! Explore the full ProwlrBot experience.",
    },
}


class OnboardingProgress(BaseModel):
    """User's onboarding progress."""

    user_id: str
    current_step: OnboardingStep = OnboardingStep.WELCOME
    steps: List[StepInfo] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    started_at: float = 0.0
    completed_at: float = 0.0


class OnboardingManager:
    """Manages onboarding progress for users."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS onboarding (
                user_id TEXT PRIMARY KEY,
                current_step TEXT DEFAULT 'welcome',
                steps TEXT DEFAULT '[]',
                preferences TEXT DEFAULT '{}',
                started_at REAL NOT NULL,
                completed_at REAL DEFAULT 0
            );
        """)
        self._conn.commit()

    def start(self, user_id: str) -> OnboardingProgress:
        """Start onboarding for a user."""
        now = time.time()
        steps = [StepInfo(step=s, **STEP_DETAILS[s]) for s in STEP_ORDER]
        progress = OnboardingProgress(
            user_id=user_id,
            current_step=OnboardingStep.WELCOME,
            steps=steps,
            started_at=now,
        )
        self._save(progress)
        return progress

    def get_progress(self, user_id: str) -> Optional[OnboardingProgress]:
        row = self._conn.execute(
            "SELECT * FROM onboarding WHERE user_id = ?", (user_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_progress(row)

    def complete_step(
        self, user_id: str, step: OnboardingStep
    ) -> Optional[OnboardingProgress]:
        """Mark a step as completed and advance to next."""
        progress = self.get_progress(user_id)
        if not progress:
            return None

        for s in progress.steps:
            if s.step == step:
                s.completed = True
                s.completed_at = time.time()
                break

        # Advance to next uncompleted step
        current_idx = STEP_ORDER.index(step)
        for next_step in STEP_ORDER[current_idx + 1 :]:
            step_info = next((s for s in progress.steps if s.step == next_step), None)
            if step_info and not step_info.completed and not step_info.skipped:
                progress.current_step = next_step
                break
        else:
            progress.current_step = OnboardingStep.COMPLETE
            progress.completed_at = time.time()

        self._save(progress)
        return progress

    def skip_step(
        self, user_id: str, step: OnboardingStep
    ) -> Optional[OnboardingProgress]:
        """Skip a step."""
        progress = self.get_progress(user_id)
        if not progress:
            return None

        for s in progress.steps:
            if s.step == step:
                s.skipped = True
                break

        # Advance to next
        current_idx = STEP_ORDER.index(step)
        for next_step in STEP_ORDER[current_idx + 1 :]:
            step_info = next((s for s in progress.steps if s.step == next_step), None)
            if step_info and not step_info.completed and not step_info.skipped:
                progress.current_step = next_step
                break
        else:
            progress.current_step = OnboardingStep.COMPLETE
            progress.completed_at = time.time()

        self._save(progress)
        return progress

    def set_preferences(
        self, user_id: str, preferences: Dict[str, Any]
    ) -> Optional[OnboardingProgress]:
        progress = self.get_progress(user_id)
        if not progress:
            return None
        progress.preferences.update(preferences)
        self._save(progress)
        return progress

    def reset(self, user_id: str) -> OnboardingProgress:
        """Reset onboarding for a user."""
        self._conn.execute("DELETE FROM onboarding WHERE user_id = ?", (user_id,))
        self._conn.commit()
        return self.start(user_id)

    def _save(self, progress: OnboardingProgress) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO onboarding "
            "(user_id, current_step, steps, preferences, started_at, completed_at) "
            "VALUES (?,?,?,?,?,?)",
            (
                progress.user_id,
                progress.current_step,
                json.dumps([s.model_dump() for s in progress.steps]),
                json.dumps(progress.preferences),
                progress.started_at,
                progress.completed_at,
            ),
        )
        self._conn.commit()

    @staticmethod
    def _row_to_progress(row: sqlite3.Row) -> OnboardingProgress:
        steps_data = json.loads(row["steps"]) if row["steps"] else []
        return OnboardingProgress(
            user_id=row["user_id"],
            current_step=OnboardingStep(row["current_step"]),
            steps=[StepInfo(**s) for s in steps_data],
            preferences=json.loads(row["preferences"]) if row["preferences"] else {},
            started_at=row["started_at"],
            completed_at=row["completed_at"],
        )

    def close(self) -> None:
        self._conn.close()
