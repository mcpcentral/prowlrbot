# -*- coding: utf-8 -*-
"""API endpoints for session replay."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...constant import WORKING_DIR
from ...replay.recorder import (
    EventType,
    ReplayEvent,
    ReplaySession,
    ReplaySessionDetail,
    SessionRecorder,
)

router = APIRouter(prefix="/replay", tags=["replay"])

_recorder = SessionRecorder(db_path=WORKING_DIR / "replay.db")


class StartRecordingRequest(BaseModel):
    session_id: str
    agent_id: str = ""
    title: str = ""


@router.post("/start", response_model=ReplaySession)
async def start_recording(req: StartRecordingRequest) -> ReplaySession:
    return _recorder.start_recording(req.session_id, req.agent_id, req.title)


class RecordEventRequest(BaseModel):
    event_type: EventType
    content: str = ""
    metadata: Dict[str, Any] = {}
    agent_id: str = ""


@router.post("/{replay_id}/events", response_model=ReplayEvent)
async def record_event(replay_id: str, req: RecordEventRequest) -> ReplayEvent:
    session = _recorder.get_session(replay_id)
    if not session:
        raise HTTPException(404, f"Replay session '{replay_id}' not found")
    return _recorder.record_event(
        replay_id,
        req.event_type,
        req.content,
        req.metadata,
        req.agent_id,
    )


@router.post("/{replay_id}/stop", response_model=ReplaySession)
async def stop_recording(replay_id: str) -> ReplaySession:
    session = _recorder.stop_recording(replay_id)
    if not session:
        raise HTTPException(404, f"Replay session '{replay_id}' not found")
    return session


@router.get("/sessions", response_model=List[ReplaySession])
async def list_sessions(limit: int = 50) -> List[ReplaySession]:
    return _recorder.list_sessions(limit=limit)


@router.get("/{replay_id}", response_model=ReplaySessionDetail)
async def get_session(replay_id: str) -> ReplaySessionDetail:
    detail = _recorder.get_session_detail(replay_id)
    if not detail:
        raise HTTPException(404, f"Replay session '{replay_id}' not found")
    return detail


@router.get("/{replay_id}/events", response_model=List[ReplayEvent])
async def get_events_in_range(
    replay_id: str,
    start_ms: int = 0,
    end_ms: int = 0,
) -> List[ReplayEvent]:
    return _recorder.get_events_in_range(replay_id, start_ms, end_ms)


@router.delete("/{replay_id}")
async def delete_session(replay_id: str) -> Dict[str, str]:
    if not _recorder.delete_session(replay_id):
        raise HTTPException(404, f"Replay session '{replay_id}' not found")
    return {"status": "deleted"}
