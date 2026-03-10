# -*- coding: utf-8 -*-
"""Tests for WebSocket event system."""

import json

import pytest

from prowlrbot.dashboard.events import DashboardEvent, EventType, EventBus


def test_event_serialization():
    event = DashboardEvent(
        type=EventType.TOOL_CALL,
        session_id="test-session",
        data={"tool": "shell", "command": "ls"},
    )
    serialized = event.to_json()
    parsed = json.loads(serialized)
    assert parsed["type"] == "tool_call"
    assert parsed["session_id"] == "test-session"
    assert parsed["data"]["tool"] == "shell"
    assert "timestamp" in parsed


def test_event_type_values():
    assert EventType.TOOL_CALL == "tool_call"
    assert EventType.REASONING == "reasoning"
    assert EventType.TASK_UPDATE == "task_update"
    assert EventType.MONITOR_ALERT == "monitor_alert"
    assert EventType.STREAM_TOKEN == "stream_token"


@pytest.mark.asyncio
async def test_event_bus_subscribe_and_publish():
    bus = EventBus()
    received = []

    async def handler(event):
        received.append(event)

    bus.subscribe("test-session", handler)

    event = DashboardEvent(
        type=EventType.TOOL_CALL,
        session_id="test-session",
        data={"tool": "shell"},
    )
    await bus.publish(event)

    assert len(received) == 1
    assert received[0].type == EventType.TOOL_CALL


@pytest.mark.asyncio
async def test_event_bus_unsubscribe():
    bus = EventBus()
    received = []

    async def handler(event):
        received.append(event)

    bus.subscribe("test-session", handler)
    bus.unsubscribe("test-session", handler)

    event = DashboardEvent(
        type=EventType.TOOL_CALL,
        session_id="test-session",
        data={},
    )
    await bus.publish(event)
    assert len(received) == 0


@pytest.mark.asyncio
async def test_event_bus_broadcast():
    bus = EventBus()
    received_a = []
    received_b = []

    async def handler_a(event):
        received_a.append(event)

    async def handler_b(event):
        received_b.append(event)

    bus.subscribe("session-a", handler_a)
    bus.subscribe("session-b", handler_b)

    event = DashboardEvent(
        type=EventType.MONITOR_ALERT,
        session_id="*",  # broadcast
        data={"alert": "test"},
    )
    await bus.broadcast(event)

    assert len(received_a) == 1
    assert len(received_b) == 1
