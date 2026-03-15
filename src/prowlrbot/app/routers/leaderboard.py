# -*- coding: utf-8 -*-
"""API endpoints for model leaderboard and benchmarking."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ...benchmarks.leaderboard import (
    BenchmarkResult,
    BenchmarkSuite,
    ModelLeaderboard,
    ModelRanking,
)
from ...constant import WORKING_DIR

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

_leaderboard = ModelLeaderboard(db_path=WORKING_DIR / "leaderboard.db")


@router.get("/rankings", response_model=List[ModelRanking])
async def get_rankings(
    benchmark: Optional[str] = None,
    limit: int = 20,
) -> List[ModelRanking]:
    """Get model rankings, optionally filtered by benchmark category."""
    return _leaderboard.get_leaderboard(
        benchmark=benchmark,
        limit=min(limit, 100),
    )


@router.get("/categories", response_model=List[str])
async def get_categories() -> List[str]:
    """Get all benchmark categories."""
    return _leaderboard.get_categories()


@router.get("/model/{model}/history", response_model=List[BenchmarkResult])
async def get_model_history(
    model: str,
    limit: int = 50,
) -> List[BenchmarkResult]:
    """Get benchmark history for a model."""
    return _leaderboard.get_model_history(model, limit=min(limit, 200))


class RecordResultRequest(BaseModel):
    model: str
    benchmark: str
    score: float
    latency_ms: int = 0
    cost_usd: float = 0.0
    details: Dict[str, Any] = {}


@router.post("/results")
async def record_result(req: RecordResultRequest) -> Dict[str, Any]:
    """Record a benchmark result."""
    result = BenchmarkResult(
        model=req.model,
        benchmark=req.benchmark,
        score=req.score,
        latency_ms=req.latency_ms,
        cost_usd=req.cost_usd,
        details=req.details,
    )
    row_id = _leaderboard.record_result(result)
    return {"id": row_id, "status": "recorded"}


@router.get("/suites", response_model=List[BenchmarkSuite])
async def list_suites() -> List[BenchmarkSuite]:
    """List benchmark suites."""
    return _leaderboard.list_suites()


@router.post("/suites")
async def create_suite(suite: BenchmarkSuite) -> Dict[str, str]:
    """Create or update a benchmark suite."""
    _leaderboard.save_suite(suite)
    return {"status": "saved", "id": suite.id}
