# -*- coding: utf-8 -*-
"""API endpoints for external agent management."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...constant import WORKING_DIR
from ...external_agents.manager import ExternalAgentManager
from ...external_agents.models import (
    ExternalAgentConfig,
    ExternalAgentStatus,
    ExternalTask,
    TaskStatus,
)

router = APIRouter(prefix="/external-agents", tags=["external-agents"])

_manager = ExternalAgentManager(db_path=WORKING_DIR / "external_agents.db")


@router.post("/agents", response_model=ExternalAgentConfig)
async def register_agent(config: ExternalAgentConfig) -> ExternalAgentConfig:
    return _manager.register_agent(config)


@router.get("/agents", response_model=List[ExternalAgentConfig])
async def list_agents(enabled_only: bool = False) -> List[ExternalAgentConfig]:
    return _manager.list_agents(enabled_only=enabled_only)


@router.get("/agents/{agent_id}", response_model=ExternalAgentConfig)
async def get_agent(agent_id: str) -> ExternalAgentConfig:
    agent = _manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, f"External agent '{agent_id}' not found")
    return agent


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str) -> Dict[str, str]:
    if not _manager.delete_agent(agent_id):
        raise HTTPException(404, f"External agent '{agent_id}' not found")
    return {"status": "deleted"}


@router.get("/agents/{agent_id}/health", response_model=ExternalAgentStatus)
async def check_health(agent_id: str) -> ExternalAgentStatus:
    return await _manager.check_agent_health(agent_id)


# --- Tasks ---


class TaskRequest(BaseModel):
    agent_id: str
    prompt: str
    context: Dict[str, Any] = {}


@router.post("/tasks", response_model=ExternalTask)
async def create_task(req: TaskRequest) -> ExternalTask:
    agent = _manager.get_agent(req.agent_id)
    if not agent:
        raise HTTPException(404, f"External agent '{req.agent_id}' not found")
    task = ExternalTask(
        agent_id=req.agent_id,
        prompt=req.prompt,
        context=req.context,
    )
    return _manager.create_task(task)


@router.post("/tasks/{task_id}/execute", response_model=ExternalTask)
async def execute_task(task_id: str) -> ExternalTask:
    task = _manager.get_task(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return await _manager.execute_task(task_id)


@router.get("/tasks/{task_id}", response_model=ExternalTask)
async def get_task(task_id: str) -> ExternalTask:
    task = _manager.get_task(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return task


@router.get("/tasks", response_model=List[ExternalTask])
async def list_tasks(
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> List[ExternalTask]:
    return _manager.list_tasks(agent_id=agent_id, status=status, limit=limit)


@router.put("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str) -> Dict[str, str]:
    if not _manager.cancel_task(task_id):
        raise HTTPException(404, f"Task '{task_id}' not found")
    return {"status": "cancelled"}
