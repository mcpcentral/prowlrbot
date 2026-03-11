# -*- coding: utf-8 -*-
"""Route monitor alerts to configured channels based on severity."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AlertRouter:
    """Route alerts to channels based on severity and quiet hours.

    Severity levels (highest to lowest): critical, warning, info.
    During quiet hours, only critical alerts are routed.

    Args:
        rules: Mapping of severity level to list of channel names.
        quiet_hours: Optional tuple of (start_hour, end_hour) in 24h format.
            When set, non-critical alerts are suppressed during this window.
            Wraps midnight if start > end (e.g., (22, 7) = 10pm to 7am).
    """

    SEVERITY_LEVELS = ("critical", "warning", "info")

    def __init__(
        self,
        rules: Optional[Dict[str, List[str]]] = None,
        quiet_hours: Optional[Tuple[int, int]] = None,
    ) -> None:
        self._rules: Dict[str, List[str]] = rules or {
            "critical": ["console"],
            "warning": ["console"],
            "info": ["console"],
        }
        self._quiet_hours = quiet_hours

    @property
    def rules(self) -> Dict[str, List[str]]:
        """Return a copy of the current routing rules."""
        return {k: list(v) for k, v in self._rules.items()}

    @property
    def quiet_hours(self) -> Optional[Tuple[int, int]]:
        """Return the configured quiet hours window, or None."""
        return self._quiet_hours

    def _is_quiet_hour(self, hour: int) -> bool:
        """Check whether the given hour falls within the quiet window."""
        if self._quiet_hours is None:
            return False
        start, end = self._quiet_hours
        if start > end:
            # Wraps midnight: e.g. (22, 7) means 22:00 .. 06:59
            return hour >= start or hour < end
        else:
            return start <= hour < end

    def route(
        self,
        severity: str,
        message: str,
        *,
        force_hour: Optional[int] = None,
    ) -> List[str]:
        """Return list of channel names to send this alert to.

        Args:
            severity: Alert severity level (critical, warning, info).
            message: The alert message text (used for logging only).
            force_hour: Override the current hour for testing quiet-hour logic.

        Returns:
            List of channel name strings that should receive this alert.
        """
        channels = self._rules.get(severity, [])
        if not channels:
            return []

        # During quiet hours, only critical alerts get through
        if self._quiet_hours is not None and severity != "critical":
            hour = force_hour if force_hour is not None else datetime.now().hour
            if self._is_quiet_hour(hour):
                logger.debug(
                    "Suppressed %s alert during quiet hours: %s",
                    severity,
                    message[:80],
                )
                return []

        return list(channels)

    def update_rules(self, rules: Dict[str, List[str]]) -> None:
        """Replace routing rules."""
        self._rules = {k: list(v) for k, v in rules.items()}

    def set_quiet_hours(self, quiet_hours: Optional[Tuple[int, int]]) -> None:
        """Update quiet hours window."""
        self._quiet_hours = quiet_hours
