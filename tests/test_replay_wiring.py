# -*- coding: utf-8 -*-
"""Tests for replay recording wiring in AgentRunner."""
import pytest
from pathlib import Path
from prowlrbot.replay.recorder import SessionRecorder, EventType


def test_start_and_stop_recording(tmp_path):
    recorder = SessionRecorder(db_path=tmp_path / "test_replay.db")
    sess = recorder.start_recording("test_session", agent_id="agent1", title="Test")
    assert sess.session_id == "test_session"
    assert sess.id.startswith("replay_")
    recorder.record_event(sess.id, EventType.USER_MESSAGE, content="hello")
    recorder.record_event(sess.id, EventType.AGENT_RESPONSE, content="world")
    stopped = recorder.stop_recording(sess.id)
    assert stopped is not None
    assert stopped.event_count == 2
    detail = recorder.get_session_detail(sess.id)
    assert detail is not None
    types = [e.event_type for e in detail.events]
    assert types[0] == EventType.USER_MESSAGE
    assert types[1] == EventType.AGENT_RESPONSE
    recorder.close()


def test_list_sessions_returns_recorded(tmp_path):
    recorder = SessionRecorder(db_path=tmp_path / "test_replay2.db")
    recorder.start_recording("session_a", agent_id="", title="A")
    sessions = recorder.list_sessions()
    assert any(s.session_id == "session_a" for s in sessions)
    recorder.close()


def test_module_level_recorder_importable():
    """The _replay_recorder module singleton is importable from runner."""
    from prowlrbot.app.runner.runner import _replay_recorder
    assert _replay_recorder is not None
