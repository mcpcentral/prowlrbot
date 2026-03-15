# -*- coding: utf-8 -*-
"""Monitoring API endpoints — expose monitor engine to console UI."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...monitor.config import (
    AnyMonitorConfig,
    WebMonitorConfig,
    APIMonitorConfig,
    parse_interval,
)
from ...monitor.engine import MonitorEngine
from ...monitor.storage import MonitorStorage

router = APIRouter(prefix="/monitors", tags=["monitoring"])

# Lazily initialized engine singleton.
_engine: MonitorEngine | None = None


def _get_engine() -> MonitorEngine:
    """Get or create the global MonitorEngine instance."""
    global _engine
    if _engine is None:
        _engine = MonitorEngine()
    return _engine


# ------------------------------------------------------------------
# Request / Response models
# ------------------------------------------------------------------


class MonitorCreateRequest(BaseModel):
    """Payload for creating a new monitor."""

    url: str
    type: str = "web"
    interval_minutes: int = Field(default=60, ge=1, le=1440)
    css_selector: Optional[str] = None
    method: str = "GET"
    expected_status: int = 200
    json_path: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)


class MonitorResponse(BaseModel):
    """Serialized monitor for API responses."""

    id: str
    type: str
    url: str
    interval_minutes: int
    enabled: bool = True
    status: str = "unknown"
    last_checked: Optional[str] = None


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.get("", response_model=List[MonitorResponse])
async def list_monitors() -> List[MonitorResponse]:
    """List all configured monitors."""
    engine = _get_engine()
    results: List[MonitorResponse] = []
    for config in engine.list():
        snapshot = engine.storage.load(config.name)
        results.append(
            MonitorResponse(
                id=config.name,
                type=config.type if hasattr(config, "type") else "web",
                url=config.url,
                interval_minutes=config.interval_seconds // 60 or 1,
                enabled=config.enabled,
                status="ok" if snapshot else "unknown",
                last_checked=snapshot.checked_at if snapshot else None,
            ),
        )
    return results


@router.post("", response_model=MonitorResponse)
async def create_monitor(body: MonitorCreateRequest) -> MonitorResponse:
    """Create a new monitor."""
    engine = _get_engine()
    monitor_id = f"mon_{uuid.uuid4().hex[:8]}"
    interval_str = f"{body.interval_minutes}m"

    if body.type == "api":
        config: AnyMonitorConfig = APIMonitorConfig(
            name=monitor_id,
            url=body.url,
            interval=interval_str,
            method=body.method,
            expected_status=body.expected_status,
            json_path=body.json_path,
            headers=body.headers,
        )
    else:
        config = WebMonitorConfig(
            name=monitor_id,
            url=body.url,
            interval=interval_str,
            css_selector=body.css_selector,
            headers=body.headers,
        )

    engine.add(config)

    return MonitorResponse(
        id=monitor_id,
        type=body.type,
        url=body.url,
        interval_minutes=body.interval_minutes,
        enabled=True,
        status="unknown",
        last_checked=None,
    )


@router.get("/{monitor_id}", response_model=MonitorResponse)
async def get_monitor(monitor_id: str) -> MonitorResponse:
    """Get a single monitor by ID."""
    engine = _get_engine()
    configs = {c.name: c for c in engine.list()}
    config = configs.get(monitor_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Monitor not found")

    snapshot = engine.storage.load(config.name)
    return MonitorResponse(
        id=config.name,
        type=config.type if hasattr(config, "type") else "web",
        url=config.url,
        interval_minutes=config.interval_seconds // 60 or 1,
        enabled=config.enabled,
        status="ok" if snapshot else "unknown",
        last_checked=snapshot.checked_at if snapshot else None,
    )


@router.delete("/{monitor_id}")
async def delete_monitor(monitor_id: str) -> Dict[str, Any]:
    """Delete a monitor."""
    engine = _get_engine()
    removed = engine.remove(monitor_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return {"id": monitor_id, "status": "deleted"}


@router.get("/{monitor_id}/history")
async def get_monitor_history(monitor_id: str) -> List[Dict[str, Any]]:
    """Get check history for a monitor.

    Currently returns the latest snapshot. Will be extended to store
    full history in a future iteration.
    """
    engine = _get_engine()
    snapshot = engine.storage.load(monitor_id)
    if snapshot is None:
        return []
    return [
        {
            "monitor_name": snapshot.monitor_name,
            "checked_at": snapshot.checked_at,
            "content_length": len(snapshot.content),
        },
    ]
