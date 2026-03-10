# -*- coding: utf-8 -*-
"""Tests for rate limiting."""

import time

from prowlrbot.app.rate_limit import RateLimiter


def test_allows_within_limit():
    limiter = RateLimiter(max_requests=5, window_seconds=60)
    for _ in range(5):
        assert limiter.allow("client1") is True


def test_blocks_over_limit():
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        limiter.allow("client1")
    assert limiter.allow("client1") is False


def test_different_clients_independent():
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    limiter.allow("client1")
    limiter.allow("client1")
    assert limiter.allow("client1") is False
    assert limiter.allow("client2") is True


def test_window_resets():
    limiter = RateLimiter(max_requests=1, window_seconds=0.1)
    assert limiter.allow("client1") is True
    assert limiter.allow("client1") is False
    time.sleep(0.15)
    assert limiter.allow("client1") is True
