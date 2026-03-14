# -*- coding: utf-8 -*-
"""Tests for prowlrbot.monitor.engine."""

import asyncio
import json
from unittest.mock import patch

import pytest
import httpx

from prowlrbot.monitor.config import WebMonitorConfig, APIMonitorConfig
from prowlrbot.monitor.engine import MonitorEngine
from prowlrbot.monitor.notifications.webhook import WebhookNotifier
from prowlrbot.monitor.storage import MonitorStorage


@pytest.fixture
def storage(tmp_path):
    s = MonitorStorage(db_path=tmp_path / "test.db")
    yield s
    s.close()


@pytest.fixture
def engine(storage):
    return MonitorEngine(storage=storage)


class TestMonitorEngine:
    def test_add_and_list(self, engine):
        config = WebMonitorConfig(name="test", url="https://example.com")
        engine.add(config)
        assert len(engine.list()) == 1
        assert engine.list()[0].name == "test"

    def test_remove(self, engine):
        config = WebMonitorConfig(name="test", url="https://example.com")
        engine.add(config)
        assert engine.remove("test") is True
        assert len(engine.list()) == 0

    def test_remove_nonexistent(self, engine):
        assert engine.remove("nope") is False

    @pytest.mark.asyncio
    async def test_run_once_first_check(self, engine):
        transport = httpx.MockTransport(
            lambda req: httpx.Response(200, text="<h1>Hello</h1>")
        )
        config = WebMonitorConfig(
            name="web1",
            url="https://example.com",
            css_selector="h1",
        )
        engine.add(config)

        def patched(cfg):
            from prowlrbot.monitor.detectors.web import WebDetector

            return WebDetector(
                url=cfg.url,
                css_selector=cfg.css_selector,
                client=httpx.AsyncClient(transport=transport),
            )

        engine._make_detector = patched

        with patch(
            "prowlrbot.security.url_validator.validate_outbound_url",
            return_value=(True, "OK"),
        ):
            result = await engine.run_once("web1")
        assert result.changed is True
        assert result.content == "Hello"

        # Check storage was updated
        snap = engine.storage.load("web1")
        assert snap is not None
        assert snap.content == "Hello"

    @pytest.mark.asyncio
    async def test_run_once_no_change(self, engine):
        transport = httpx.MockTransport(
            lambda req: httpx.Response(200, text="<h1>Hello</h1>")
        )
        config = WebMonitorConfig(
            name="web1",
            url="https://example.com",
            css_selector="h1",
        )
        engine.add(config)
        engine.storage.save("web1", "Hello")

        def patched(cfg):
            from prowlrbot.monitor.detectors.web import WebDetector

            return WebDetector(
                url=cfg.url,
                css_selector=cfg.css_selector,
                client=httpx.AsyncClient(transport=transport),
            )

        engine._make_detector = patched

        with patch(
            "prowlrbot.security.url_validator.validate_outbound_url",
            return_value=(True, "OK"),
        ):
            result = await engine.run_once("web1")
        assert result.changed is False

    @pytest.mark.asyncio
    async def test_run_once_unknown_monitor(self, engine):
        with pytest.raises(KeyError, match="No monitor named"):
            await engine.run_once("nonexistent")

    @pytest.mark.asyncio
    async def test_run_once_triggers_notifier(self, storage):
        notified = []

        class FakeNotifier:
            async def notify(self, name, summary, content=None):
                notified.append({"name": name, "summary": summary})
                return True

        engine = MonitorEngine(storage=storage, notifiers=[FakeNotifier()])

        transport = httpx.MockTransport(
            lambda req: httpx.Response(200, text="<h1>Changed</h1>")
        )
        config = WebMonitorConfig(
            name="web1",
            url="https://example.com",
            css_selector="h1",
        )
        engine.add(config)

        def patched(cfg):
            from prowlrbot.monitor.detectors.web import WebDetector

            return WebDetector(
                url=cfg.url,
                css_selector=cfg.css_selector,
                client=httpx.AsyncClient(transport=transport),
            )

        engine._make_detector = patched

        with patch(
            "prowlrbot.security.url_validator.validate_outbound_url",
            return_value=(True, "OK"),
        ):
            await engine.run_once("web1")
        assert len(notified) == 1
        assert notified[0]["name"] == "web1"

    @pytest.mark.asyncio
    async def test_start_and_stop(self, engine):
        config = WebMonitorConfig(
            name="web1",
            url="https://example.com",
            interval="1s",
        )
        engine.add(config)

        # Override detector to avoid real HTTP
        run_count = {"n": 0}

        def patched(cfg):
            from prowlrbot.monitor.detectors.base import DetectionResult

            class CountDetector:
                async def detect(self, last_content=None):
                    run_count["n"] += 1
                    return DetectionResult(content="ok", changed=False)

            return CountDetector()

        engine._make_detector = patched

        await engine.start()
        await asyncio.sleep(0.2)  # let loop tick
        await engine.stop()
        assert run_count["n"] >= 1


class TestMonitorEngineAPI:
    @pytest.mark.asyncio
    async def test_api_monitor_run_once(self, storage):
        from unittest.mock import patch

        engine = MonitorEngine(storage=storage)
        payload = json.dumps({"data": {"status": "up"}})
        transport = httpx.MockTransport(lambda req: httpx.Response(200, text=payload))
        config = APIMonitorConfig(
            name="api1",
            url="https://api.example.com/status",
            json_path="data.status",
        )
        engine.add(config)

        def patched(cfg):
            from prowlrbot.monitor.detectors.api import APIDetector

            return APIDetector(
                url=cfg.url,
                json_path=cfg.json_path,
                client=httpx.AsyncClient(transport=transport),
            )

        engine._make_detector = patched

        with patch(
            "prowlrbot.security.url_validator.validate_outbound_url",
            return_value=(True, "OK"),
        ):
            result = await engine.run_once("api1")
        assert result.changed is True
        assert result.content == "up"
