# -*- coding: utf-8 -*-
"""Tests for HealthChecker — async provider health probes."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from prowlrbot.providers.health import HealthChecker
from prowlrbot.providers.models import ProviderDefinition


@pytest.mark.asyncio
async def test_healthy_provider_returns_true():
    provider = ProviderDefinition(
        id="test",
        name="Test",
        default_base_url="https://api.test.com/v1",
        env_var="TEST_KEY",
        health_check_endpoint="/v1/models",
    )
    checker = HealthChecker(timeout=5.0)
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = MagicMock(status_code=200)
        result = await checker.check(provider, api_key="test-key")
    assert result is True
    assert checker.get_status("test") is True


@pytest.mark.asyncio
async def test_unreachable_provider_returns_false():
    provider = ProviderDefinition(
        id="dead",
        name="Dead",
        default_base_url="https://api.unreachable.com/v1",
        env_var="TEST_KEY",
        health_check_endpoint="/v1/models",
    )
    checker = HealthChecker(timeout=1.0)
    with patch(
        "httpx.AsyncClient.get",
        new_callable=AsyncMock,
        side_effect=Exception("timeout"),
    ):
        result = await checker.check(provider, api_key="test-key")
    assert result is False
    assert checker.get_status("dead") is False


@pytest.mark.asyncio
async def test_server_error_returns_false():
    provider = ProviderDefinition(
        id="error",
        name="Error Provider",
        default_base_url="https://api.error.com",
        health_check_endpoint="/v1/models",
    )
    checker = HealthChecker(timeout=5.0)
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = MagicMock(status_code=500)
        result = await checker.check(provider, api_key="")
    assert result is False


@pytest.mark.asyncio
async def test_auth_error_still_healthy():
    """401/403 means the server is up, just auth failed — still 'available'."""
    provider = ProviderDefinition(
        id="auth-fail",
        name="Auth Fail",
        default_base_url="https://api.test.com",
        health_check_endpoint="/v1/models",
    )
    checker = HealthChecker(timeout=5.0)
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = MagicMock(status_code=401)
        result = await checker.check(provider, api_key="bad-key")
    assert result is True  # Server is reachable


@pytest.mark.asyncio
async def test_no_health_endpoint_skips_check():
    """Provider without health_check_endpoint returns True (assumed healthy)."""
    provider = ProviderDefinition(
        id="no-check",
        name="No Check",
        default_base_url="https://api.test.com",
        health_check_endpoint="",
    )
    checker = HealthChecker(timeout=5.0)
    result = await checker.check(provider, api_key="")
    assert result is True


def test_get_status_default():
    checker = HealthChecker()
    assert checker.get_status("unknown") is False
