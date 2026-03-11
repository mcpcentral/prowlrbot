# -*- coding: utf-8 -*-
# Implements Google A2A Protocol v0.3.0 (proto3, 47 message types)
# Spec: https://github.com/google/A2A — Linux Foundation governance
# Agent Cards: /.well-known/agent.json convention
"""A2A (Agent-to-Agent) protocol server — discover and coordinate with agents.

Implements the A2A v0.3.0 specification with 7-state task lifecycle,
Agent Cards, Messages/Artifacts pattern, and SSE streaming placeholders.

Exposes ProwlrBot agents as A2A-compatible endpoints with Agent Cards,
task lifecycle, and context sharing.

Integration path:
    1. Mount A2A router on the FastAPI app
    2. Agents auto-register Agent Cards on startup
    3. External A2A agents discover ProwlrBot via /.well-known/agent.json
"""

from __future__ import annotations

import time
import uuid
from prowlrbot.compat import StrEnum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# ------------------------------------------------------------------
# Task Status — 7 states per A2A v0.3.0
# ------------------------------------------------------------------


class TaskStatus(StrEnum):
    """A2A v0.3.0 task lifecycle states.

    Transitions:
        submitted -> working -> completed
        submitted -> working -> input_required -> working -> completed
        submitted -> rejected
        submitted | working -> canceled
        submitted | working -> failed
    """

    SUBMITTED = "submitted"
    WORKING = "working"
    COMPLETED = "completed"
    INPUT_REQUIRED = "input_required"
    FAILED = "failed"
    CANCELED = "canceled"
    REJECTED = "rejected"


# ------------------------------------------------------------------
# Message & Artifact Models — A2A v0.3.0 exchange format
# ------------------------------------------------------------------


class Part(BaseModel):
    """A single content part within a Message or Artifact.

    Supports text, inline data (base64), or file references.
    """

    type: str = "text"  # text | inlineData | fileData
    text: Optional[str] = None
    mime_type: Optional[str] = None
    data: Optional[str] = None  # base64-encoded for inlineData
    uri: Optional[str] = None  # for fileData


class Message(BaseModel):
    """A message exchanged between agents or users.

    Follows the A2A v0.3.0 Messages pattern with role-based parts.
    """

    role: str = "user"  # user | agent
    parts: List[Part] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Artifact(BaseModel):
    """An output artifact produced by a task.

    Artifacts represent tangible outputs: files, images, structured data.
    """

    id: str = Field(default_factory=lambda: f"artifact_{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    parts: List[Part] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ------------------------------------------------------------------
# Status Transition History
# ------------------------------------------------------------------


class StatusEntry(BaseModel):
    """A recorded status transition in the task history."""

    status: TaskStatus
    timestamp: float = Field(default_factory=time.time)
    message: Optional[str] = None


# ------------------------------------------------------------------
# Agent Card — A2A v0.3.0 discovery descriptor
# ------------------------------------------------------------------


class A2ASkill(BaseModel):
    """A skill advertised in an Agent Card.

    Skills describe discrete capabilities that an agent can perform,
    with optional tags and examples for discoverability.
    """

    id: str
    name: str
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)


class A2AAgentCard(BaseModel):
    """A2A v0.3.0 Agent Card — capability and identity descriptor.

    Served at ``/.well-known/agent.json`` for agent discovery.
    Includes capabilities dict, structured skills list, authentication
    schemes, and provider metadata.
    """

    name: str = "ProwlrBot"
    description: str = "Autonomous AI agent platform — Always watching. Always ready."
    url: str = ""
    version: str = "1.0.0"
    capabilities: Dict[str, bool] = Field(
        default_factory=lambda: {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": True,
        }
    )
    skills: List[A2ASkill] = Field(default_factory=list)
    authentication: Dict[str, Any] = Field(
        default_factory=lambda: {"schemes": ["Bearer"]}
    )
    supported_protocols: List[str] = Field(
        default_factory=lambda: ["a2a", "mcp", "roar"]
    )
    provider: Dict[str, str] = Field(
        default_factory=lambda: {"organization": "ProwlrBot", "url": ""}
    )


# ------------------------------------------------------------------
# Task Model — A2A v0.3.0 task lifecycle
# ------------------------------------------------------------------


class A2ATask(BaseModel):
    """A task in the A2A v0.3.0 task lifecycle.

    Tasks carry structured Messages (input) and produce Artifacts (output).
    The ``history`` field records all status transitions when
    ``stateTransitionHistory`` is enabled on the agent card.
    """

    id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    from_agent: str = ""
    to_agent: str = ""
    status: TaskStatus = TaskStatus.SUBMITTED
    messages: List[Message] = Field(default_factory=list)
    artifacts: List[Artifact] = Field(default_factory=list)
    history: List[StatusEntry] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ------------------------------------------------------------------
