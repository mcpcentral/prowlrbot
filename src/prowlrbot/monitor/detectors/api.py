# -*- coding: utf-8 -*-
"""REST API endpoint detector."""

from __future__ import annotations

import json
from typing import Dict, Optional

import httpx

from prowlrbot.monitor.detectors.base import BaseDetector, DetectionResult
from prowlrbot.monitor.diff import diff_text


def _extract_json_path(data: object, path: str) -> str:
    """Simple dot-notation JSON path extraction (e.g. 'data.status')."""
    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            current = current[int(part)]
        else:
            return str(current)
    return json.dumps(current) if not isinstance(current, str) else current


class APIDetector(BaseDetector):
    """Monitors a REST API endpoint for changes."""

    def __init__(
        self,
        url: str,
        method: str = "GET",
        expected_status: int = 200,
        json_path: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.url = url
        self.method = method.upper()
        self.expected_status = expected_status
        self.json_path = json_path
        self.headers = headers or {}
        self.body = body
        self._client = client

    async def detect(
        self,
        last_content: Optional[str] = None,
    ) -> DetectionResult:
        try:
            from prowlrbot.security.url_validator import validate_outbound_url

            allowed, reason = validate_outbound_url(self.url)
            if not allowed:
                return DetectionResult(
                    changed=False,
                    content=None,
                    error=f"URL blocked: {reason}",
                )

            client = self._client or httpx.AsyncClient()
            try:
                resp = await client.request(
                    self.method,
                    self.url,
                    headers=self.headers,
                    content=self.body,
                    timeout=30,
                )
            finally:
                if self._client is None:
                    await client.aclose()

            if resp.status_code != self.expected_status:
                return DetectionResult(
                    content=None,
                    changed=False,
                    error=f"Unexpected status {resp.status_code} (expected {self.expected_status})",
                )

            content = resp.text
            if self.json_path:
                try:
                    data = resp.json()
                    content = _extract_json_path(data, self.json_path)
                except (json.JSONDecodeError, ValueError):
                    pass

            result = diff_text(last_content, content)
            return DetectionResult(
                content=content,
                changed=result.changed,
                diff_summary=result.summary,
            )
        except Exception as exc:
            return DetectionResult(
                content=None,
                changed=False,
                diff_summary="",
                error=str(exc),
            )
