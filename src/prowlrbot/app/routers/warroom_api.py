# -*- coding: utf-8 -*-
"""War Room API router — embeds the war room engine into the main FastAPI app.

This eliminates the need for a separate bridge server on port 8099.
The console frontend calls these endpoints via /api/warroom/*.
The standalone bridge (hub/bridge.py) remains available for cross-machine use.
"""

from __future__ import annotations

import json
import logging
import os
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request, WebSocket
from pydantic import BaseModel, Field

from ...hub.engine import WarRoomEngine
from ...hub.websocket import broadcast_ws, warroom_ws

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/warroom", tags=["warroom"])

# Lazily initialized singleton engine
_engine: WarRoomEngine | None = None


def _get_engine() -> WarRoomEngine:
    global _engine
    if _engine is None:
        db_path = os.environ.get("PROWLR_HUB_DB", None)
        _engine = WarRoomEngine(db_path)
        _engine.get_or_create_default_room()

        # Wire engine events to WebSocket broadcast
        import asyncio

        def _on_engine_event(event: dict):
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(broadcast_ws(event))
            except RuntimeError:
                pass

        _engine.set_event_callback(_on_engine_event)
        logger.info("War Room engine initialized")
    return _engine


# --- Request models ---


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    capabilities: List[str] = Field(default=["general"], max_length=20)


class ClaimRequest(BaseModel):
    task_id: str = Field(default="", max_length=64)
    title: str = Field(default="", max_length=512)
    file_scopes: List[str] = Field(default=[], max_length=50)
    description: str = Field(default="", max_length=8192)
    priority: str = Field(default="normal", max_length=16)


class UpdateRequest(BaseModel):
    task_id: str = Field(..., max_length=64)
    progress_note: str = Field(..., max_length=4096)


class CompleteRequest(BaseModel):
    task_id: str = Field(..., max_length=64)
    summary: str = Field(default="", max_length=8192)


class FailRequest(BaseModel):
    task_id: str = Field(..., max_length=64)
    reason: str = Field(default="", max_length=4096)


class LockRequest(BaseModel):
    path: str = Field(..., min_length=1, max_length=1024)


class ConflictRequest(BaseModel):
    paths: List[str] = Field(..., max_length=50)


class BroadcastRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4096)


class FindingRequest(BaseModel):
    key: str = Field(..., min_length=1, max_length=256)
    value: str = Field(..., max_length=65536)


# --- Path validation ---

_VALID_PRIORITIES = {"critical", "high", "normal", "low"}
_MAX_LIMIT = 500


def _validate_lock_path(path: str) -> str:
    if "\x00" in path:
        raise HTTPException(status_code=400, detail="Invalid path")
    if path.startswith("/") or path.startswith("\\"):
        raise HTTPException(
            status_code=400,
            detail="Absolute paths not allowed",
        )
    normalized = os.path.normpath(path)
    if normalized.startswith(".."):
        raise HTTPException(
            status_code=400,
            detail="Path traversal not allowed",
        )
    return normalized


def _clamp_limit(limit: int) -> int:
    return max(1, min(limit, _MAX_LIMIT))


# --- JSON API endpoints (consumed by console frontend) ---


@router.get("/agents")
async def api_agents():
    engine = _get_engine()
    room = engine.get_or_create_default_room()
    return engine.get_agents(room["room_id"])


@router.get("/board")
async def api_board(status: str = ""):
    engine = _get_engine()
    room = engine.get_or_create_default_room()
    tasks = engine.get_mission_board(room["room_id"])
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    return tasks


@router.get("/events")
async def api_events(limit: int = 50, event_type: str = ""):
    engine = _get_engine()
    room = engine.get_or_create_default_room()
    return engine.get_events(room["room_id"], _clamp_limit(limit), event_type)


@router.get("/context")
async def api_context(key: str = ""):
    engine = _get_engine()
    room = engine.get_or_create_default_room()
    return engine.get_context(room["room_id"], key)


