# -*- coding: utf-8 -*-
"""Client configuration module."""
import os


class Config:
    """Client configuration loaded from environment."""

    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        pass  # Client only needs Redis connection
