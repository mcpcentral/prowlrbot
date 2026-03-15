# -*- coding: utf-8 -*-
"""Verify leaderboard_update is pushed after XP award."""
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pytest


def test_xp_tracker_award_records_xp(tmp_path):
    """Basic: award_xp writes to DB and returns XPGain."""
    from prowlrbot.gamification.xp_tracker import XPTracker
    from prowlrbot.gamification.models import XPGain

    tracker = XPTracker(db_path=tmp_path / "test.db")
    result = tracker.award_xp(
        entity_id="test-agent",
        amount=10,
        category="task_complete",
        reason="test task",
    )
    assert result is not None
    # Result should be XPGain
    assert isinstance(result, XPGain)
    assert result.amount == 10
    assert result.entity_id == "test-agent"
    tracker.close()


def test_xp_tracker_leaderboard_has_entry_after_award(tmp_path):
    """After awarding XP, entity appears in leaderboard."""
    from prowlrbot.gamification.xp_tracker import XPTracker

    tracker = XPTracker(db_path=tmp_path / "test.db")
    tracker.award_xp(
        "agent-abc",
        25,
        "task_complete",
        "did something",
        entity_type="agent",
    )

    leaderboard = tracker.get_leaderboard(entity_type="agent", limit=10)
    entity_ids = [e.entity_id for e in leaderboard]
    assert "agent-abc" in entity_ids
    tracker.close()


@pytest.mark.asyncio
async def test_xp_award_broadcasts_leaderboard_update(tmp_path):
    """award_xp triggers a broadcast on the global EventBus when one is set."""
    from prowlrbot.gamification.xp_tracker import XPTracker
    from prowlrbot.dashboard.events import (
        EventBus,
        EventType,
        set_global_event_bus,
        get_global_event_bus,
    )

    # Set up a real EventBus with a capturing subscriber
    bus = EventBus()
    set_global_event_bus(bus)

    received_events = []

    async def capture(event):
        received_events.append(event)

    # Subscribe with a fake session_id — broadcast hits all subscribers
    bus.subscribe("test-session", capture)

    try:
        tracker = XPTracker(db_path=tmp_path / "test.db")
        tracker.award_xp(
            "agent-xyz",
            50,
            "task_complete",
            "pushed task",
            entity_type="agent",
        )

        # Give the event loop a moment to process the create_task
        await asyncio.sleep(0.05)

        assert (
            len(received_events) == 1
        ), f"Expected 1 event, got {len(received_events)}"
        evt = received_events[0]
        assert evt.type == EventType.LEADERBOARD_UPDATE
        assert evt.data["entity_id"] == "agent-xyz"
        assert evt.data["entity_type"] == "agent"
        assert evt.data["new_xp"] == 50
        assert evt.data["category"] == "task_complete"
        tracker.close()
    finally:
        bus.unsubscribe("test-session", capture)
        # Reset global bus to avoid cross-test pollution
        set_global_event_bus(None)


def test_xp_award_safe_without_event_bus(tmp_path):
    """award_xp must not raise when no global EventBus is registered."""
    from prowlrbot.dashboard.events import set_global_event_bus
    from prowlrbot.gamification.xp_tracker import XPTracker

    set_global_event_bus(None)
    tracker = XPTracker(db_path=tmp_path / "test.db")
    # Should complete without any exception
    result = tracker.award_xp("safe-entity", 5, "misc", "no bus test")
    assert result is not None
    tracker.close()
