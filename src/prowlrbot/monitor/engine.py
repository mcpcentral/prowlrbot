# -*- coding: utf-8 -*-
"""Core MonitorEngine — schedule and execute monitors."""
from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional

from prowlrbot.monitor.config import AnyMonitorConfig, WebMonitorConfig, APIMonitorConfig
from prowlrbot.monitor.detectors.base import BaseDetector, DetectionResult
from prowlrbot.monitor.detectors.web import WebDetector
from prowlrbot.monitor.detectors.api import APIDetector
from prowlrbot.monitor.notifications.base import BaseNotifier
from prowlrbot.monitor.storage import MonitorStorage

logger = logging.getLogger(__name__)


class MonitorEngine:
    """Manages a collection of monitors and executes them."""

    def __init__(
        self,
        storage: Optional[MonitorStorage] = None,
        notifiers: Optional[List[BaseNotifier]] = None,
    ) -> None:
        self.storage = storage or MonitorStorage()
        self.notifiers = notifiers or []
        self._configs: Dict[str, AnyMonitorConfig] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def add(self, config: AnyMonitorConfig) -> None:
        """Register a monitor configuration."""
        self._configs[config.name] = config

    def remove(self, name: str) -> bool:
        """Remove a monitor. Returns True if it existed."""
        if name in self._configs:
            del self._configs[name]
            self.storage.delete(name)
            return True
        return False

    def list(self) -> List[AnyMonitorConfig]:
        """Return all registered monitor configs."""
        return list(self._configs.values())

    def _make_detector(self, config: AnyMonitorConfig) -> BaseDetector:
        """Create the appropriate detector for a config."""
        if isinstance(config, WebMonitorConfig):
            return WebDetector(
                url=config.url,
                css_selector=config.css_selector,
                headers=config.headers,
            )
        elif isinstance(config, APIMonitorConfig):
            return APIDetector(
                url=config.url,
                method=config.method,
                expected_status=config.expected_status,
                json_path=config.json_path,
                headers=config.headers,
                body=config.body,
            )
        raise ValueError(f"Unknown config type: {type(config)}")

    async def run_once(self, name: str) -> DetectionResult:
        """Run a single check for the named monitor."""
        config = self._configs.get(name)
        if config is None:
            raise KeyError(f"No monitor named '{name}'")

        detector = self._make_detector(config)

        # Load last seen content
        snapshot = self.storage.load(name)
        last_content = snapshot.content if snapshot else None

        result = await detector.detect(last_content)

        # Persist new content on success
        if result.content is not None and result.error is None:
            self.storage.save(name, result.content)

        # Notify on change
        if result.changed and not result.error:
            for notifier in self.notifiers:
                try:
                    await notifier.notify(name, result.diff_summary, result.content)
                except Exception:
                    logger.exception("Notifier failed for %s", name)

        return result

    async def _loop(self) -> None:
        """Run all enabled monitors on their intervals."""
        # Track next-run times
        next_run: Dict[str, float] = {}
        loop = asyncio.get_event_loop()
        for name, config in self._configs.items():
            if config.enabled:
                next_run[name] = loop.time()

        while self._running:
            now = loop.time()
            for name, config in list(self._configs.items()):
                if not config.enabled or name not in next_run:
                    continue
                if now >= next_run[name]:
                    try:
                        await self.run_once(name)
                    except Exception:
                        logger.exception("Monitor %s failed", name)
                    next_run[name] = now + config.interval_seconds
            await asyncio.sleep(1)

    async def start(self) -> None:
        """Start the monitoring loop."""
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        """Stop the monitoring loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
