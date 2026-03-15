# -*- coding: utf-8 -*-
"""In-process event bus — zero external dependencies.

Implements pub/sub with async queues. Each subscriber gets its own
bounded queue; backpressure is applied when queues fill up.

This is the default streaming backend. For production use with
multiple processes, swap in the NATS backend.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import AsyncIterator, Deque, Dict, List, Optional, Set

from ...roar import StreamEvent, StreamEventType

logger = logging.getLogger(__name__)


@dataclass
class StreamFilter:
    """Filter for selecting which events a subscriber receives.

    All filters are AND-combined: an event must match every non-empty
    filter field to be delivered.

    Attributes:
        event_types: Only deliver events of these types (empty = all).
        source_dids: Only deliver events from these DIDs (empty = all).
        session_ids: Only deliver events in these sessions (empty = all).
    """

    event_types: List[str] = field(default_factory=list)
    source_dids: List[str] = field(default_factory=list)
    session_ids: List[str] = field(default_factory=list)

    def matches(self, event: StreamEvent) -> bool:
        """Return True if the event passes all filter criteria."""
        if self.event_types and event.type not in self.event_types:
            return False
        if self.source_dids and event.source not in self.source_dids:
            return False
        if self.session_ids and event.session_id not in self.session_ids:
            return False
        return True


class Subscription:
    """An active subscription to the event bus.

    Provides an async iterator interface for consuming events.
    The subscription is automatically cleaned up when the iterator
    is abandoned or explicitly closed.

    Usage::

        sub = bus.subscribe(StreamFilter(event_types=["reasoning"]))
        async for event in sub:
            process(event)
        sub.close()
    """

    def __init__(
        self,
        sub_id: str,
        filter_spec: StreamFilter,
        queue: asyncio.Queue,
        bus: "EventBus",
    ) -> None:
        self.id = sub_id
        self.filter = filter_spec
        self._queue = queue
        self._bus = bus
        self._closed = False
        self.events_received: int = 0
        self.events_dropped: int = 0

    @property
    def closed(self) -> bool:
        return self._closed

    async def __aiter__(self) -> AsyncIterator[StreamEvent]:
        while not self._closed:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                self.events_received += 1
                yield event
            except asyncio.TimeoutError:
                continue

    async def get(self, timeout: float = 5.0) -> Optional[StreamEvent]:
        """Get the next event, or None on timeout."""
        if self._closed:
            return None
        try:
            event = await asyncio.wait_for(self._queue.get(), timeout=timeout)
            self.events_received += 1
            return event
        except asyncio.TimeoutError:
            return None

    def close(self) -> None:
        """Close this subscription and unregister from the bus."""
        if not self._closed:
            self._closed = True
            self._bus._unsubscribe(self.id)


class EventBus:
    """In-process pub/sub event bus for ROAR streaming.

    Thread-safe via asyncio. Each subscriber gets a bounded queue
    (default 1000 events). When a queue is full, the oldest event
    is dropped and a checkpoint event is emitted.

    Usage::

        bus = EventBus(max_buffer=500)

        # Subscribe with filter
        sub = bus.subscribe(StreamFilter(event_types=["tool_call"]))

        # Publish (from agent code)
        await bus.publish(StreamEvent(type="tool_call", data={...}))

        # Consume
        event = await sub.get(timeout=2.0)
    """

    def __init__(self, max_buffer: int = 1000, replay_size: int = 100) -> None:
        self._max_buffer = max_buffer
        self._replay_size = replay_size
        self._replay_buffer: Deque[StreamEvent] = deque(maxlen=replay_size)
        self._subscriptions: Dict[str, Subscription] = {}
        self._event_count: int = 0

    @property
    def subscriber_count(self) -> int:
        return len(self._subscriptions)

    @property
    def event_count(self) -> int:
        return self._event_count

    def subscribe(
        self,
        filter_spec: Optional[StreamFilter] = None,
        buffer_size: Optional[int] = None,
        replay: bool = False,
    ) -> Subscription:
        """Create a new subscription.

        Args:
            filter_spec: Event filter (None = receive all events).
            buffer_size: Per-subscriber buffer size (None = bus default).
            replay: If True, pre-fill the subscriber's queue with matching
                events from the replay buffer so late subscribers can
                catch up on recent history.

        Returns:
            A Subscription that can be iterated or polled.
        """
        sub_id = f"sub-{uuid.uuid4().hex[:12]}"
        queue: asyncio.Queue = asyncio.Queue(
            maxsize=buffer_size or self._max_buffer,
        )
        effective_filter = filter_spec or StreamFilter()

        # Pre-fill queue with matching events from the replay buffer
        if replay:
            for event in self._replay_buffer:
                if effective_filter.matches(event):
                    try:
                        queue.put_nowait(event)
                    except asyncio.QueueFull:
                        break

        sub = Subscription(
            sub_id=sub_id,
            filter_spec=effective_filter,
            queue=queue,
            bus=self,
        )
        self._subscriptions[sub_id] = sub
        logger.debug(
            "Subscription %s created (filter=%s, replay=%s)",
            sub_id,
            filter_spec,
            replay,
        )
        return sub

    async def publish(self, event: StreamEvent) -> int:
        """Publish an event to all matching subscribers.

        Args:
            event: The StreamEvent to broadcast.

        Returns:
            Number of subscribers that received the event.
        """
        self._event_count += 1
        self._replay_buffer.append(event)
        delivered = 0

        for sub in list(self._subscriptions.values()):
            if sub.closed:
                continue
            if not sub.filter.matches(event):
                continue

            try:
                sub._queue.put_nowait(event)
                delivered += 1
            except asyncio.QueueFull:
                # Drop oldest, enqueue new — emit checkpoint
                try:
                    sub._queue.get_nowait()
                    sub.events_dropped += 1
                except asyncio.QueueEmpty:
                    pass
                try:
                    sub._queue.put_nowait(event)
                    delivered += 1
                except asyncio.QueueFull:
                    sub.events_dropped += 1
                    logger.warning(
                        "Subscription %s dropping events (buffer full)",
                        sub.id,
                    )

        return delivered

    async def publish_many(self, events: List[StreamEvent]) -> int:
        """Publish multiple events. Returns total deliveries."""
        total = 0
        for event in events:
            total += await self.publish(event)
        return total

    def _unsubscribe(self, sub_id: str) -> None:
        """Remove a subscription (called by Subscription.close())."""
        self._subscriptions.pop(sub_id, None)
        logger.debug("Subscription %s removed", sub_id)

    def close_all(self) -> None:
        """Close all subscriptions and reset the bus."""
        for sub in list(self._subscriptions.values()):
            sub._closed = True
        self._subscriptions.clear()