# Send Task Request — payload for POST /a2a/tasks/send
# ------------------------------------------------------------------


class SendTaskRequest(BaseModel):
    """Request body for sending a message to create or continue a task.

    If ``task_id`` is provided, the message is appended to an existing task.
    Otherwise a new task is created.
    """

    task_id: Optional[str] = None
    from_agent: str = ""
    to_agent: str = ""
    message: Message
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ------------------------------------------------------------------
# In-Memory Task Store
# ------------------------------------------------------------------


class A2ATaskStore:
    """In-memory task store for A2A coordination.

    Provides CRUD operations for tasks with status transition tracking.
    In production this would be backed by a persistent store.
    """

    def __init__(self) -> None:
        self._tasks: Dict[str, A2ATask] = {}

    def create(self, task: A2ATask) -> A2ATask:
        """Create and store a new task, recording the initial status."""
        task.history.append(StatusEntry(status=task.status))
        self._tasks[task.id] = task
        return task

    def get(self, task_id: str) -> Optional[A2ATask]:
        """Retrieve a task by ID, or ``None`` if not found."""
        return self._tasks.get(task_id)

    def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        message: Optional[str] = None,
    ) -> Optional[A2ATask]:
        """Transition a task to a new status with history tracking."""
        task = self._tasks.get(task_id)
        if task:
            task.status = status
            task.history.append(StatusEntry(status=status, message=message))
        return task

    def append_message(self, task_id: str, msg: Message) -> Optional[A2ATask]:
        """Append a message to an existing task."""
        task = self._tasks.get(task_id)
        if task:
            task.messages.append(msg)
        return task

    def append_artifact(self, task_id: str, artifact: Artifact) -> Optional[A2ATask]:
        """Append an output artifact to a task."""
        task = self._tasks.get(task_id)
        if task:
            task.artifacts.append(artifact)
        return task

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[A2ATask]:
        """List all tasks, optionally filtered by status."""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks


# ------------------------------------------------------------------
# FastAPI Router
# ------------------------------------------------------------------

router = APIRouter(tags=["a2a"])
_store = A2ATaskStore()
_agent_card = A2AAgentCard()
_event_bus = None  # Injected by app startup when ROAR server is available


def set_event_bus(bus: Any) -> None:
    """Inject a ROAR EventBus for real-time A2A SSE streaming."""
    global _event_bus
    _event_bus = bus


@router.get("/.well-known/agent.json")
async def get_agent_card() -> Dict[str, Any]:
    """A2A agent discovery endpoint.

    Returns the Agent Card describing this agent's capabilities,
    skills, authentication requirements, and supported protocols.
    """
    return _agent_card.model_dump()


@router.post("/a2a/tasks/send", response_model=A2ATask)
async def send_task(request: SendTaskRequest) -> A2ATask:
    """Send a message to create or continue a task.

    If ``task_id`` is provided in the request, the message is appended
    to the existing task and the task transitions to ``working``.
    Otherwise a new task is created in ``submitted`` status and
    immediately transitioned to ``working``.
    """
    if request.task_id:
        task = _store.get(request.task_id)
        if not task:
            raise HTTPException(404, f"Task '{request.task_id}' not found")
        _store.append_message(request.task_id, request.message)
        if task.status == TaskStatus.INPUT_REQUIRED:
            _store.update_status(request.task_id, TaskStatus.WORKING)
        return task

    task = A2ATask(
        from_agent=request.from_agent,
        to_agent=request.to_agent,
        messages=[request.message],
        metadata=request.metadata,
    )
    _store.create(task)
    _store.update_status(task.id, TaskStatus.WORKING)
    return task


