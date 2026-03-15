# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os
import warnings
from pathlib import Path

# Suppress known deprecation noise from dependencies (uvicorn/websockets, nacos/pydantic)
# before uvicorn is imported so the filters apply when those modules load.
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings(
    "ignore",
    message=".*Support for class-based `config`.*",
)
warnings.filterwarnings("ignore", message=".*deprecated.*Pydantic.*")

import click
import uvicorn

from ..constant import LOG_LEVEL_ENV, RUNNING_IN_CONTAINER
from ..config.utils import write_last_api
from ..utils.logging import setup_logger, SuppressPathAccessLogFilter


def _load_dotenv_if_present() -> None:
    """Load .env from current working directory so PROWLRBOT_ADMIN_* etc. are set."""
    try:
        from dotenv import load_dotenv

        env_path = Path.cwd() / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass


@click.command("app")
@click.option(
    "--host",
    default=None,
    show_default=True,
    help="Bind host (default: 0.0.0.0 in container, 127.0.0.1 otherwise)",
)
@click.option(
    "--port",
    default=8088,
    type=int,
    show_default=True,
    help="Bind port",
)
@click.option("--reload", is_flag=True, help="Enable auto-reload (dev only)")
@click.option(
    "--workers",
    default=1,
    type=int,
    show_default=True,
    help="Worker processes",
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(
        ["critical", "error", "warning", "info", "debug", "trace"],
        case_sensitive=False,
    ),
    show_default=True,
    help="Log level",
)
@click.option(
    "--hide-access-paths",
    multiple=True,
    default=("/console/push-messages",),
    show_default=True,
    help="Path substrings to hide from uvicorn access log (repeatable).",
)
def app_cmd(
    host: str | None,
    port: int,
    reload: bool,
    workers: int,
    log_level: str,
    hide_access_paths: tuple[str, ...],
) -> None:
    """Run ProwlrBot FastAPI app."""
    _load_dotenv_if_present()
    if host is None:
        host = (
            "0.0.0.0"
            if (RUNNING_IN_CONTAINER or "").lower() in ("1", "true", "yes")
            else "127.0.0.1"
        )
    # Persist last used host/port for other terminals
    write_last_api(host, port)
    os.environ[LOG_LEVEL_ENV] = log_level
    setup_logger(log_level)
    if log_level in ("debug", "trace"):
        from .main import log_init_timings

        log_init_timings()

    paths = [p for p in hide_access_paths if p]
    if paths:
        logging.getLogger("uvicorn.access").addFilter(
            SuppressPathAccessLogFilter(paths),
        )

    uvicorn.run(
        "prowlrbot.app._app:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level=log_level,
    )
