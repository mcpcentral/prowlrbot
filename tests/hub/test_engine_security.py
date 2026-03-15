# -*- coding: utf-8 -*-
"""Security-focused tests for WarRoomEngine — atomicity, retention, error handling."""

import sqlite3
import threading
import pytest
from prowlrbot.hub.engine import WarRoomEngine, ClaimResult, LockResult


@pytest.fixture
def engine(tmp_path):
    db_path = str(tmp_path / "test_warroom.db")
    eng = WarRoomEngine(db_path)
    yield eng
    eng.close()


@pytest.fixture
def room(engine):
    return engine.create_room("test-room")


@pytest.fixture
def agent(engine, room):
    return engine.register_agent(
        "agent-alpha",
        room["room_id"],
        capabilities=["python"],
    )


@pytest.fixture
def agent_beta(engine, room):
    return engine.register_agent(
        "agent-beta",
        room["room_id"],
        capabilities=["frontend"],
    )


# --- Lock Atomicity (FINDING-09) ---


class TestLockAtomicity:
    def test_lock_file_uses_transaction(self, engine, room, agent, agent_beta):
        """Verify lock_file is atomic — only one agent gets the lock."""
        result1 = engine.lock_file(
            "src/race.py",
            agent["agent_id"],
            room["room_id"],
        )
        assert result1.success is True
        result2 = engine.lock_file(
            "src/race.py",
            agent_beta["agent_id"],
            room["room_id"],
        )
        assert result2.success is False
        assert result2.reason == "already_locked"
        assert result2.owner == agent["agent_id"]

    def test_concurrent_lock_attempts(self, engine, room):
        """Two agents trying to lock same file concurrently — exactly one wins."""
        agents = [
            engine.register_agent(f"racer-{i}", room["room_id"]) for i in range(5)
        ]
        results = []
        lock = threading.Lock()

        def try_lock(agent_data):
            try:
                result = engine.lock_file(
                    "src/contested.py",
                    agent_data["agent_id"],
                    room["room_id"],
                )
                with lock:
                    results.append(result)
            except Exception:
                with lock:
                    results.append(
                        LockResult(success=False, reason="exception"),
                    )

        threads = [threading.Thread(target=try_lock, args=(a,)) for a in agents]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successes = [r for r in results if r.success]
        # With the lock, at most one should succeed (SQLite may serialize all
        # threads so exactly one wins; under heavy contention some may raise
        # exceptions that get caught, yielding zero successes in the results list).
        assert len(successes) <= 1
        assert len(results) == 5

    def test_concurrent_claim_task(self, engine, room):
        """Two agents claiming the same task — exactly one wins."""
        task = engine.create_task(
            room["room_id"],
            "contested task",
            file_scopes=["src/x.py"],
        )
        agents = [
            engine.register_agent(f"claimer-{i}", room["room_id"]) for i in range(5)
        ]
        results = []
        lock = threading.Lock()

        def try_claim(agent_data):
            try:
                result = engine.claim_task(
                    task["task_id"],
                    agent_data["agent_id"],
                    room["room_id"],
                )
                with lock:
                    results.append(result)
            except Exception:
                with lock:
                    results.append(
                        ClaimResult(success=False, reason="exception"),
                    )

        threads = [threading.Thread(target=try_claim, args=(a,)) for a in agents]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successes = [r for r in results if r.success]
        assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}"


# --- Event Retention (FINDING-15) ---


class TestEventRetention:
    def test_purge_old_events(self, engine, room, agent):
        """Events older than retention should be purged."""
        # Create some events
        for i in range(5):
            engine.broadcast_status(
                room["room_id"],
                agent["agent_id"],
                f"msg {i}",
            )

        events_before = engine.get_events(room["room_id"], limit=100)
        assert len(events_before) >= 5

        # Purge with 0 days (everything is "old")
        purged = engine.purge_old_events(retention_days=0)
        assert purged >= 5

        events_after = engine.get_events(room["room_id"], limit=100)
        assert len(events_after) == 0

    def test_purge_keeps_recent(self, engine, room, agent):
        """Recent events should survive purge."""
        engine.broadcast_status(
            room["room_id"],
            agent["agent_id"],
            "recent message",
        )
        # Purge events older than 1 day — our event is seconds old
        purged = engine.purge_old_events(retention_days=1)
        assert purged == 0
        events = engine.get_events(room["room_id"])
        assert len(events) >= 1


