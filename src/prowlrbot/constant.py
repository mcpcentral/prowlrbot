# -*- coding: utf-8 -*-
import os
from pathlib import Path

WORKING_DIR = (
    Path(os.environ.get("PROWLRBOT_WORKING_DIR", "~/.prowlrbot")).expanduser().resolve()
)
SECRET_DIR = (
    Path(
        os.environ.get(
            "PROWLRBOT_SECRET_DIR",
            f"{WORKING_DIR}.secret",
        ),
    )
    .expanduser()
    .resolve()
)

JOBS_FILE = os.environ.get("PROWLRBOT_JOBS_FILE", "jobs.json")

CHATS_FILE = os.environ.get("PROWLRBOT_CHATS_FILE", "chats.json")

CONFIG_FILE = os.environ.get("PROWLRBOT_CONFIG_FILE", "config.json")

HEARTBEAT_FILE = os.environ.get("PROWLRBOT_HEARTBEAT_FILE", "HEARTBEAT.md")
HEARTBEAT_DEFAULT_EVERY = "6h"
HEARTBEAT_DEFAULT_TARGET = "main"
HEARTBEAT_TARGET_LAST = "last"

# Env key for app log level (used by CLI and app load for reload child).
LOG_LEVEL_ENV = "PROWLRBOT_LOG_LEVEL"

# Env to indicate running inside a container (e.g. Docker). Set to 1/true/yes.
RUNNING_IN_CONTAINER = os.environ.get(
    "PROWLRBOT_RUNNING_IN_CONTAINER",
    "false",
)

# Playwright: use system Chromium when set (e.g. in Docker).
PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH_ENV = "PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"

# When True, expose /docs, /redoc, /openapi.json
# (dev only; keep False in prod).
DOCS_ENABLED = os.environ.get("PROWLRBOT_OPENAPI_DOCS", "false").lower() in (
    "true",
    "1",
    "yes",
)

# Skills directories
# Active skills directory (activated skills that agents use)
ACTIVE_SKILLS_DIR = WORKING_DIR / "active_skills"
# Customized skills directory (user-created skills)
CUSTOMIZED_SKILLS_DIR = WORKING_DIR / "customized_skills"

# Memory directory
MEMORY_DIR = WORKING_DIR / "memory"

# Custom channel modules (installed via `prowlr channels install`); manager
# loads BaseChannel subclasses from here.
CUSTOM_CHANNELS_DIR = WORKING_DIR / "custom_channels"

# Local models directory
MODELS_DIR = WORKING_DIR / "models"

# Memory compaction configuration
MEMORY_COMPACT_KEEP_RECENT = int(
    os.environ.get("PROWLRBOT_MEMORY_COMPACT_KEEP_RECENT", "3"),
)

MEMORY_COMPACT_RATIO = float(
    os.environ.get("PROWLRBOT_MEMORY_COMPACT_RATIO", "0.7"),
)

DASHSCOPE_BASE_URL = os.environ.get(
    "DASHSCOPE_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# CORS configuration — comma-separated list of allowed origins.
# Example: PROWLRBOT_CORS_ORIGINS="http://localhost:5173,https://prowlrbot.com"
# When unset: if PROWLR_OFFICIAL_APP=1 (e.g. app.prowlrbot.com), allows the marketing
# site origins so the ROAR demo (prowlrbot.com/demo/roar-demo.html) can call /roar/health and /roar/card.
_OFFICIAL_APP = os.environ.get("PROWLR_OFFICIAL_APP", "").strip().lower() in ("1", "true", "yes")
_DEMO_ORIGINS = "https://prowlrbot.com,https://www.prowlrbot.com"
CORS_ORIGINS = (
    os.environ.get("PROWLRBOT_CORS_ORIGINS", "").strip()
    or (_DEMO_ORIGINS if _OFFICIAL_APP else "")
)

# API authentication — set to a SHA-256 hash of your token.
# Generate with: python -c "from prowlrbot.app.auth import generate_api_token, hash_token; t=generate_api_token(); print(f'Token: {t}\nHash:  {hash_token(t)}')"
PROWLRBOT_API_TOKEN_HASH = os.environ.get("PROWLRBOT_API_TOKEN_HASH", "")