@router.get("/conflicts")
async def api_conflicts():
    engine = _get_engine()
    room = engine.get_or_create_default_room()
    room_id = room["room_id"]
    rows = engine._conn.execute(
        """SELECT fl.*, a.name as agent_name
           FROM file_locks fl
           LEFT JOIN agents a ON fl.agent_id = a.agent_id
           WHERE fl.room_id=?
           ORDER BY fl.acquired_at DESC""",
        (room_id,),
    ).fetchall()
    return [dict(row) for row in rows]


@router.get("/health")
async def api_health():
    engine = _get_engine()
    room = engine.get_or_create_default_room()
    agents = engine.get_agents(room["room_id"])
    tasks = engine.get_mission_board(room["room_id"])
    return {
        "status": "ok",
        "room_id": room["room_id"],
        "agents": len(agents),
        "tasks": len(tasks),
    }


# --- State-changing endpoints ---


@router.post("/register")
async def register(req: RegisterRequest):
    engine = _get_engine()
    room = engine.get_or_create_default_room()
    return engine.register_agent(req.name, room["room_id"], req.capabilities)


@router.post("/heartbeat/{agent_id}")
async def heartbeat(agent_id: str):
    engine = _get_engine()
    engine.heartbeat(agent_id)
    return {"ok": True}


@router.post("/claim/{agent_id}")
async def claim_task(agent_id: str, req: ClaimRequest):
    engine = _get_engine()
    if req.priority not in _VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail="Invalid priority")
    room = engine.get_or_create_default_room()
    task_id = req.task_id
    if not task_id and req.title:
        task = engine.create_task(
            room["room_id"],
            req.title,
            description=req.description,
            file_scopes=req.file_scopes,
            priority=req.priority,
        )
        task_id = task["task_id"]
    result = engine.claim_task(task_id, agent_id, room["room_id"])
    if result.success:
        return {"success": True, "lock_token": result.lock_token}
    return {
        "success": False,
        "reason": result.reason,
        "conflicts": result.conflicts,
    }


@router.post("/update/{agent_id}")
async def update_task(agent_id: str, req: UpdateRequest):
    engine = _get_engine()
    engine.update_task(req.task_id, agent_id, req.progress_note)
    return {"ok": True}


@router.post("/complete/{agent_id}")
async def complete_task(agent_id: str, req: CompleteRequest):
    engine = _get_engine()
    ok = engine.complete_task(req.task_id, agent_id, req.summary)
    return {"ok": ok}


@router.post("/fail/{agent_id}")
async def fail_task(agent_id: str, req: FailRequest):
    engine = _get_engine()
    ok = engine.fail_task(req.task_id, agent_id, req.reason)
    return {"ok": ok}


@router.post("/lock/{agent_id}")
async def lock_file(agent_id: str, req: LockRequest):
    engine = _get_engine()
    safe_path = _validate_lock_path(req.path)
    room = engine.get_or_create_default_room()
    result = engine.lock_file(safe_path, agent_id, room["room_id"])
    if result.success:
        return {"success": True, "lock_token": result.lock_token}
    return {"success": False, "reason": result.reason, "owner": result.owner}


@router.post("/unlock/{agent_id}")
async def unlock_file(agent_id: str, req: LockRequest):
    engine = _get_engine()
    safe_path = _validate_lock_path(req.path)
    room = engine.get_or_create_default_room()
    ok = engine.unlock_file(safe_path, agent_id, room["room_id"])
    return {"ok": ok}


@router.post("/conflicts")
async def check_conflicts(req: ConflictRequest):
    engine = _get_engine()
    room = engine.get_or_create_default_room()
    return {"conflicts": engine.check_conflicts(req.paths, room["room_id"])}


@router.post("/broadcast/{agent_id}")
async def broadcast(agent_id: str, req: BroadcastRequest):
    engine = _get_engine()
    room = engine.get_or_create_default_room()
    engine.broadcast_status(room["room_id"], agent_id, req.message)
    return {"ok": True}


@router.post("/findings/{agent_id}")
async def share_finding(agent_id: str, req: FindingRequest):
    engine = _get_engine()
    room = engine.get_or_create_default_room()
    engine.set_context(room["room_id"], agent_id, req.key, req.value)
    return {"ok": True}
