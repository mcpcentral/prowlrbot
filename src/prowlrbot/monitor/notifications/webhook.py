# -*- coding: utf-8 -*-
"""Webhook notifier — POST JSON to a configured URL."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional

import httpx

from prowlrbot.monitor.notifications.base import BaseNotifier


class WebhookNotifier(BaseNotifier):
    """Sends change notifications as JSON POST requests."""

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.url = url
        self.headers = headers or {}
        self._client = client

    async def notify(
        self,
        monitor_name: str,
        summary: str,
        content: Optional[str] = None,
    ) -> bool:
        payload = {
            "monitor": monitor_name,
            "summary": summary,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            client = self._client or httpx.AsyncClient()
            try:
                resp = await client.post(
                    self.url,
                    json=payload,
                    headers=self.headers,
                    timeout=15,
                )
                return 200 <= resp.status_code < 300
            finally:
                if self._client is None:
                    await client.aclose()
        except Exception:
            return False
