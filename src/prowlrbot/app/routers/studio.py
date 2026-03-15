# -*- coding: utf-8 -*-
"""Studio integration API endpoints."""

from __future__ import annotations

import asyncio
import json
import time
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from prowlrbot.auth.middleware import get_current_user

router = APIRouter(prefix="/studio", tags=["studio"])


class StudioHealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float


class AgentSummary(BaseModel):
    id: str
    name: str
    description: str
    status: str
    capabilities: list[str]
    model: str | None = None
    provider: str | None = None


class AgentRunRequest(BaseModel):
    query: str
    autonomy: str = "delegate"
    timeout_s: int = 300


class AgentRunResponse(BaseModel):
    run_id: str
    agent_id: str
    status: str


class AgentMessageRequest(BaseModel):
    content: str


class AutonomyUpdateRequest(BaseModel):
    level: str


_start_time = time.time()


@router.get("/health")
async def studio_health() -> StudioHealthResponse:
    """Health check for the Studio API."""
    return StudioHealthResponse(
        status="ok",
        version="0.1.0",
        uptime_seconds=time.time() - _start_time,
    )


@router.get("/agents")
async def list_agents(
    request: Request,
    _user=Depends(get_current_user),
) -> list[AgentSummary]:
    """List all agents with status, config, and capabilities."""
    agents = []
    runner = getattr(request.app.state, "runner", None)
    if not runner:
        return agents

    from prowlrbot.config.utils import load_config

    config = load_config()

    agents_config = getattr(config, "agents", [])
    if isinstance(agents_config, list):
        for agent_cfg in agents_config:
            get = (
                agent_cfg.get
                if isinstance(agent_cfg, dict)
                else lambda k, d=None: getattr(agent_cfg, k, d)
            )
            agents.append(
                AgentSummary(
                    id=get("id", get("name", "unknown")),
                    name=get("name", "Unknown"),
                    description=get("description", ""),
                    status="idle",
                    capabilities=get("skills", []) or [],
                    model=get("model"),
                    provider=get("provider"),
                ),
            )

    return agents


@router.post("/agents/{agent_id}/run")
async def run_agent(
    agent_id: str,
    body: AgentRunRequest,
    request: Request,
    _user=Depends(get_current_user),
) -> AgentRunResponse:
    """Start an agent run."""
    import uuid

    run_id = str(uuid.uuid4())
    runner = getattr(request.app.state, "runner", None)
    if not runner:
        raise HTTPException(
            status_code=503,
            detail="Agent runner not available",
        )
    return AgentRunResponse(
        run_id=run_id,
        agent_id=agent_id,
        status="starting",
    )


@router.post("/agents/{agent_id}/stop")
async def stop_agent(
    agent_id: str,
    request: Request,
    _user=Depends(get_current_user),
) -> dict:
    """Stop a running agent."""
    return {"agent_id": agent_id, "status": "stopped"}


@router.post("/agents/{agent_id}/message")
async def message_agent(
    agent_id: str,
    body: AgentMessageRequest,
    request: Request,
    _user=Depends(get_current_user),
) -> dict:
    """Send a human message to a running agent."""
    return {"agent_id": agent_id, "status": "message_sent"}


@router.put("/agents/{agent_id}/autonomy")
async def update_autonomy(
    agent_id: str,
    body: AutonomyUpdateRequest,
    request: Request,
    _user=Depends(get_current_user),
) -> dict:
    """Change an agent's autonomy level mid-run."""
    valid_levels = {"watch", "guide", "delegate", "autonomous"}
    if body.level not in valid_levels:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid level. Must be one of: {valid_levels}",
        )
    return {"agent_id": agent_id, "autonomy": body.level}


@router.get("/agents/{agent_id}/stream")
async def stream_agent_events(
    agent_id: str,
    request: Request,
    token: str | None = None,
) -> StreamingResponse:
    """SSE stream of agent events for the Agent Workspace."""
    if token:
        try:
            from prowlrbot.auth.jwt_handler import JWTHandler
            from prowlrbot.auth.middleware import _get_jwt_handler

            handler = _get_jwt_handler()
            handler.decode_token(token)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")

    async def event_generator() -> AsyncGenerator[str, None]:
        yield _sse_event(
            "status",
            {"state": "connected", "agent_id": agent_id},
        )
        try:
            while True:
                await asyncio.sleep(15)
                yield _sse_event("heartbeat", {"timestamp": time.time()})
        except asyncio.CancelledError:
            return

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/auth/validate")
async def validate_token(request: Request) -> dict:
    """Validate a JWT token. Called by Studio's NestJS backend."""
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = auth_header[7:]
    try:
        from prowlrbot.auth.middleware import _get_jwt_handler

        handler = _get_jwt_handler()
        payload = handler.decode_token(token)
        return {
            "valid": True,
            "user": {
                "id": payload.sub,
                "role": payload.role,
                "username": payload.username,
            },
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def _sse_event(event_type: str, data: dict) -> str:
    """Format a server-sent event."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
