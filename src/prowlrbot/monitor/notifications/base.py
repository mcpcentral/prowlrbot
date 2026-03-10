# -*- coding: utf-8 -*-
"""Abstract base notifier."""
from __future__ import annotations

import abc
from typing import Optional


class BaseNotifier(abc.ABC):
    """ABC for notification backends."""

    @abc.abstractmethod
    async def notify(
        self,
        monitor_name: str,
        summary: str,
        content: Optional[str] = None,
    ) -> bool:
        """Send a notification. Return True on success."""
        ...
