# -*- coding: utf-8 -*-
"""Swarm API router — exposes Docker/Redis swarm status to the console.

Gracefully degrades when Docker or Redis aren't available, returning
dependency status so the frontend can show a setup guide.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import time
from typing import Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/swarm", tags=["swarm"])

# Cache status checks for 10 seconds
_status_cache: dict[str, Any] = {}
_status_cache_ts: float = 0.0
_CACHE_TTL = 10.0


def _check_docker() -> bool:
    """Check if Docker daemon is running."""
    if not shutil.which("docker"):
        return False
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def _check_redis() -> bool:
    """Check if Redis is reachable."""
    try:
        import os
        import redis

        r = redis.Redis(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", "6379")),
            socket_timeout=2,
        )
        return r.ping()
    except Exception:
        return False


def _get_docker_workers() -> list[dict[str, Any]]:
    """Get prowlrbot swarm worker containers."""
    try:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                "label=prowlrbot.swarm=worker",
                "--format",
                '{"id":"{{.ID}}","name":"{{.Names}}","status":"{{.Status}}","image":"{{.Image}}","ports":"{{.Ports}}"}',
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return []

        workers = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                import json

                w = json.loads(line)
                workers.append(
                    {
                        "id": w.get("id", ""),
                        "name": w.get("name", "unknown"),
                        "host": "localhost",
                        "status": (
                            "working" if "Up" in w.get("status", "") else "offline"
                        ),
                        "current_task": None,
                        "capabilities": ["code", "review"],
                        "last_heartbeat": "",
                        "image": w.get("image", ""),
                    },
                )
            except Exception:
                continue
        return workers
    except Exception:
        return []


@router.get("/status")
async def swarm_status():
    """Check swarm infrastructure availability."""
    global _status_cache, _status_cache_ts

    now = time.time()
    if now - _status_cache_ts < _CACHE_TTL and _status_cache:
        return _status_cache

    docker_ok = _check_docker()
    redis_ok = _check_redis()
    available = docker_ok and redis_ok

    workers = _get_docker_workers() if available else None

    _status_cache = {
        "available": available,
        "docker": docker_ok,
        "redis": redis_ok,
        "workers": workers,
    }
    _status_cache_ts = now
    return _status_cache


@router.get("/workers")
async def swarm_workers():
    """List active swarm workers. Returns 503 if dependencies unavailable."""
    docker_ok = _check_docker()
    redis_ok = _check_redis()

    if not docker_ok or not redis_ok:
        missing = []
        if not docker_ok:
            missing.append("Docker")
        if not redis_ok:
            missing.append("Redis")
        return {
            "available": False,
            "missing": missing,
            "workers": [],
            "setup_guide": {
                "docker": (
                    "Install Docker Desktop or run: brew install docker"
                    if not docker_ok
                    else None
                ),
                "redis": (
                    "Run: brew install redis && brew services start redis"
                    if not redis_ok
                    else None
                ),
            },
        }

    workers = _get_docker_workers()
    return {"available": True, "workers": workers}
