# -*- coding: utf-8 -*-
"""Tests for WebSocket endpoint."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from prowlrbot.app.websocket import create_websocket_router
from prowlrbot.dashboard.events import EventBus


def test_websocket_requires_session_id():
    bus = EventBus()
    app = FastAPI()
    app.include_router(create_websocket_router(bus))

    client = TestClient(app)
    # Missing session_id — should close with error
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/dashboard") as ws:
            pass


def test_websocket_accepts_with_session_id():
    bus = EventBus()
    app = FastAPI()
    app.include_router(create_websocket_router(bus))

    client = TestClient(app)
    # Should successfully connect
    with client.websocket_connect("/ws/dashboard?session_id=test") as ws:
        # Connection established — just close cleanly
        pass
