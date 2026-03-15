# -*- coding: utf-8 -*-
"""Tests for EventBus replay buffer feature."""

from __future__ import annotations

import asyncio
import unittest

from prowlrbot.protocols.roar import StreamEvent, StreamEventType
from prowlrbot.protocols.sdk.streaming.local import EventBus, StreamFilter


class TestReplayBuffer(unittest.TestCase):
    """Tests for EventBus replay buffer behavior."""

    def _run(self, coro):
        """Helper to run async tests."""
        return asyncio.run(coro)

    def test_replay_disabled_by_default(self):
        """Subscribers without replay=True get no buffered events."""

        async def _test():
            bus = EventBus(replay_size=50)
            await bus.publish(
                StreamEvent(type=StreamEventType.TOOL_CALL, data={"n": 1}),
            )
            await bus.publish(
                StreamEvent(type=StreamEventType.REASONING, data={"n": 2}),
            )

            sub = bus.subscribe()  # replay defaults to False
            # Should have no events pre-filled
            event = await sub.get(timeout=0.1)
            assert event is None
            sub.close()

        self._run(_test())

    def test_replay_delivers_past_events(self):
        """Subscribers with replay=True get buffered events."""

        async def _test():
            bus = EventBus(replay_size=50)
            await bus.publish(
                StreamEvent(type=StreamEventType.TOOL_CALL, data={"n": 1}),
            )
            await bus.publish(
                StreamEvent(type=StreamEventType.REASONING, data={"n": 2}),
            )
            await bus.publish(
                StreamEvent(type=StreamEventType.TOOL_CALL, data={"n": 3}),
            )

            sub = bus.subscribe(replay=True)
            e1 = await sub.get(timeout=0.5)
            e2 = await sub.get(timeout=0.5)
            e3 = await sub.get(timeout=0.5)

            assert e1 is not None
            assert e1.data == {"n": 1}
            assert e2 is not None
            assert e2.data == {"n": 2}
            assert e3 is not None
            assert e3.data == {"n": 3}
            sub.close()

        self._run(_test())

    def test_replay_with_filter(self):
        """Replay only delivers events matching the subscriber's filter."""

        async def _test():
            bus = EventBus(replay_size=50)
            await bus.publish(
                StreamEvent(type=StreamEventType.TOOL_CALL, data={"n": 1}),
            )
            await bus.publish(
                StreamEvent(type=StreamEventType.REASONING, data={"n": 2}),
            )
            await bus.publish(
                StreamEvent(type=StreamEventType.TOOL_CALL, data={"n": 3}),
            )

            filt = StreamFilter(event_types=[StreamEventType.TOOL_CALL])
            sub = bus.subscribe(filter_spec=filt, replay=True)

            e1 = await sub.get(timeout=0.5)
            e2 = await sub.get(timeout=0.5)
            e3 = await sub.get(timeout=0.1)

            assert e1 is not None
            assert e1.data == {"n": 1}
            assert e2 is not None
            assert e2.data == {"n": 3}
            assert e3 is None  # No more matching events
            sub.close()

        self._run(_test())

    def test_replay_buffer_size_limit(self):
        """Replay buffer respects max size (oldest events evicted)."""

        async def _test():
            bus = EventBus(replay_size=3)
            for i in range(5):
                await bus.publish(
                    StreamEvent(type=StreamEventType.TOOL_CALL, data={"n": i}),
                )

            sub = bus.subscribe(replay=True)
            events = []
            for _ in range(5):
                e = await sub.get(timeout=0.1)
                if e is None:
                    break
                events.append(e)

            # Only last 3 events should be in the buffer
            assert len(events) == 3
            assert events[0].data == {"n": 2}
            assert events[1].data == {"n": 3}
            assert events[2].data == {"n": 4}
            sub.close()

        self._run(_test())

    def test_replay_plus_live_events(self):
        """Replay events are followed by live events."""

        async def _test():
            bus = EventBus(replay_size=50)
            await bus.publish(
                StreamEvent(
                    type=StreamEventType.TOOL_CALL,
                    data={"n": "replay"},
                ),
            )

            sub = bus.subscribe(replay=True)

            # Get replay event
            e1 = await sub.get(timeout=0.5)
            assert e1 is not None
            assert e1.data == {"n": "replay"}

            # Publish a live event
            await bus.publish(
                StreamEvent(
                    type=StreamEventType.REASONING,
                    data={"n": "live"},
                ),
            )
            e2 = await sub.get(timeout=0.5)
            assert e2 is not None
            assert e2.data == {"n": "live"}
            sub.close()

        self._run(_test())

    def test_default_replay_size(self):
        """Default EventBus has replay_size=100."""
        bus = EventBus()
        assert bus._replay_size == 100

    def test_existing_behavior_unchanged(self):
        """Existing subscribe() without replay still works as before."""

        async def _test():
            bus = EventBus()
            sub = bus.subscribe()

            await bus.publish(
                StreamEvent(type=StreamEventType.TOOL_CALL, data={"x": 1}),
            )
            e = await sub.get(timeout=0.5)
            assert e is not None
            assert e.data == {"x": 1}
            sub.close()

        self._run(_test())

    def test_replay_buffer_empty(self):
        """Replay with empty buffer yields no events."""

        async def _test():
            bus = EventBus(replay_size=10)
            sub = bus.subscribe(replay=True)
            e = await sub.get(timeout=0.1)
            assert e is None
            sub.close()

        self._run(_test())

    def test_replay_buffer_with_source_filter(self):
        """Replay filter by source DID works correctly."""

        async def _test():
            bus = EventBus(replay_size=50)
            await bus.publish(
                StreamEvent(
                    type=StreamEventType.TOOL_CALL,
                    source="did:roar:agent:a",
                    data={"from": "a"},
                ),
            )
            await bus.publish(
                StreamEvent(
                    type=StreamEventType.TOOL_CALL,
                    source="did:roar:agent:b",
                    data={"from": "b"},
                ),
            )

            filt = StreamFilter(source_dids=["did:roar:agent:a"])
            sub = bus.subscribe(filter_spec=filt, replay=True)

            e1 = await sub.get(timeout=0.5)
            e2 = await sub.get(timeout=0.1)

            assert e1 is not None
            assert e1.data == {"from": "a"}
            assert e2 is None
            sub.close()

        self._run(_test())


if __name__ == "__main__":
    unittest.main()