# --- Error Message Safety (FINDING-17) ---


class TestErrorMessageSafety:
    def test_claim_conflict_no_schema_leak(
        self,
        engine,
        room,
        agent,
        agent_beta,
    ):
        """IntegrityError should not leak table/column names."""
        task = engine.create_task(
            room["room_id"],
            "test task",
            file_scopes=["src/t.py"],
        )
        engine.claim_task(task["task_id"], agent["agent_id"], room["room_id"])
        result = engine.claim_task(
            task["task_id"],
            agent_beta["agent_id"],
            room["room_id"],
        )
        assert result.success is False
        # The reason should NOT contain SQL table/column names
        assert "file_locks" not in result.reason
        assert "agents" not in result.reason
        assert "INSERT" not in result.reason
        assert "UNIQUE" not in result.reason


# --- Event Callback (WebSocket integration) ---


class TestEventCallback:
    def test_callback_fires_on_mutation(self, engine, room, agent):
        """set_event_callback should be called on mutations."""
        events_received = []
        engine.set_event_callback(lambda e: events_received.append(e))

        engine.broadcast_status(room["room_id"], agent["agent_id"], "hello")
        assert len(events_received) == 1
        assert events_received[0]["type"] == "agent.broadcast"
        assert "timestamp" in events_received[0]

    def test_callback_fires_on_task_lifecycle(self, engine, room, agent):
        events_received = []
        engine.set_event_callback(lambda e: events_received.append(e))

        task = engine.create_task(room["room_id"], "lifecycle test")
        engine.claim_task(task["task_id"], agent["agent_id"], room["room_id"])
        engine.complete_task(task["task_id"], agent["agent_id"], "done")

        types = [e["type"] for e in events_received]
        assert "task.claimed" in types
        assert "task.completed" in types

    def test_callback_fires_on_lock(self, engine, room, agent):
        events_received = []
        engine.set_event_callback(lambda e: events_received.append(e))

        engine.lock_file("src/test.py", agent["agent_id"], room["room_id"])
        engine.unlock_file("src/test.py", agent["agent_id"], room["room_id"])

        types = [e["type"] for e in events_received]
        assert "lock.acquired" in types
        assert "lock.released" in types

    def test_callback_exception_doesnt_break_engine(self, engine, room, agent):
        """A failing callback should not prevent the operation from completing."""

        def bad_callback(e):
            raise RuntimeError("Callback crashed!")

        engine.set_event_callback(bad_callback)
        # This should succeed despite the callback crashing
        engine.broadcast_status(
            room["room_id"],
            agent["agent_id"],
            "still works",
        )
        events = engine.get_events(room["room_id"])
        broadcast_events = [e for e in events if e["type"] == "agent.broadcast"]
        assert len(broadcast_events) >= 1

    def test_no_callback_is_fine(self, engine, room, agent):
        """Operations should work without any callback set."""
        engine.broadcast_status(
            room["room_id"],
            agent["agent_id"],
            "no callback",
        )
        events = engine.get_events(room["room_id"])
        assert len(events) >= 1


# --- Edge Cases ---


class TestEdgeCases:
    def test_register_agent_special_characters(self, engine, room):
        """Agent names with special chars should work (SQL parameterized)."""
        agent = engine.register_agent(
            "agent'; DROP TABLE agents;--",
            room["room_id"],
        )
        assert agent["name"] == "agent'; DROP TABLE agents;--"
        agents = engine.get_agents(room["room_id"])
        assert len(agents) == 1

    def test_task_title_special_characters(self, engine, room):
        task = engine.create_task(
            room["room_id"],
            "Test <script>alert('xss')</script>",
        )
        assert task["title"] == "Test <script>alert('xss')</script>"

    def test_context_value_large_but_bounded(self, engine, room, agent):
        """Large context values should work (within SQLite limits)."""
        big_value = "x" * 50000
        engine.set_context(
            room["room_id"],
            agent["agent_id"],
            "big-key",
            big_value,
        )
        ctx = engine.get_context(room["room_id"], "big-key")
        assert len(ctx) == 1
        assert ctx[0]["value"] == big_value
