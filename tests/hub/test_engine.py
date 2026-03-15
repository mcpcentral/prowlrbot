# -*- coding: utf-8 -*-
"""Tests for ProwlrHub WarRoomEngine — atomic task claiming, file locking, shared context."""

import os
import tempfile
import pytest
from prowlrbot.hub.engine import WarRoomEngine, ClaimResult, LockResult


@pytest.fixture
def engine(tmp_path):
    """Create a fresh engine with an ephemeral database."""
    db_path = str(tmp_path / "test_warroom.db")
    eng = WarRoomEngine(db_path)
    yield eng
    eng.close()


@pytest.fixture
def room(engine):
    """Create a default room."""
    return engine.create_room("test-room")


@pytest.fixture
def agent(engine, room):
    """Register an agent in the room."""
    return engine.register_agent(
        "agent-alpha",
        room["room_id"],
        capabilities=["python", "testing"],
    )


@pytest.fixture
def agent_beta(engine, room):
    """Register a second agent."""
    return engine.register_agent(
        "agent-beta",
        room["room_id"],
        capabilities=["frontend"],
    )


# --- Room Management ---


class TestRoomManagement:
    def test_create_room(self, engine):
        room = engine.create_room("my-room", mode="local")
        assert room["name"] == "my-room"
        assert room["mode"] == "local"
        assert room["room_id"].startswith("room-")

    def test_get_room(self, engine):
        room = engine.create_room("lookup-room")
        fetched = engine.get_room(room["room_id"])
        assert fetched is not None
        assert fetched["name"] == "lookup-room"

    def test_get_room_missing(self, engine):
        assert engine.get_room("room-nonexistent") is None

    def test_get_or_create_default_room(self, engine):
        r1 = engine.get_or_create_default_room()
        r2 = engine.get_or_create_default_room()
        assert r1["room_id"] == r2["room_id"]


# --- Agent Lifecycle ---


class TestAgentLifecycle:
    def test_register_agent(self, engine, room):
        agent = engine.register_agent(
            "test-agent",
            room["room_id"],
            capabilities=["python"],
        )
        assert agent["agent_id"].startswith("agent-")
        assert agent["name"] == "test-agent"
        assert agent["capabilities"] == ["python"]

    def test_get_agents(self, engine, room):
        engine.register_agent("a1", room["room_id"])
        engine.register_agent("a2", room["room_id"])
        agents = engine.get_agents(room["room_id"])
        assert len(agents) == 2
        names = {a["name"] for a in agents}
        assert names == {"a1", "a2"}

    def test_heartbeat(self, engine, room):
        agent = engine.register_agent("heartbeat-agent", room["room_id"])
        assert engine.heartbeat(agent["agent_id"]) is True

    def test_disconnect_releases_locks(self, engine, room):
        agent = engine.register_agent("locker", room["room_id"])
        engine.lock_file("src/foo.py", agent["agent_id"], room["room_id"])
        engine.disconnect_agent(agent["agent_id"])
        # Lock should be released
        conflicts = engine.check_conflicts(["src/foo.py"], room["room_id"])
        assert len(conflicts) == 0

    def test_disconnect_releases_tasks(self, engine, room):
        agent = engine.register_agent("worker", room["room_id"])
        task = engine.create_task(room["room_id"], "do stuff")
        engine.claim_task(task["task_id"], agent["agent_id"], room["room_id"])
        engine.disconnect_agent(agent["agent_id"])
        # Task should be back to pending
        board = engine.get_mission_board(room["room_id"])
        assert board[0]["status"] == "pending"


# --- Task Management ---


