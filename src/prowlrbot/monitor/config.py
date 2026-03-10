# -*- coding: utf-8 -*-
"""Pydantic models for monitor configuration."""
from __future__ import annotations

import re
from enum import Enum
from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator

_INTERVAL_RE = re.compile(r"^(\d+)\s*(s|m|h|d)$", re.IGNORECASE)

_UNIT_SECONDS = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
}


def parse_interval(value: str) -> int:
    """Parse an interval string like '5m', '1h', '30s' into seconds."""
    m = _INTERVAL_RE.match(value.strip())
    if not m:
        raise ValueError(
            f"Invalid interval '{value}'. Use format like '30s', '5m', '1h', '2d'."
        )
    amount = int(m.group(1))
    unit = m.group(2).lower()
    return amount * _UNIT_SECONDS[unit]


class MonitorConfig(BaseModel):
    """Base monitor configuration."""

    name: str
    interval: str = "5m"
    enabled: bool = True

    @field_validator("interval")
    @classmethod
    def _validate_interval(cls, v: str) -> str:
        parse_interval(v)  # validates; raises on bad input
        return v

    @property
    def interval_seconds(self) -> int:
        return parse_interval(self.interval)


class WebMonitorConfig(MonitorConfig):
    """Configuration for web page monitoring."""

    type: Literal["web"] = "web"
    url: str
    css_selector: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)


class APIMonitorConfig(MonitorConfig):
    """Configuration for REST API monitoring."""

    type: Literal["api"] = "api"
    url: str
    method: str = "GET"
    expected_status: int = 200
    json_path: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)
    body: Optional[str] = None


AnyMonitorConfig = Union[WebMonitorConfig, APIMonitorConfig]


def parse_monitor_configs(data: List[dict]) -> List[AnyMonitorConfig]:
    """Parse a list of raw dicts into typed monitor configs."""
    configs: List[AnyMonitorConfig] = []
    for item in data:
        t = item.get("type", "web")
        if t == "api":
            configs.append(APIMonitorConfig(**item))
        else:
            configs.append(WebMonitorConfig(**item))
    return configs
