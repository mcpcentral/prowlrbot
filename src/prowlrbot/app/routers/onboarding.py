# -*- coding: utf-8 -*-
"""API endpoints for the onboarding wizard."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...constant import WORKING_DIR
from ...onboarding.wizard import (
    OnboardingManager,
    OnboardingProgress,
    OnboardingStep,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

_manager = OnboardingManager(db_path=WORKING_DIR / "onboarding.db")


@router.post("/start", response_model=OnboardingProgress)
async def start_onboarding(user_id: str = "default") -> OnboardingProgress:
    return _manager.start(user_id)


@router.get("/progress/{user_id}", response_model=OnboardingProgress)
async def get_progress(user_id: str) -> OnboardingProgress:
    progress = _manager.get_progress(user_id)
    if not progress:
        raise HTTPException(404, f"No onboarding progress for '{user_id}'")
    return progress


class StepAction(BaseModel):
    step: OnboardingStep


@router.post("/complete-step/{user_id}", response_model=OnboardingProgress)
async def complete_step(
    user_id: str,
    action: StepAction,
) -> OnboardingProgress:
    progress = _manager.complete_step(user_id, action.step)
    if not progress:
        raise HTTPException(404, f"No onboarding progress for '{user_id}'")
    return progress


@router.post("/skip-step/{user_id}", response_model=OnboardingProgress)
async def skip_step(user_id: str, action: StepAction) -> OnboardingProgress:
    progress = _manager.skip_step(user_id, action.step)
    if not progress:
        raise HTTPException(404, f"No onboarding progress for '{user_id}'")
    return progress


@router.put("/preferences/{user_id}", response_model=OnboardingProgress)
async def set_preferences(
    user_id: str,
    preferences: Dict[str, Any],
) -> OnboardingProgress:
    progress = _manager.set_preferences(user_id, preferences)
    if not progress:
        raise HTTPException(404, f"No onboarding progress for '{user_id}'")
    return progress


@router.post("/reset/{user_id}", response_model=OnboardingProgress)
async def reset_onboarding(user_id: str) -> OnboardingProgress:
    return _manager.reset(user_id)
