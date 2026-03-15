# -*- coding: utf-8 -*-
"""Bridge API configuration module."""
import os


class Config:
    """Bridge configuration loaded from environment."""

    # Server settings
    HOST = os.getenv("BRIDGE_HOST", "0.0.0.0")
    PORT = int(os.getenv("BRIDGE_PORT", "8765"))

    # Security
    HMAC_SECRET = os.getenv("HMAC_SECRET", "")
    ALLOWED_IPS = os.getenv("ALLOWED_IPS", "")  # Comma-separated Tailscale IPs

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.HMAC_SECRET or len(cls.HMAC_SECRET) < 32:
            raise ValueError("HMAC_SECRET must be at least 32 characters")

    @classmethod
    def get_allowed_ips(cls) -> set:
        """Get set of allowed IPs."""
        if not cls.ALLOWED_IPS:
            return set()
        return set(ip.strip() for ip in cls.ALLOWED_IPS.split(",") if ip.strip())