@router.post("/a2a/tasks/sendSubscribe")
async def send_task_subscribe(request: SendTaskRequest) -> StreamingResponse:
    """Send a message and subscribe to task updates via SSE.

    Creates or continues a task (same as ``/send``) and returns a
    Server-Sent Events stream for real-time status and artifact updates.

    Note: This is a placeholder implementation. Full SSE streaming
    requires an async event bus wired to the agent runner.
    """
    # Create or retrieve the task using the same logic as send_task
    if request.task_id:
        task = _store.get(request.task_id)
        if not task:
            raise HTTPException(404, f"Task '{request.task_id}' not found")
        _store.append_message(request.task_id, request.message)
        if task.status == TaskStatus.INPUT_REQUIRED:
            _store.update_status(request.task_id, TaskStatus.WORKING)
    else:
        task = A2ATask(
            from_agent=request.from_agent,
            to_agent=request.to_agent,
            messages=[request.message],
            metadata=request.metadata,
        )
        _store.create(task)
        _store.update_status(task.id, TaskStatus.WORKING)

    async def _event_stream() -> Any:
        import json
        from .roar import StreamEvent, StreamEventType

        # Emit initial status
        yield f"data: {json.dumps({'type': 'status', 'task_id': task.id, 'status': task.status})}\n\n"

        # Subscribe to ROAR EventBus for real-time updates
        if _event_bus is not None:
            from .sdk.streaming import StreamFilter

            sub = _event_bus.subscribe(
                StreamFilter(
                    session_ids=[task.id],
                )
            )
            try:
                async for event in sub:
                    yield f"data: {json.dumps({'type': event.type, 'task_id': task.id, 'data': event.data, 'timestamp': event.timestamp})}\n\n"
                    if event.type in (StreamEventType.TASK_UPDATE,) and event.data.get(
                        "status"
                    ) in ("completed", "failed", "canceled"):
                        break
            finally:
                sub.close()
        else:
            yield f"data: {json.dumps({'type': 'done', 'task_id': task.id})}\n\n"

    return StreamingResponse(_event_stream(), media_type="text/event-stream")


@router.get("/a2a/tasks/{task_id}", response_model=A2ATask)
async def get_task(task_id: str) -> A2ATask:
    """Get a task by ID including messages, artifacts, and history."""
    task = _store.get(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return task


@router.get("/a2a/tasks/{task_id}/subscribe")
async def subscribe_task(task_id: str) -> StreamingResponse:
    """Subscribe to real-time updates for a task via SSE.

    Returns a Server-Sent Events stream that emits status changes
    and new artifacts as they are produced. Backed by ROAR EventBus.
    """
    task = _store.get(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")

    async def _event_stream() -> Any:
        import json
        from .roar import StreamEventType

        yield f"data: {json.dumps({'type': 'status', 'task_id': task.id, 'status': task.status})}\n\n"

        if _event_bus is not None:
            from .sdk.streaming import StreamFilter

            sub = _event_bus.subscribe(
                StreamFilter(
                    session_ids=[task.id],
                )
            )
            try:
                async for event in sub:
                    yield f"data: {json.dumps({'type': event.type, 'task_id': task.id, 'data': event.data, 'timestamp': event.timestamp})}\n\n"
                    if event.type in (StreamEventType.TASK_UPDATE,) and event.data.get(
                        "status"
                    ) in ("completed", "failed", "canceled"):
                        break
            finally:
                sub.close()
        else:
            yield f"data: {json.dumps({'type': 'done', 'task_id': task.id})}\n\n"

    return StreamingResponse(_event_stream(), media_type="text/event-stream")


@router.post("/a2a/tasks/{task_id}/cancel")
async def cancel_task(task_id: str) -> Dict[str, str]:
    """Cancel a task.

    Transitions the task to ``canceled`` status. Only tasks in
    ``submitted`` or ``working`` status can be canceled.
    """
    task = _store.get(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")

    if task.status not in (TaskStatus.SUBMITTED, TaskStatus.WORKING):
        raise HTTPException(
            409,
            f"Cannot cancel task in '{task.status}' status — "
            f"only 'submitted' or 'working' tasks can be canceled",
        )

    _store.update_status(task_id, TaskStatus.CANCELED)
    return {"status": "canceled", "task_id": task_id}


@router.get("/a2a/tasks", response_model=List[A2ATask])
async def list_tasks(status: Optional[str] = None) -> List[A2ATask]:
    """List all A2A tasks, optionally filtered by status."""
    task_status = TaskStatus(status) if status else None
    return _store.list_tasks(task_status)


# ------------------------------------------------------------------
# ROAR Bridge — A2A Agent Card to ROAR AgentCard conversion
# ------------------------------------------------------------------


def a2a_card_to_roar(card: A2AAgentCard) -> "AgentCard":
    """Convert an A2A Agent Card to a ROAR AgentCard.

    Bridges the A2A discovery format to ROAR's identity-based
    discovery system, mapping skills to capabilities and preserving
    the HTTP endpoint URL.

    Args:
        card: The A2A Agent Card to convert.

    Returns:
        A ROAR AgentCard with identity, skills, and endpoint info.
    """
    from .roar import AgentCard, AgentIdentity

    identity = AgentIdentity(
        display_name=card.name,
        capabilities=[s.id for s in card.skills],
    )
    return AgentCard(
        identity=identity,
        description=card.description,
        skills=[s.id for s in card.skills],
        endpoints={"http": card.url} if card.url else {},
    )