class TestTaskManagement:
    def test_create_task(self, engine, room):
        task = engine.create_task(
            room["room_id"],
            "Build feature X",
            priority="high",
        )
        assert task["task_id"].startswith("task-")
        assert task["title"] == "Build feature X"
        assert task["priority"] == "high"
        assert task["status"] == "pending"

    def test_mission_board_sorted_by_priority(self, engine, room):
        engine.create_task(room["room_id"], "low task", priority="low")
        engine.create_task(
            room["room_id"],
            "critical task",
            priority="critical",
        )
        engine.create_task(room["room_id"], "normal task", priority="normal")
        board = engine.get_mission_board(room["room_id"])
        priorities = [t["priority"] for t in board]
        assert priorities == ["critical", "normal", "low"]

    def test_claim_task_success(self, engine, room, agent):
        task = engine.create_task(
            room["room_id"],
            "claimable",
            file_scopes=["src/a.py"],
        )
        result = engine.claim_task(
            task["task_id"],
            agent["agent_id"],
            room["room_id"],
        )
        assert result.success is True
        assert result.lock_token != ""

    def test_claim_task_already_taken(self, engine, room, agent, agent_beta):
        task = engine.create_task(
            room["room_id"],
            "race condition",
            file_scopes=["src/b.py"],
        )
        r1 = engine.claim_task(
            task["task_id"],
            agent["agent_id"],
            room["room_id"],
        )
        assert r1.success is True
        r2 = engine.claim_task(
            task["task_id"],
            agent_beta["agent_id"],
            room["room_id"],
        )
        assert r2.success is False
        assert r2.reason == "not_available"

    def test_claim_task_file_conflict(self, engine, room, agent, agent_beta):
        t1 = engine.create_task(
            room["room_id"],
            "task1",
            file_scopes=["src/shared.py"],
        )
        t2 = engine.create_task(
            room["room_id"],
            "task2",
            file_scopes=["src/shared.py"],
        )
        r1 = engine.claim_task(
            t1["task_id"],
            agent["agent_id"],
            room["room_id"],
        )
        assert r1.success is True
        r2 = engine.claim_task(
            t2["task_id"],
            agent_beta["agent_id"],
            room["room_id"],
        )
        assert r2.success is False
        assert r2.reason == "files_locked"
        assert len(r2.conflicts) == 1
        assert r2.conflicts[0]["file"] == "src/shared.py"

    def test_complete_task_releases_locks(self, engine, room, agent):
        task = engine.create_task(
            room["room_id"],
            "finish me",
            file_scopes=["src/c.py"],
        )
        engine.claim_task(task["task_id"], agent["agent_id"], room["room_id"])
        ok = engine.complete_task(task["task_id"], agent["agent_id"], "done!")
        assert ok is True
        # File should be free
        conflicts = engine.check_conflicts(["src/c.py"], room["room_id"])
        assert len(conflicts) == 0
        # Task should be done
        board = engine.get_mission_board(room["room_id"])
        assert board[0]["status"] == "done"

    def test_fail_task_releases_locks(self, engine, room, agent):
        task = engine.create_task(
            room["room_id"],
            "fail me",
            file_scopes=["src/d.py"],
        )
        engine.claim_task(task["task_id"], agent["agent_id"], room["room_id"])
        ok = engine.fail_task(task["task_id"], agent["agent_id"], "too hard")
        assert ok is True
        conflicts = engine.check_conflicts(["src/d.py"], room["room_id"])
        assert len(conflicts) == 0

    def test_complete_task_wrong_owner(self, engine, room, agent, agent_beta):
        task = engine.create_task(room["room_id"], "owned task")
        engine.claim_task(task["task_id"], agent["agent_id"], room["room_id"])
        ok = engine.complete_task(
            task["task_id"],
            agent_beta["agent_id"],
            "stealing",
        )
        assert ok is False

    def test_update_task_progress(self, engine, room, agent):
        task = engine.create_task(room["room_id"], "progress tracker")
        engine.claim_task(task["task_id"], agent["agent_id"], room["room_id"])
        engine.update_task(task["task_id"], agent["agent_id"], "50% done")
        board = engine.get_mission_board(room["room_id"])
        assert board[0]["progress_note"] == "50% done"

    def test_blocked_tasks(self, engine, room):
        t1 = engine.create_task(room["room_id"], "prerequisite")
        t2 = engine.create_task(
            room["room_id"],
            "depends on t1",
            blocked_by=[t1["task_id"]],
        )
        board = engine.get_mission_board(room["room_id"])
        blocked_task = [t for t in board if t["task_id"] == t2["task_id"]][0]
        assert blocked_task["is_blocked"] is True

    def test_capability_filter(self, engine, room):
        engine.create_task(
            room["room_id"],
            "python only",
            required_capabilities=["python"],
        )
        engine.create_task(
            room["room_id"],
            "frontend only",
            required_capabilities=["frontend"],
        )
        board = engine.get_mission_board(
            room["room_id"],
            agent_capabilities=["python"],
        )
        assert len(board) == 1
        assert board[0]["title"] == "python only"


