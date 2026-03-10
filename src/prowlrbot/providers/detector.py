# -*- coding: utf-8 -*-
"""Auto-detect available AI providers by scanning environment variables."""

from __future__ import annotations

import logging
import os
from typing import List, Optional

from .models import ProviderDefinition

logger = logging.getLogger(__name__)


class ProviderDetector:
    """Scans environment variables to discover configured providers."""

    def __init__(
        self,
        providers: Optional[List[ProviderDefinition]] = None,
    ) -> None:
        if providers is not None:
            self._providers = providers
        else:
            from .registry import list_providers

            self._providers = list_providers()

    def scan_env_vars(self) -> List[ProviderDefinition]:
        """Return providers whose API key env var is set.

        Skips local providers that use URL-based detection (e.g. Ollama)
        and providers without an ``env_var`` defined.
        """
        detected: List[ProviderDefinition] = []
        for provider in self._providers:
            if provider.is_local and provider.url_based_detection:
                continue
            if not provider.env_var:
                continue
            key = os.environ.get(provider.env_var, "")
            if not key:
                continue
            if (
                provider.api_key_prefix
                and not key.startswith(provider.api_key_prefix)
            ):
                logger.warning(
                    "Key for %s doesn't start with expected prefix %s",
                    provider.id,
                    provider.api_key_prefix,
                )
            logger.info(
                "Detected provider: %s (via %s)",
                provider.name,
                provider.env_var,
            )
            detected.append(provider)
        return detected
