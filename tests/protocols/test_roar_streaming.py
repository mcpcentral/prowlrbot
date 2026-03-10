# -*- coding: utf-8 -*-
"""Tests for ROAR Protocol Phase 3 — Streaming Layer."""
from __future__ import annotations

import asyncio
import time
import unittest

from src.prowlrbot.protocols.roar import StreamEvent, StreamEventType
from src.prowlrbot.protocols.sdk.streaming.backpressure import AIMDController
from src.prowlrbot.protocols.sdk.streaming.dedup import IdempotencyGuard
from src.prowlrbot.protocols.sdk.streaming.local import EventBus, StreamFilter


def _make_event(
    event_type: str = "tool_call",
    source: str = "did:roar:agent:test-12345678",
    session_id: str = "sess-1",
    data: dict = None,
) -> StreamEvent:
    return StreamEvent(
        type=event_type,
        source=source,
        session_id=session_id,
        data=data or {"action": "test"},
    )


class TestStreamFilter(unittest.TestCase):
    """Tests for StreamFilter matching logic."""

    def test_empty_filter_matches_all(self):
        f = StreamFilter()
        assert f.matches(_make_event())
        assert f.matches(_make_event(event_type="reasoning"))
        assert f.matches(_make_event(source="did:roar:agent:other-99999999"))

    def test_event_type_filter(self):
        f = StreamFilter(event_types=["tool_call", "reasoning"])
        assert f.matches(_make_event(event_type="tool_call"))
        assert f.matches(_make_event(event_type="reasoning"))
        assert not f.matches(_make_event(event_type="monitor_alert"))

    def test_source_filter(self):
        f = StreamFilter(source_dids=["did:roar:agent:alice-11111111"])
        assert f.matches(_make_event(source="did:roar:agent:alice-11111111"))
        assert not f.matches(_make_event(source="did:roar:agent:bob-22222222"))

    def test_session_filter(self):
        f = StreamFilter(session_ids=["sess-42"])
        assert f.matches(_make_event(session_id="sess-42"))
        assert not f.matches(_make_event(session_id="sess-99"))

    def test_combined_filters_are_and(self):
        f = StreamFilter(
            event_types=["tool_call"],
            source_dids=["did:roar:agent:alice-11111111"],
        )
        # Must match both
        assert f.matches(
            _make_event(event_type="tool_call", source="did:roar:agent:alice-11111111")
        )
        # Wrong type
        assert not f.matches(
            _make_event(event_type="reasoning", source="did:roar:agent:alice-11111111")
        )
        # Wrong source
        assert not f.matches(
            _make_event(event_type="tool_call", source="did:roar:agent:bob-22222222")
        )


