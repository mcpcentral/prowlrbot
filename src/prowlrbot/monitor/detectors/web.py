# -*- coding: utf-8 -*-
"""Web page detector — fetch URL, optionally extract via CSS selector, diff."""

from __future__ import annotations

import re
from typing import Dict, Optional

import httpx

from prowlrbot.monitor.detectors.base import BaseDetector, DetectionResult
from prowlrbot.monitor.diff import diff_text


def _css_extract(html: str, selector: str) -> str:
    """Best-effort CSS extraction using selectolax if available, else regex tag match."""
    try:
        from selectolax.parser import HTMLParser  # type: ignore[import-untyped]

        tree = HTMLParser(html)
        nodes = tree.css(selector)
        return "\n".join(node.text(strip=True) for node in nodes)
    except ImportError:
        pass

    # Regex fallback: handle simple tag selectors like "h1", "div", "p"
    tag = selector.strip()
    if re.match(r"^[a-zA-Z][a-zA-Z0-9]*$", tag):
        pattern = rf"<{tag}[^>]*>(.*?)</{tag}>"
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        return "\n".join(m.strip() for m in matches)

    # For class/id selectors without selectolax, return full HTML
    return html


class WebDetector(BaseDetector):
    """Fetches a web page and detects content changes."""

    def __init__(
        self,
        url: str,
        css_selector: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.url = url
        self.css_selector = css_selector
        self.headers = headers or {}
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
                resp = await client.get(
                    self.url,
                    headers=self.headers,
                    timeout=30,
                )
                resp.raise_for_status()
            finally:
                if self._client is None:
                    await client.aclose()

            html = resp.text
            content = (
                _css_extract(html, self.css_selector) if self.css_selector else html
            )

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
