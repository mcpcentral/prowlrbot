# -*- coding: utf-8 -*-
"""Worker configuration module."""
import os


class Config:
    """Worker configuration loaded from environment."""

    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))

    BRIDGE_HOST = os.getenv("BRIDGE_HOST", "localhost")
    BRIDGE_PORT = int(os.getenv("BRIDGE_PORT", "8765"))
    BRIDGE_BASE_URL = f"http://{BRIDGE_HOST}:{BRIDGE_PORT}"

    HMAC_SECRET = os.getenv("HMAC_SECRET", "")
    POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "5"))

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.HMAC_SECRET or len(cls.HMAC_SECRET) < 32:
            raise ValueError("HMAC_SECRET must be at least 32 characters")
        if cls.BRIDGE_HOST in ("localhost", "100.x.x.x"):
            raise ValueError("BRIDGE_HOST must be set to actual Tailscale IP")