class TestEventBus(unittest.TestCase):
    """Tests for the in-process event bus."""

    def test_subscribe_and_publish(self):
        loop = asyncio.new_event_loop()

        async def run():
            bus = EventBus()
            sub = bus.subscribe()
            assert bus.subscriber_count == 1

            event = _make_event()
            delivered = await bus.publish(event)
            assert delivered == 1

            received = await sub.get(timeout=1.0)
            assert received is not None
            assert received.type == "tool_call"
            sub.close()

        loop.run_until_complete(run())
        loop.close()

    def test_filtered_subscription(self):
        loop = asyncio.new_event_loop()

        async def run():
            bus = EventBus()
            sub = bus.subscribe(StreamFilter(event_types=["reasoning"]))

            # Publish non-matching event
            await bus.publish(_make_event(event_type="tool_call"))
            result = await sub.get(timeout=0.1)
            assert result is None  # Should not receive it

            # Publish matching event
            await bus.publish(_make_event(event_type="reasoning"))
            result = await sub.get(timeout=1.0)
            assert result is not None
            assert result.type == "reasoning"
            sub.close()

        loop.run_until_complete(run())
        loop.close()

    def test_multiple_subscribers(self):
        loop = asyncio.new_event_loop()

        async def run():
            bus = EventBus()
            sub1 = bus.subscribe()
            sub2 = bus.subscribe(StreamFilter(event_types=["reasoning"]))

            await bus.publish(_make_event(event_type="tool_call"))
            r1 = await sub1.get(timeout=1.0)
            r2 = await sub2.get(timeout=0.1)

            assert r1 is not None  # sub1 gets all
            assert r2 is None  # sub2 filtered out tool_call

            await bus.publish(_make_event(event_type="reasoning"))
            r1 = await sub1.get(timeout=1.0)
            r2 = await sub2.get(timeout=1.0)
            assert r1 is not None
            assert r2 is not None

            sub1.close()
            sub2.close()

        loop.run_until_complete(run())
        loop.close()

    def test_buffer_overflow_drops_oldest(self):
        loop = asyncio.new_event_loop()

        async def run():
            bus = EventBus(max_buffer=3)
            sub = bus.subscribe(buffer_size=3)

            # Fill buffer
            for i in range(5):
                await bus.publish(_make_event(data={"i": i}))

            # Should have last 3 events (oldest 2 dropped)
            events = []
            for _ in range(3):
                e = await sub.get(timeout=0.5)
                if e:
                    events.append(e)

            assert len(events) == 3
            assert sub.events_dropped >= 2
            sub.close()

        loop.run_until_complete(run())
        loop.close()

    def test_close_subscription(self):
        loop = asyncio.new_event_loop()

        async def run():
            bus = EventBus()
            sub = bus.subscribe()
            assert bus.subscriber_count == 1

            sub.close()
            assert sub.closed
            assert bus.subscriber_count == 0

        loop.run_until_complete(run())
        loop.close()

    def test_close_all(self):
        loop = asyncio.new_event_loop()

        async def run():
            bus = EventBus()
            bus.subscribe()
            bus.subscribe()
            assert bus.subscriber_count == 2

            bus.close_all()
            assert bus.subscriber_count == 0

        loop.run_until_complete(run())
        loop.close()

    def test_publish_many(self):
        loop = asyncio.new_event_loop()

        async def run():
            bus = EventBus()
            sub = bus.subscribe()

            events = [_make_event(data={"i": i}) for i in range(5)]
            total = await bus.publish_many(events)
            assert total == 5

            for i in range(5):
                e = await sub.get(timeout=0.5)
                assert e is not None
            sub.close()

        loop.run_until_complete(run())
        loop.close()


class TestAIMDController(unittest.TestCase):
    """Tests for AIMD backpressure controller."""

    def test_initial_state(self):
        ctrl = AIMDController()
        assert ctrl.rate == 100.0
        assert ctrl.delay > 0

    def test_additive_increase(self):
        ctrl = AIMDController(rate=100.0, window_size=5, additive_increase=10.0)
        initial_rate = ctrl.rate
        for _ in range(5):  # Fill one window
            ctrl.on_success()
        assert ctrl.rate == initial_rate + 10.0

    def test_multiplicative_decrease(self):
        ctrl = AIMDController(rate=100.0, multiplicative_decrease=0.5)
        ctrl.on_drop()
        assert ctrl.rate == 50.0

    def test_min_rate_floor(self):
        ctrl = AIMDController(rate=2.0, min_rate=1.0, multiplicative_decrease=0.5)
        ctrl.on_drop()
        assert ctrl.rate == 1.0
        ctrl.on_drop()
        assert ctrl.rate == 1.0  # Can't go below min

    def test_max_rate_ceiling(self):
        ctrl = AIMDController(
            rate=9995.0, max_rate=10000.0, window_size=1, additive_increase=10.0
        )
        ctrl.on_success()
        assert ctrl.rate == 10000.0
        ctrl.on_success()
        assert ctrl.rate == 10000.0  # Can't exceed max

    def test_stats(self):
        ctrl = AIMDController(rate=200.0)
        stats = ctrl.stats
        assert stats["rate"] == 200.0
        assert stats["delay_ms"] == 5.0  # 1/200 * 1000
        assert "drops" in stats

    def test_reset(self):
        ctrl = AIMDController(rate=500.0)
        ctrl.on_drop()
        assert ctrl.rate != 100.0
        ctrl.reset()
        assert ctrl.rate == 100.0

    def test_sawtooth_pattern(self):
        """AIMD should produce a sawtooth pattern: slow increase, fast decrease."""
        ctrl = AIMDController(
            rate=100.0, window_size=3, additive_increase=10.0,
            multiplicative_decrease=0.5
        )
        # Increase for 2 windows
        for _ in range(6):
            ctrl.on_success()
        assert ctrl.rate == 120.0  # 100 + 10 + 10

        # Drop
        ctrl.on_drop()
        assert ctrl.rate == 60.0  # 120 * 0.5


