# -*- coding: utf-8 -*-
"""ROAR Protocol SDK — Streaming Layer (Layer 5).

Provides real-time event streaming with in-process and external backends,
backpressure control, and idempotent delivery.

Usage::

    from prowlrbot.protocols.sdk.streaming import EventBus, StreamFilter

    bus = EventBus()
    sub = bus.subscribe(StreamFilter(event_types=["reasoning", "tool_call"]))

    # Publish events
    bus.publish(event)

    # Consume
    async for event in sub:
        print(event)
"""
from .local import EventBus, StreamFilter, Subscription
from .backpressure import AIMDController
from .dedup import IdempotencyGuard

__all__ = [
    "EventBus",
    "StreamFilter",
    "Subscription",
    "AIMDController",
    "IdempotencyGuard",
]
