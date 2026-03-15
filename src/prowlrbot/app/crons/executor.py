# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from .models import CronJobSpec

logger = logging.getLogger(__name__)


async def _award_xp_background(
    entity_id: str,
    category: str,
    reason: str,
    amount: int = 5,
) -> None:
    """Fire-and-forget XP award via internal HTTP. Never raises."""
    try:
        import httpx  # noqa: PLC0415

        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(
                "http://localhost:8088/api/gamification/xp",
                json={
                    "entity_id": entity_id,
                    "entity_type": "agent",
                    "amount": amount,
                    "category": category,
                    "reason": reason,
                },
            )
    except Exception:
        pass  # XP is best-effort, never block cron execution


class CronExecutor:
    def __init__(self, *, runner: Any, channel_manager: Any):
        self._runner = runner
        self._channel_manager = channel_manager

    async def execute(self, job: CronJobSpec) -> None:
        """Execute one job once.

        - task_type text: send fixed text to channel
        - task_type agent: ask agent with prompt, send reply to channel (
            stream_query + send_event)
        """
        target_user_id = job.dispatch.target.user_id
        target_session_id = job.dispatch.target.session_id
        dispatch_meta: Dict[str, Any] = dict(job.dispatch.meta or {})
        logger.info(
            "cron execute: job_id=%s channel=%s task_type=%s "
            "target_user_id=%s target_session_id=%s",
            job.id,
            job.dispatch.channel,
            job.task_type,
            target_user_id[:40] if target_user_id else "",
            target_session_id[:40] if target_session_id else "",
        )

        if job.task_type == "text" and job.text:
            logger.info(
                "cron send_text: job_id=%s channel=%s len=%s",
                job.id,
                job.dispatch.channel,
                len(job.text or ""),
            )
            await self._channel_manager.send_text(
                channel=job.dispatch.channel,
                user_id=target_user_id,
                session_id=target_session_id,
                text=job.text.strip(),
                meta=dispatch_meta,
            )
            return

        # agent: run request as the dispatch target user so context matches
        logger.info(
            "cron agent: job_id=%s channel=%s stream_query then send_event",
            job.id,
            job.dispatch.channel,
        )
        assert job.request is not None
        req: Dict[str, Any] = job.request.model_dump(mode="json")
        req["user_id"] = target_user_id or "cron"
        req["session_id"] = target_session_id or f"cron:{job.id}"

        async def _run() -> None:
            async for event in self._runner.stream_query(req):
                await self._channel_manager.send_event(
                    channel=job.dispatch.channel,
                    user_id=target_user_id,
                    session_id=target_session_id,
                    event=event,
                    meta=dispatch_meta,
                )

        await asyncio.wait_for(_run(), timeout=job.runtime.timeout_seconds)
        asyncio.create_task(
            _award_xp_background(
                entity_id=target_session_id or f"cron:{job.id}",
                category="cron_complete",
                reason=f"Completed cron job {job.id}",
                amount=5,
            ),
        )
