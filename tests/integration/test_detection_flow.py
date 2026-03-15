# -*- coding: utf-8 -*-
"""Integration test: Detect → Health Check → Route pipeline."""

import os

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from prowlrbot.providers.detector import ProviderDetector
from prowlrbot.providers.health import HealthChecker
from prowlrbot.providers.router import SmartRouter
from prowlrbot.providers.registry import list_providers


@pytest.mark.asyncio
async def test_full_detection_pipeline():
    """End-to-end: detect providers by env → health check → route to best."""
    with patch.dict(
        os.environ,
        {"ANTHROPIC_API_KEY": "sk-ant-test123", "GROQ_API_KEY": "gsk_testkey"},
        clear=False,
    ):
        # Step 1: Detect
        detector = ProviderDetector()
        detected = detector.scan_env_vars()
        ids = [p.id for p in detected]
        assert "anthropic" in ids
        assert "groq" in ids

        # Step 2: Health check (mocked)
        checker = HealthChecker(timeout=2.0)
        health_status = {}
        with patch(
            "httpx.AsyncClient.get",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            for p in detected:
                result = await checker.check(
                    p,
                    api_key=os.environ.get(p.env_var, ""),
                )
                health_status[p.id] = result

        # All should be healthy (mocked 200)
        assert health_status["anthropic"] is True
        assert health_status["groq"] is True

        # Step 3: Route
        router = SmartRouter(detected, health_status=health_status)
        selected = router.select()
        assert selected is not None
        # Groq (cost_tier="low") should score higher than Anthropic ("premium")
        assert selected.id == "groq"

        # Fallback chain should have both
        chain = router.get_fallback_chain()
        assert len(chain) == 2
        assert chain[0].id == "groq"
        assert chain[1].id == "anthropic"


@pytest.mark.asyncio
async def test_pipeline_with_unhealthy_provider():
    """When one provider fails health check, router picks the healthy one."""
    with patch.dict(
        os.environ,
        {"ANTHROPIC_API_KEY": "sk-ant-test", "GROQ_API_KEY": "gsk_test"},
        clear=False,
    ):
        detector = ProviderDetector()
        detected = detector.scan_env_vars()

        checker = HealthChecker(timeout=2.0)
        health_status = {}

        async def mock_get_side_effect(url, **kwargs):
            if "groq" in url:
                raise Exception("connection refused")
            return MagicMock(status_code=200)

        with patch(
            "httpx.AsyncClient.get",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.side_effect = mock_get_side_effect
            for p in detected:
                result = await checker.check(
                    p,
                    api_key=os.environ.get(p.env_var, ""),
                )
                health_status[p.id] = result

        # Groq should be unhealthy
        assert health_status.get("groq") is False
        assert health_status.get("anthropic") is True

        router = SmartRouter(detected, health_status=health_status)
        selected = router.select()
        assert selected is not None
        assert selected.id == "anthropic"


def test_registry_has_detection_metadata():
    """Verify built-in providers have detection fields populated."""
    providers = list_providers()
    providers_with_env = [p for p in providers if p.env_var]
    # At minimum: anthropic, openai, groq, zai, modelscope, dashscope, aliyun, azure
    assert len(providers_with_env) >= 7

    # Verify specific providers
    by_id = {p.id: p for p in providers}
    assert by_id["anthropic"].env_var == "ANTHROPIC_API_KEY"
    assert by_id["anthropic"].cost_tier == "premium"
    assert by_id["groq"].env_var == "GROQ_API_KEY"
    assert by_id["groq"].cost_tier == "low"
    assert by_id["ollama"].url_based_detection is True
    assert by_id["ollama"].cost_tier == "free"
