# -*- coding: utf-8 -*-
"""API endpoints for gamification — XP, levels, achievements, leaderboards."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

from ...constant import WORKING_DIR
from ...gamification.models import (
    Achievement,
    LeaderboardEntry,
    LevelInfo,
    XPGain,
)
from ...gamification.xp_tracker import XPTracker

router = APIRouter(prefix="/gamification", tags=["gamification"])

_tracker = XPTracker(db_path=WORKING_DIR / "gamification.db")


class AwardXPRequest(BaseModel):
    entity_id: str
    entity_type: str = "user"
    amount: int
    category: str
    reason: str


@router.post("/xp", response_model=XPGain)
async def award_xp(req: AwardXPRequest) -> XPGain:
    """Award XP to a user or agent."""
    return _tracker.award_xp(
        entity_id=req.entity_id,
        amount=req.amount,
        category=req.category,
        reason=req.reason,
        entity_type=req.entity_type,
    )


@router.get("/level/{entity_id}", response_model=LevelInfo)
async def get_level(entity_id: str, entity_type: str = "user") -> LevelInfo:
    """Get level info for a user or agent."""
    return _tracker.get_level_info(entity_id, entity_type)


@router.get("/xp/{entity_id}/history", response_model=List[XPGain])
async def get_xp_history(
    entity_id: str,
    entity_type: str = "user",
    limit: int = 50,
) -> List[XPGain]:
    """Get XP history for a user or agent."""
    return _tracker.get_xp_history(entity_id, entity_type, limit)


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    entity_type: str = "user",
    limit: int = 20,
) -> List[LeaderboardEntry]:
    """Get the leaderboard."""
    return _tracker.get_leaderboard(entity_type, limit)


@router.get("/achievements", response_model=List[Achievement])
async def list_achievements() -> List[Achievement]:
    """List all available achievements."""
    return _tracker.list_achievements()


@router.get("/achievements/{entity_id}")
async def get_unlocked_achievements(entity_id: str) -> List[Dict[str, Any]]:
    """Get unlocked achievements for an entity."""
    unlocked = _tracker.get_unlocked(entity_id)
    result = []
    for u in unlocked:
        defn = _tracker.get_achievement_def(u.achievement_id)
        result.append(
            {
                "achievement_id": u.achievement_id,
                "unlocked_at": u.unlocked_at,
                "name": defn.name if defn else u.achievement_id,
                "description": defn.description if defn else "",
                "badge": defn.badge if defn else "",
            },
        )
    return result


class UnlockRequest(BaseModel):
    entity_id: str
    achievement_id: str


@router.post("/achievements/unlock")
async def unlock_achievement(req: UnlockRequest) -> Dict[str, Any]:
    """Unlock an achievement for an entity."""
    result = _tracker.unlock_achievement(req.entity_id, req.achievement_id)
    if result is None:
        return {"status": "already_unlocked"}
    return {
        "status": "unlocked",
        "achievement_id": result.achievement_id,
        "unlocked_at": result.unlocked_at,
    }
