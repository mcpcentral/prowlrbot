# -*- coding: utf-8 -*-
"""Graduated autonomy control API endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from prowlrbot.autonomy.controller import AutonomyController
from prowlrbot.autonomy.models import AutonomyPolicy

router = APIRouter(prefix="/autonomy", tags=["autonomy"])


def _get_controller() -> AutonomyController:
    """Return a short-lived controller handle.

    Each request opens its own connection so we avoid threading issues
    with SQLite.  WAL mode ensures readers do not block writers.
    """
    return AutonomyController()


# ------------------------------------------------------------------
# Request schemas
# ------------------------------------------------------------------


class EvaluateRequest(BaseModel):
    """Body for the POST /evaluate endpoint."""

    agent_id: str
    action: str
    tool_name: str
    estimated_cost: float = 0.0


# ------------------------------------------------------------------
# Policy endpoints
# ------------------------------------------------------------------


@router.put("/policies/{agent_id}")
async def set_policy(agent_id: str, policy: AutonomyPolicy):
    """Create or update the autonomy policy for an agent."""
    policy.agent_id = agent_id
    ctrl = _get_controller()
    try:
        result = ctrl.set_policy(policy)
        return result.model_dump()
    finally:
        ctrl.close()


@router.get("/policies/{agent_id}")
async def get_policy(agent_id: str):
    """Get the autonomy policy for an agent."""
    ctrl = _get_controller()
    try:
        policy = ctrl.get_policy(agent_id)
        if policy is None:
            raise HTTPException(status_code=404, detail="Policy not found")
        return policy.model_dump()
    finally:
        ctrl.close()


@router.get("/policies")
async def list_policies():
    """List all autonomy policies."""
    ctrl = _get_controller()
    try:
        policies = ctrl.list_policies()
        return [p.model_dump() for p in policies]
    finally:
        ctrl.close()


@router.delete("/policies/{agent_id}")
async def delete_policy(agent_id: str):
    """Delete the autonomy policy for an agent."""
    ctrl = _get_controller()
    try:
        deleted = ctrl.delete_policy(agent_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Policy not found")
        return {"deleted": True}
    finally:
        ctrl.close()


# ------------------------------------------------------------------
# Evaluation endpoint
# ------------------------------------------------------------------


@router.post("/evaluate")
async def evaluate_action(req: EvaluateRequest):
    """Evaluate whether an action should be approved for an agent."""
    ctrl = _get_controller()
    try:
        decision = ctrl.evaluate_action(
            agent_id=req.agent_id,
            action=req.action,
            tool_name=req.tool_name,
            estimated_cost=req.estimated_cost,
        )
        return decision.model_dump()
    finally:
        ctrl.close()


# ------------------------------------------------------------------
# Escalation endpoints
# ------------------------------------------------------------------


@router.get("/escalations/{agent_id}")
async def list_escalations(
    agent_id: str,
    resolved: Optional[bool] = Query(
        None,
        description="Filter by resolution status",
    ),
):
    """List escalation events for an agent."""
    ctrl = _get_controller()
    try:
        events = ctrl.list_escalations(agent_id=agent_id, resolved=resolved)
        return [e.model_dump() for e in events]
    finally:
        ctrl.close()


@router.put("/escalations/{escalation_id}/resolve")
async def resolve_escalation(escalation_id: str):
    """Mark an escalation as resolved."""
    ctrl = _get_controller()
    try:
        resolved = ctrl.resolve_escalation(escalation_id)
        if not resolved:
            raise HTTPException(
                status_code=404,
                detail="Escalation not found or already resolved",
            )
        return {"resolved": True}
    finally:
        ctrl.close()
