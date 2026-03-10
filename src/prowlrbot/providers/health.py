# -*- coding: utf-8 -*-
"""Async health check system for AI providers."""

from __future__ import annotations

import logging
from typing import Dict

import httpx

from .models import ProviderDefinition

logger = logging.getLogger(__name__)


class HealthChecker:
    """Probes provider endpoints to determine availability."""

    def __init__(self, timeout: float = 5.0) -> None:
        self.timeout = timeout
        self._status: Dict[str, bool] = {}

    async def check(
        self,
        provider: ProviderDefinition,
        api_key: str = "",
    ) -> bool:
        """Check if a provider's API is reachable.

        Returns True if the server responds with a non-5xx status,
        or if no health_check_endpoint is configured (assumed healthy).
        """
        if not provider.health_check_endpoint:
            self._status[provider.id] = True
            return True

        try:
            base = provider.default_base_url.rstrip("/")
            url = f"{base}{provider.health_check_endpoint}"
            headers: Dict[str, str] = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=headers)
                healthy = resp.status_code < 500
                self._status[provider.id] = healthy
                if healthy:
                    logger.info("Health check passed: %s", provider.name)
                else:
                    logger.warning(
                        "Health check failed: %s (status %d)",
                        provider.name,
                        resp.status_code,
                    )
                return healthy
        except Exception as e:
            logger.warning(
                "Health check error for %s: %s",
                provider.name,
                str(e),
            )
            self._status[provider.id] = False
            return False

    def get_status(self, provider_id: str) -> bool:
        """Return last known health status for a provider."""
        return self._status.get(provider_id, False)
