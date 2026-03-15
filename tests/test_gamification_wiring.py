# -*- coding: utf-8 -*-
"""Smoke tests — verify XP wiring doesn't break normal agent/cron execution."""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_award_xp_background_never_raises():
    """_award_xp_background must never raise even if HTTP fails."""
    from prowlrbot.app.runner.runner import _award_xp_background

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=ConnectionError("server down"),
        )
        # Should not raise
        await _award_xp_background("test-agent", "task_complete", "test", 10)


@pytest.mark.asyncio
async def test_award_xp_background_never_raises_on_timeout():
    """_award_xp_background must handle timeout gracefully."""
    from prowlrbot.app.runner.runner import _award_xp_background

    import httpx

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=httpx.TimeoutException("timeout"),
        )
        await _award_xp_background("test-agent", "cron_complete", "test", 5)


@pytest.mark.asyncio
async def test_award_xp_background_cron_never_raises():
    """Cron executor's _award_xp_background must never raise even if HTTP fails."""
    from prowlrbot.app.crons.executor import _award_xp_background

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=ConnectionError("server down"),
        )
        await _award_xp_background("cron-session", "cron_complete", "test", 5)


@pytest.mark.asyncio
async def test_award_xp_background_succeeds_silently():
    """_award_xp_background completes without error on a 200 response."""
    from prowlrbot.app.runner.runner import _award_xp_background

    mock_response = AsyncMock()
    mock_response.status_code = 200

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response,
        )
        await _award_xp_background(
            "test-agent",
            "task_complete",
            "Completed",
            10,
        )
