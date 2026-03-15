# -*- coding: utf-8 -*-
"""Tests for activity log storage."""

import pytest

from prowlrbot.dashboard.activity_log import ActivityLog
from prowlrbot.dashboard.events import EventType


@pytest.fixture
def log(tmp_path):
    db = ActivityLog(db_path=tmp_path / "activity.db")
    yield db
    db.close()


def test_record_event(log):
    log.record(
        session_id="s1",
        event_type=EventType.TOOL_CALL,
        data={"tool": "shell", "command": "ls"},
    )
    events = log.query(session_id="s1")
    assert len(events) == 1
    assert events[0]["event_type"] == "tool_call"


def test_query_by_session(log):
    log.record(session_id="s1", event_type=EventType.TOOL_CALL, data={})
    log.record(session_id="s2", event_type=EventType.TOOL_CALL, data={})
    log.record(session_id="s1", event_type=EventType.REASONING, data={})
    events = log.query(session_id="s1")
    assert len(events) == 2


def test_query_by_type(log):
    log.record(session_id="s1", event_type=EventType.TOOL_CALL, data={})
    log.record(session_id="s1", event_type=EventType.REASONING, data={})
    events = log.query(session_id="s1", event_type=EventType.TOOL_CALL)
    assert len(events) == 1


def test_query_limit(log):
    for i in range(10):
        log.record(
            session_id="s1",
            event_type=EventType.TOOL_CALL,
            data={"i": i},
        )
    events = log.query(session_id="s1", limit=5)
    assert len(events) == 5


def test_query_returns_newest_first(log):
    log.record(
        session_id="s1",
        event_type=EventType.TOOL_CALL,
        data={"order": 1},
    )
    log.record(
        session_id="s1",
        event_type=EventType.TOOL_CALL,
        data={"order": 2},
    )
    events = log.query(session_id="s1")
    assert events[0]["data"]["order"] == 2  # newest first


def test_cleanup_old_events(log):
    log.record(session_id="s1", event_type=EventType.TOOL_CALL, data={})
    deleted = log.cleanup(max_age_days=0)  # Delete everything
    assert deleted >= 1
    assert len(log.query(session_id="s1")) == 0