# --- File Locking ---


class TestFileLocking:
    def test_lock_file(self, engine, room, agent):
        result = engine.lock_file(
            "src/lock.py",
            agent["agent_id"],
            room["room_id"],
        )
        assert result.success is True
        assert result.lock_token != ""

    def test_lock_file_conflict(self, engine, room, agent, agent_beta):
        engine.lock_file("src/conflict.py", agent["agent_id"], room["room_id"])
        result = engine.lock_file(
            "src/conflict.py",
            agent_beta["agent_id"],
            room["room_id"],
        )
        assert result.success is False
        assert result.reason == "already_locked"
        assert result.owner == agent["agent_id"]

    def test_lock_same_agent_succeeds(self, engine, room, agent):
        engine.lock_file("src/relock.py", agent["agent_id"], room["room_id"])
        result = engine.lock_file(
            "src/relock.py",
            agent["agent_id"],
            room["room_id"],
        )
        # Same agent re-locking should succeed (or at least not fail)
        assert result.success is True

    def test_unlock_file(self, engine, room, agent):
        engine.lock_file("src/unlock.py", agent["agent_id"], room["room_id"])
        ok = engine.unlock_file(
            "src/unlock.py",
            agent["agent_id"],
            room["room_id"],
        )
        assert ok is True
        # Now another agent can lock it
        agent2 = engine.register_agent("other", room["room_id"])
        result = engine.lock_file(
            "src/unlock.py",
            agent2["agent_id"],
            room["room_id"],
        )
        assert result.success is True

    def test_check_conflicts(self, engine, room, agent):
        engine.lock_file("src/a.py", agent["agent_id"], room["room_id"])
        conflicts = engine.check_conflicts(
            ["src/a.py", "src/b.py"],
            room["room_id"],
        )
        assert len(conflicts) == 1
        assert conflicts[0]["file"] == "src/a.py"


# --- Shared Context ---


class TestSharedContext:
    def test_set_and_get_context(self, engine, room, agent):
        engine.set_context(
            room["room_id"],
            agent["agent_id"],
            "api-pattern",
            "REST over gRPC",
        )
        ctx = engine.get_context(room["room_id"], "api-pattern")
        assert len(ctx) == 1
        assert ctx[0]["value"] == "REST over gRPC"

    def test_get_all_context(self, engine, room, agent):
        engine.set_context(room["room_id"], agent["agent_id"], "k1", "v1")
        engine.set_context(room["room_id"], agent["agent_id"], "k2", "v2")
        ctx = engine.get_context(room["room_id"])
        assert len(ctx) == 2

    def test_context_overwrite(self, engine, room, agent):
        engine.set_context(room["room_id"], agent["agent_id"], "key", "old")
        engine.set_context(room["room_id"], agent["agent_id"], "key", "new")
        ctx = engine.get_context(room["room_id"], "key")
        assert len(ctx) == 1
        assert ctx[0]["value"] == "new"


# --- Events ---


class TestEvents:
    def test_events_logged(self, engine, room, agent):
        engine.broadcast_status(
            room["room_id"],
            agent["agent_id"],
            "hello world",
        )
        events = engine.get_events(room["room_id"])
        broadcast_events = [e for e in events if e["type"] == "agent.broadcast"]
        assert len(broadcast_events) >= 1
        assert broadcast_events[0]["payload"]["message"] == "hello world"

    def test_event_type_filter(self, engine, room, agent):
        engine.create_task(room["room_id"], "filter test")
        engine.broadcast_status(
            room["room_id"],
            agent["agent_id"],
            "status update",
        )
        events = engine.get_events(
            room["room_id"],
            event_type="agent.broadcast",
        )
        assert all(e["type"] == "agent.broadcast" for e in events)

    def test_event_limit(self, engine, room, agent):
        for i in range(10):
            engine.broadcast_status(
                room["room_id"],
                agent["agent_id"],
                f"msg {i}",
            )
        events = engine.get_events(room["room_id"], limit=3)
        assert len(events) <= 3


# --- Dead Agent Sweep ---


class TestDeadAgentSweep:
    def test_sweep_no_dead_agents(self, engine, room, agent):
        swept = engine.sweep_dead_agents(ttl_minutes=5)
        assert swept == 0
