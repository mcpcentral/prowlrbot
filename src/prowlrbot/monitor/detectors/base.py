# -*- coding: utf-8 -*-
"""Abstract base detector."""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class DetectionResult:
    """Result from a single detection check."""

    content: Optional[str]
    changed: bool
    diff_summary: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[str] = None


class BaseDetector(abc.ABC):
    """ABC for all detectors."""

    @abc.abstractmethod
    async def detect(self, last_content: Optional[str] = None) -> DetectionResult:
        """Run a detection check. *last_content* is the previous snapshot."""
        ...
