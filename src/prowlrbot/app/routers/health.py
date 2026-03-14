# -*- coding: utf-8 -*-
"""Health dashboard endpoint — self-monitoring for ProwlrBot."""

from __future__ import annotations

import time
from typing import Any, Dict

from fastapi import APIRouter, Request

from ...__version__ import __version__

router = APIRouter(prefix="/health", tags=["health"])

_start_time = time.time()


@router.get("")
async def health_check(request: Request) -> Dict[str, Any]:
    """Return system health status."""
    uptime_s = time.time() - _start_time
    days, remainder = divmod(int(uptime_s), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    uptime_str = f"{days}d {hours}h {minutes}m"

    # Channel status
    channels: Dict[str, str] = {}
    channel_manager = getattr(request.app.state, "channel_manager", None)
    if channel_manager:
        for name, ch in getattr(channel_manager, "_channels", {}).items():
            channels[name] = (
                "connected" if getattr(ch, "_running", False) else "stopped"
            )

    # Cron status
    cron_info: Dict[str, Any] = {"active_jobs": 0}
    cron_manager = getattr(request.app.state, "cron_manager", None)
    if cron_manager and hasattr(cron_manager, "list_jobs"):
        try:
            jobs = await cron_manager.list_jobs()
            cron_info["active_jobs"] = len(jobs) if jobs else 0
        except Exception:
            pass

    # MCP status
    mcp_info: Dict[str, Any] = {"servers": 0}
    mcp_manager = getattr(request.app.state, "mcp_manager", None)
    if mcp_manager:
        try:
            clients = getattr(mcp_manager, "_clients", {})
            mcp_info["servers"] = len(clients)
        except Exception:
            pass

    return {
        "status": "healthy",
        "version": __version__,
        "uptime": uptime_str,
        "uptime_seconds": int(uptime_s),
        "channels": channels,
        "cron": cron_info,
        "mcp": mcp_info,
    }
