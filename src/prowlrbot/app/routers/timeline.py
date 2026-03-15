# -*- coding: utf-8 -*-
"""FastAPI router for timeline and checkpoint endpoints."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ...constant import WORKING_DIR
from ...dashboard.timeline import TimelineManager

router = APIRouter(prefix="/timeline", tags=["timeline"])

_DB_PATH = WORKING_DIR / "timeline.db"

# Lazy singleton — created on first use so the DB file is only opened when
# the router is actually hit (avoids side-effects at import time).
_manager: Optional[TimelineManager] = None


def _get_manager() -> TimelineManager:
    global _manager  # noqa: PLW0603
    if _manager is None:
        _manager = TimelineManager(_DB_PATH)
    return _manager


# -- Request schemas --


class CreateCheckpointRequest(BaseModel):
    label: str
    state_snapshot: Dict[str, Any] = {}
    parent_id: Optional[str] = None


class ForkCheckpointRequest(BaseModel):
    new_label: str


# -- Endpoints --


@router.get("/{session_id}/checkpoints")
def list_checkpoints(session_id: str):
    """List all checkpoints for a session."""
    mgr = _get_manager()
    checkpoints = mgr.list_checkpoints(session_id)
    return [cp.model_dump(mode="json") for cp in checkpoints]


@router.post("/{session_id}/checkpoint", status_code=201)
def create_checkpoint(session_id: str, body: CreateCheckpointRequest):
    """Create a new checkpoint for a session."""
    mgr = _get_manager()
    cp = mgr.create_checkpoint(
        session_id=session_id,
        label=body.label,
        state_snapshot=body.state_snapshot,
        parent_id=body.parent_id,
    )
    return cp.model_dump(mode="json")


@router.post("/checkpoint/{checkpoint_id}/fork", status_code=201)
def fork_checkpoint(checkpoint_id: str, body: ForkCheckpointRequest):
    """Fork a new checkpoint from an existing one."""
    mgr = _get_manager()
    cp = mgr.fork_from_checkpoint(checkpoint_id, body.new_label)
    if cp is None:
        raise HTTPException(
            status_code=404,
            detail="Parent checkpoint not found",
        )
    return cp.model_dump(mode="json")


@router.delete("/checkpoint/{checkpoint_id}")
def delete_checkpoint(checkpoint_id: str):
    """Delete a checkpoint."""
    mgr = _get_manager()
    deleted = mgr.delete_checkpoint(checkpoint_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return {"deleted": True}


@router.get("/{session_id}/export")
def export_timeline(session_id: str):
    """Export the full timeline (checkpoints + events) for a session."""
    mgr = _get_manager()
    return mgr.export_timeline(session_id)
