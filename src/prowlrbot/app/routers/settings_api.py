# -*- coding: utf-8 -*-
"""Unified settings API — aggregated settings, theme, system info."""

from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...auth.privacy import PrivacyManager
from ...constant import WORKING_DIR
from ...themes import THEMES, THEME_IDS

router = APIRouter(prefix="/settings", tags=["settings"])

_SETTINGS_FILE = WORKING_DIR / "settings.json"
_privacy_manager = PrivacyManager(config_path=WORKING_DIR / "privacy.json")

# Track process start time for uptime calculation.
_PROCESS_START = time.time()


# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------


class ThemeRequest(BaseModel):
    """Request body for theme preference update."""

    theme: str = Field(
        ...,
        pattern=r"^(light|dark|system)$",
        description="Theme preference: light, dark, or system.",
    )


class ColorThemeRequest(BaseModel):
    """Request body for color theme selection."""

    color_theme: str = Field(
        ...,
        description="Color theme ID from the available themes list.",
    )


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _load_settings() -> Dict[str, Any]:
    """Load the general settings file, returning defaults on error."""
    if _SETTINGS_FILE.is_file():
        try:
            return json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_settings(data: Dict[str, Any]) -> None:
    """Persist the general settings file."""
    _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ------------------------------------------------------------------
# GET /settings/all — aggregated settings
# ------------------------------------------------------------------


@router.get("/all")
async def get_all_settings() -> Dict[str, Any]:
    """Return combined settings from multiple subsystems.

    Aggregates privacy settings, autonomy defaults, notification
    preferences, and theme into a single response.
    """
    general = _load_settings()

    # Privacy
    privacy = _privacy_manager.get_settings().model_dump()

    # Autonomy defaults — try to load the controller, fall back to
    # sensible defaults if the autonomy subsystem is unavailable.
    autonomy_defaults: Dict[str, Any] = general.get(
        "autonomy_defaults",
        {"default_level": "guide", "require_approval_above_cost": 1.0},
    )

    # Notification preferences
    notification_prefs: Dict[str, Any] = general.get(
        "notification_preferences",
        {"enabled": True, "channels": ["console"], "quiet_hours": None},
    )

    return {
        "privacy": privacy,
        "autonomy_defaults": autonomy_defaults,
        "notification_preferences": notification_prefs,
        # Default to light mode for a brighter, more neutral first impression.
        "theme": general.get("theme", "light"),
        "color_theme": general.get("color_theme", "tech-innovation"),
    }


# ------------------------------------------------------------------
# PUT /settings/theme — theme preference
# ------------------------------------------------------------------


@router.put("/theme")
async def set_theme(req: ThemeRequest) -> Dict[str, str]:
    """Set the UI theme preference (light, dark, or system)."""
    settings = _load_settings()
    settings["theme"] = req.theme
    _save_settings(settings)
    return {"theme": req.theme}


# ------------------------------------------------------------------
# GET /settings/themes — available color themes
# ------------------------------------------------------------------


@router.get("/themes")
async def get_themes() -> Dict[str, Any]:
    """Return all available color themes and the currently active one."""
    settings = _load_settings()
    return {
        "themes": THEMES,
        "active": settings.get("color_theme", "tech-innovation"),
    }


# ------------------------------------------------------------------
# PUT /settings/color-theme — select a color theme
# ------------------------------------------------------------------


@router.put("/color-theme")
async def set_color_theme(req: ColorThemeRequest) -> Dict[str, str]:
    """Set the active color theme."""
    if req.color_theme not in THEME_IDS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown theme '{req.color_theme}'. "
            f"Valid: {sorted(THEME_IDS)}",
        )
    settings = _load_settings()
    settings["color_theme"] = req.color_theme
    _save_settings(settings)
    return {"color_theme": req.color_theme}


# ------------------------------------------------------------------
# GET /settings/system-info — system information
# ------------------------------------------------------------------


@router.get("/system-info")
async def get_system_info() -> Dict[str, Any]:
    """Return system information useful for diagnostics.

    Includes Python version, platform details, working directory,
    database sizes, and process uptime.
    """
    # Collect database sizes
    db_sizes: Dict[str, str] = {}
    for db_file in WORKING_DIR.glob("*.db"):
        size_bytes = db_file.stat().st_size
        if size_bytes < 1024:
            db_sizes[db_file.name] = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            db_sizes[db_file.name] = f"{size_bytes / 1024:.1f} KB"
        else:
            db_sizes[db_file.name] = f"{size_bytes / (1024 * 1024):.1f} MB"

    uptime_seconds = time.time() - _PROCESS_START
    hours, remainder = divmod(int(uptime_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)

    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "working_dir": str(WORKING_DIR),
        "db_sizes": db_sizes,
        "uptime_seconds": round(uptime_seconds, 1),
        "uptime_human": f"{hours}h {minutes}m {seconds}s",
        "pid": __import__("os").getpid(),
    }
