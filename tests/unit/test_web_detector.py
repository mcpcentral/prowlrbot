# -*- coding: utf-8 -*-
"""Tests for prowlrbot.monitor.detectors.web."""

import pytest
import httpx
from unittest.mock import patch

from prowlrbot.monitor.detectors.web import WebDetector, _css_extract


class TestCssExtract:
    def test_simple_tag(self):
        html = "<html><body><h1>Hello World</h1></body></html>"
        assert _css_extract(html, "h1") == "Hello World"

    def test_multiple_tags(self):
        html = "<p>One</p><p>Two</p>"
        result = _css_extract(html, "p")
        assert "One" in result
        assert "Two" in result

    def test_no_match(self):
        html = "<div>content</div>"
        result = _css_extract(html, "h1")
        assert result == ""

    def test_no_selector_returns_html(self):
        html = "<div>content</div>"
        # Complex selector without selectolax falls back to full html
        result = _css_extract(html, ".my-class")
        assert result == html


@pytest.mark.asyncio
class TestWebDetector:
    """WebDetector tests patch URL validation so mock transport is used (no real DNS)."""

    @pytest.fixture(autouse=True)
    def _allow_example_url(self):
        with patch(
            "prowlrbot.security.url_validator.validate_outbound_url",
            return_value=(True, "OK"),
        ):
            yield

    async def test_detect_first_run(self):
        """First run should always report changed."""
        transport = httpx.MockTransport(
            lambda req: httpx.Response(200, text="<h1>Hello</h1>")
        )
        client = httpx.AsyncClient(transport=transport)
        detector = WebDetector(
            url="https://example.com",
            css_selector="h1",
            client=client,
        )
        result = await detector.detect(last_content=None)
        assert result.changed is True
        assert result.content == "Hello"
        assert result.error is None
        await client.aclose()

    async def test_detect_no_change(self):
        transport = httpx.MockTransport(
            lambda req: httpx.Response(200, text="<h1>Hello</h1>")
        )
        client = httpx.AsyncClient(transport=transport)
        detector = WebDetector(
            url="https://example.com",
            css_selector="h1",
            client=client,
        )
        result = await detector.detect(last_content="Hello")
        assert result.changed is False
        assert result.content == "Hello"
        await client.aclose()

    async def test_detect_change(self):
        transport = httpx.MockTransport(
            lambda req: httpx.Response(200, text="<h1>New Title</h1>")
        )
        client = httpx.AsyncClient(transport=transport)
        detector = WebDetector(
            url="https://example.com",
            css_selector="h1",
            client=client,
        )
        result = await detector.detect(last_content="Old Title")
        assert result.changed is True
        assert result.content == "New Title"
        await client.aclose()

    async def test_detect_without_selector(self):
        html = "<html><body>Full page</body></html>"
        transport = httpx.MockTransport(lambda req: httpx.Response(200, text=html))
        client = httpx.AsyncClient(transport=transport)
        detector = WebDetector(url="https://example.com", client=client)
        result = await detector.detect(last_content=None)
        assert result.content == html
        assert result.changed is True
        await client.aclose()

    async def test_detect_http_error(self):
        transport = httpx.MockTransport(lambda req: httpx.Response(500, text="error"))
        client = httpx.AsyncClient(transport=transport)
        detector = WebDetector(url="https://example.com", client=client)
        result = await detector.detect(last_content=None)
        assert result.error is not None
        assert result.changed is False
        await client.aclose()

    async def test_detect_with_headers(self):
        def handler(req):
            assert req.headers.get("Authorization") == "Bearer token"
            return httpx.Response(200, text="<p>ok</p>")

        transport = httpx.MockTransport(handler)
        client = httpx.AsyncClient(transport=transport)
        detector = WebDetector(
            url="https://example.com",
            headers={"Authorization": "Bearer token"},
            client=client,
        )
        result = await detector.detect()
        assert result.error is None
        await client.aclose()
