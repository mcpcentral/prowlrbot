# -*- coding: utf-8 -*-
"""Core MonitorEngine — schedule and execute monitors."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Dict, List, Optional

from prowlrbot.monitor.config import (
    AnyMonitorConfig,
    WebMonitorConfig,
    APIMonitorConfig,
)
from prowlrbot.monitor.detectors.base import BaseDetector, DetectionResult
from prowlrbot.monitor.detectors.web import WebDetector
from prowlrbot.monitor.detectors.api import APIDetector
from prowlrbot.monitor.notifications.base import BaseNotifier
from prowlrbot.monitor.storage import MonitorStorage

logger = logging.getLogger(__name__)

# APScheduler is optional — only needed for schedule_monitor().
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger

    _HAS_APSCHEDULER = True
except ImportError:  # pragma: no cover
    _HAS_APSCHEDULER = False


class MonitorEngine:
    """Manages a collection of monitors and executes them.

    Supports two execution modes:
    1. Built-in async loop (start/stop) — lightweight, no dependencies.
    2. APScheduler integration (schedule_monitor) — integrates with
       the existing CronManager scheduler for production use.
    """

    def __init__(
        self,
        storage: Optional[MonitorStorage] = None,
        storage_path: Optional[str] = None,
        notifiers: Optional[List[BaseNotifier]] = None,
    ) -> None:
        if storage is not None:
            self.storage = storage
        elif storage_path is not None:
            self.storage = MonitorStorage(db_path=storage_path)
        else:
            self.storage = MonitorStorage()
        self.notifiers = notifiers or []
        self._configs: Dict[str, AnyMonitorConfig] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._scheduler: Optional[AsyncIOScheduler] = None  # type: ignore[assignment]
        self._scheduled_jobs: Dict[str, str] = {}  # job_id -> monitor_name

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
                    await notifier.notify(
                        name,
                        result.diff_summary,
                        result.content,
                    )
                except Exception:
                    logger.exception("Notifier failed for %s", name)

        return result

    async def _loop(self) -> None:
        """Run all enabled monitors on their intervals."""
        # Track next-run times
        next_run: Dict[str, float] = {}
        loop = asyncio.get_running_loop()
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

    # ------------------------------------------------------------------
    # APScheduler integration
    # ------------------------------------------------------------------

    def _ensure_scheduler(self) -> None:
        """Create and start the APScheduler instance if not already running."""
        if not _HAS_APSCHEDULER:
            raise RuntimeError(
                "APScheduler is required for schedule_monitor(). "
                "Install it with: pip install apscheduler",
            )
        if self._scheduler is None:
            self._scheduler = AsyncIOScheduler()
            self._scheduler.start()

    def schedule_monitor(
        self,
        url: str,
        interval_minutes: int = 60,
        monitor_type: str = "web",
        name: Optional[str] = None,
        **kwargs: object,
    ) -> str:
        """Schedule a monitor to run at a fixed interval via APScheduler.

        Args:
            url: The URL to monitor.
            interval_minutes: Check interval in minutes.
            monitor_type: Either 'web' or 'api'.
            name: Optional monitor name. Auto-generated if not provided.
            **kwargs: Extra config fields passed to the monitor config.

        Returns:
            The APScheduler job ID.
        """
        self._ensure_scheduler()

        if name is None:
            name = f"mon_{uuid.uuid4().hex[:8]}"

        interval_str = f"{interval_minutes}m"

        if monitor_type == "api":
            config: AnyMonitorConfig = APIMonitorConfig(
                name=name,
                url=url,
                interval=interval_str,
                **kwargs,  # type: ignore[arg-type]
            )
        else:
            config = WebMonitorConfig(
                name=name,
                url=url,
                interval=interval_str,
                **kwargs,  # type: ignore[arg-type]
            )

        self.add(config)

        # Wrap the async run_once in a sync callback for APScheduler 3.x
        async def _check() -> None:
            try:
                await self.run_once(name)
            except Exception:
                logger.exception("Scheduled monitor %s failed", name)

        def _run_check() -> None:
            loop = asyncio.get_running_loop()
            loop.create_task(_check())

        trigger = IntervalTrigger(minutes=interval_minutes)
        job = self._scheduler.add_job(_run_check, trigger=trigger, id=name)
        self._scheduled_jobs[job.id] = name
        logger.info(
            "Scheduled monitor %s every %d minutes for %s",
            name,
            interval_minutes,
            url,
        )
        return job.id

    def unschedule_monitor(self, job_id: str) -> bool:
        """Remove a scheduled monitor job.

        Args:
            job_id: The APScheduler job ID returned by schedule_monitor().

        Returns:
            True if the job was removed, False if not found.
        """
        if self._scheduler is None:
            return False
        try:
            self._scheduler.remove_job(job_id)
            monitor_name = self._scheduled_jobs.pop(job_id, None)
            if monitor_name:
                self.remove(monitor_name)
            return True
        except Exception:
            return False

    def get_scheduled_monitors(self) -> int:
        """Return the number of currently scheduled monitor jobs."""
        return len(self._scheduled_jobs)
