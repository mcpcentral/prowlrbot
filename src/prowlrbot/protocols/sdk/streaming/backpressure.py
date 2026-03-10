# -*- coding: utf-8 -*-
"""AIMD (Additive Increase / Multiplicative Decrease) backpressure controller.

The same algorithm TCP uses for congestion control, adapted for event
streaming. The controller adjusts the send rate based on consumer feedback:

- On success: rate += additive_increase (linear growth)
- On drop/timeout: rate *= multiplicative_decrease (exponential backoff)

This prevents fast producers from overwhelming slow consumers while
maximizing throughput when capacity is available.

Ref: Jacobson, V. (1988). "Congestion Avoidance and Control". SIGCOMM.
"""
from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class AIMDController:
    """AIMD backpressure controller for event streaming.

    Attributes:
        rate: Current send rate (events per second).
        min_rate: Floor — never go below this rate.
        max_rate: Ceiling — never exceed this rate.
        additive_increase: Added to rate on each success window.
        multiplicative_decrease: Rate multiplied by this on congestion (0-1).
        window_size: Number of events before adjusting rate.
    """

    rate: float = 100.0
    min_rate: float = 1.0
    max_rate: float = 10000.0
    additive_increase: float = 10.0
    multiplicative_decrease: float = 0.5
    window_size: int = 50

    _success_count: int = 0
    _drop_count: int = 0
    _last_adjustment: float = 0.0

    def __post_init__(self):
        self._last_adjustment = time.time()

    def on_success(self) -> None:
        """Record a successful delivery."""
        self._success_count += 1
        if self._success_count >= self.window_size:
            self._increase()
            self._success_count = 0

    def on_drop(self) -> None:
        """Record a dropped event (consumer can't keep up)."""
        self._drop_count += 1
        self._decrease()
        self._success_count = 0

    @property
    def delay(self) -> float:
        """Delay in seconds between events at the current rate."""
        return 1.0 / self.rate if self.rate > 0 else 1.0

    @property
    def stats(self) -> dict:
        """Return current controller statistics."""
        return {
            "rate": round(self.rate, 2),
            "delay_ms": round(self.delay * 1000, 2),
            "successes": self._success_count,
            "drops": self._drop_count,
            "last_adjustment": self._last_adjustment,
        }

    def _increase(self) -> None:
        """Additive increase — linear growth."""
        self.rate = min(self.rate + self.additive_increase, self.max_rate)
        self._last_adjustment = time.time()

    def _decrease(self) -> None:
        """Multiplicative decrease — exponential backoff."""
        self.rate = max(
            self.rate * self.multiplicative_decrease, self.min_rate
        )
        self._last_adjustment = time.time()

    def reset(self) -> None:
        """Reset to initial state."""
        self.rate = 100.0
        self._success_count = 0
        self._drop_count = 0
        self._last_adjustment = time.time()