class TestIdempotencyGuard(unittest.TestCase):
    """Tests for idempotency key deduplication."""

    def test_first_occurrence_not_duplicate(self):
        guard = IdempotencyGuard()
        assert not guard.is_duplicate("key-1")

    def test_second_occurrence_is_duplicate(self):
        guard = IdempotencyGuard()
        guard.is_duplicate("key-1")  # First time
        assert guard.is_duplicate("key-1")  # Duplicate

    def test_different_keys_not_duplicate(self):
        guard = IdempotencyGuard()
        assert not guard.is_duplicate("key-1")
        assert not guard.is_duplicate("key-2")

    def test_lru_eviction(self):
        guard = IdempotencyGuard(max_keys=3)
        guard.is_duplicate("a")
        guard.is_duplicate("b")
        guard.is_duplicate("c")
        guard.is_duplicate("d")  # Evicts "a"

        # "a" was evicted, so it's treated as new
        assert not guard.is_duplicate("a")  # Re-adds "a", evicts "b"
        # "c" and "d" should still be tracked
        assert guard.is_duplicate("c")
        assert guard.is_duplicate("d")

    def test_ttl_expiration(self):
        guard = IdempotencyGuard(ttl_seconds=0.05)
        guard.is_duplicate("key-1")

        # Wait for expiration
        time.sleep(0.1)
        assert not guard.is_duplicate("key-1")  # Expired, treated as new

    def test_mark_seen(self):
        guard = IdempotencyGuard()
        guard.mark_seen("manual-key")
        assert guard.is_duplicate("manual-key")

    def test_size(self):
        guard = IdempotencyGuard()
        assert guard.size == 0
        guard.is_duplicate("a")
        guard.is_duplicate("b")
        assert guard.size == 2

    def test_clear(self):
        guard = IdempotencyGuard()
        guard.is_duplicate("a")
        guard.is_duplicate("b")
        guard.clear()
        assert guard.size == 0
        assert not guard.is_duplicate("a")  # Cleared, treated as new


class TestServerEventBusIntegration(unittest.TestCase):
    """Tests for ROARServer with integrated event bus."""

    def test_server_has_event_bus(self):
        from src.prowlrbot.protocols.roar import AgentIdentity
        from src.prowlrbot.protocols.sdk.server import ROARServer

        identity = AgentIdentity(display_name="test-server")
        server = ROARServer(identity)
        assert server.event_bus is not None
        assert server.event_bus.subscriber_count == 0

    def test_server_emit(self):
        loop = asyncio.new_event_loop()

        async def run():
            from src.prowlrbot.protocols.roar import AgentIdentity
            from src.prowlrbot.protocols.sdk.server import ROARServer

            identity = AgentIdentity(display_name="test-server")
            server = ROARServer(identity)
            sub = server.event_bus.subscribe()

            event = _make_event(source=identity.did)
            delivered = await server.emit(event)
            assert delivered == 1

            received = await sub.get(timeout=1.0)
            assert received is not None
            assert received.source == identity.did
            sub.close()

        loop.run_until_complete(run())
        loop.close()


if __name__ == "__main__":
    unittest.main()
