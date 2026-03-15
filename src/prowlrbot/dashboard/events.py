# -*- coding: utf-8 -*-
"""Dashboard event types and event bus."""

import json
import time
from dataclasses import dataclass, field
from prowlrbot.compat import StrEnum
from typing import Any, Callable, Coroutine, Dict, List


class EventType(StrEnum):
    """Types of dashboard events."""

    TOOL_CALL = "tool_call"
    MCP_REQUEST = "mcp_request"
    REASONING = "reasoning"
    TASK_UPDATE = "task_update"
    MONITOR_ALERT = "monitor_alert"
    SWARM_JOB = "swarm_job"
    CHECKPOINT = "checkpoint"
    STREAM_TOKEN = "stream_token"
    AGENT_STATUS = "agent_status"
    ERROR = "error"
    LEADERBOARD_UPDATE = "leaderboard_update"


@dataclass
class DashboardEvent:
    """A single dashboard event for real-time streaming."""

    type: EventType
    session_id: str
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps(
            {
                "type": self.type,
                "session_id": self.session_id,
                "data": self.data,
                "timestamp": self.timestamp,
            },
        )


# Type alias for async event handlers
EventHandler = Callable[[DashboardEvent], Coroutine[Any, Any, None]]


class EventBus:
    """Pub/sub event bus for dashboard real-time updates."""

    def __init__(self):
        self._subscribers: Dict[str, List[EventHandler]] = {}

    def subscribe(self, session_id: str, handler: EventHandler) -> None:
        if session_id not in self._subscribers:
            self._subscribers[session_id] = []
        self._subscribers[session_id].append(handler)

    def unsubscribe(self, session_id: str, handler: EventHandler) -> None:
        if session_id in self._subscribers:
            self._subscribers[session_id] = [
                h for h in self._subscribers[session_id] if h is not handler
            ]

    async def publish(self, event: DashboardEvent) -> None:
        """Publish event to subscribers of the specific session."""
        handlers = self._subscribers.get(event.session_id, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception:
                pass  # Don't let one handler break others

    async def broadcast(self, event: DashboardEvent) -> None:
        """Broadcast event to ALL subscribers."""
        for session_id, handlers in self._subscribers.items():
            for handler in handlers:
                try:
                    await handler(event)
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# Global event bus singleton — set once by the app at startup so that
# subsystems (e.g. XPTracker) can push events without circular imports.
# ---------------------------------------------------------------------------

_global_event_bus: "EventBus | None" = None


def set_global_event_bus(bus: "EventBus") -> None:
    """Inject the application-level EventBus. Called once from _app.py."""
    global _global_event_bus
    _global_event_bus = bus


def get_global_event_bus() -> "EventBus | None":
    """Return the global EventBus, or None if not yet initialised."""
    return _global_event_bus
