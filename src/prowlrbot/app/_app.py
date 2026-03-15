# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name,unused-argument
import mimetypes
import os
from contextlib import asynccontextmanager
from pathlib import Path

import sentry_sdk

_sentry_dsn = os.environ.get("SENTRY_DSN", "")
if _sentry_dsn:
    sentry_sdk.init(
        dsn=_sentry_dsn,
        send_default_pii=True,
        traces_sample_rate=float(
            os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "1.0"),
        ),
        profiles_sample_rate=float(
            os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "1.0"),
        ),
    )

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from agentscope_runtime.engine.app import AgentApp

from .runner import AgentRunner
from ..config import (  # pylint: disable=no-name-in-module
    load_config,
    update_last_dispatch,
    ConfigWatcher,
)
from ..config.utils import get_jobs_path, get_chats_path, get_config_path
from ..constant import (
    DOCS_ENABLED,
    LOG_LEVEL_ENV,
    CORS_ORIGINS,
    PROWLRBOT_API_TOKEN_HASH,
)
from ..__version__ import __version__
from ..utils.logging import setup_logger
from .channels import ChannelManager  # pylint: disable=no-name-in-module
from .channels.utils import make_process_from_runner
from .mcp import MCPClientManager, MCPConfigWatcher  # MCP hot-reload support
from .runner.repo.json_repo import JsonChatRepository
from .crons.repo.json_repo import JsonJobRepository
from .crons.manager import CronManager
from .runner.manager import ChatManager
from .routers import router as api_router
from .auth import AuthConfig, AuthDependency
from ..auth.security_headers import SecurityHeadersMiddleware
from ..auth.rate_limiter import RateLimitMiddleware as AuthRateLimitMiddleware
from ..auth.csrf import CSRFMiddleware
from .websocket import create_websocket_router
from ..dashboard.events import EventBus
from ..envs import load_envs_into_environ
from ..auth.store import UserStore
from ..auth.models import Role
from ..providers.store import (
    load_providers_json,
    set_active_llm,
    update_provider_settings,
)

# Apply log level on load so reload child process gets same level as CLI.
logger = setup_logger(os.environ.get(LOG_LEVEL_ENV, "info"))

# Ensure static assets are served with browser-compatible MIME types across
# platforms (notably Windows may miss .js/.mjs mappings).
mimetypes.init()
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/javascript", ".mjs")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/wasm", ".wasm")

# Load persisted env vars into os.environ at module import time
# so they are available before the lifespan starts.
load_envs_into_environ()

runner = AgentRunner()

agent_app = AgentApp(
    app_name="Friday",
    app_description="A helpful assistant",
    runner=runner,
)


def _ensure_admin_user() -> None:
    """Create an admin user on first run if no users exist.

    Credentials come from env vars ``PROWLRBOT_ADMIN_USERNAME`` /
    ``PROWLRBOT_ADMIN_PASSWORD``. If not set, a random password is
    generated and printed to the log.
    """
    try:
        store = UserStore()
        if store.list_users():
            return  # users already exist

        import secrets as _secrets

        username = os.environ.get("PROWLRBOT_ADMIN_USERNAME", "admin")
        password = os.environ.get("PROWLRBOT_ADMIN_PASSWORD", "")
        generated = False
        if not password:
            password = _secrets.token_urlsafe(16)
            generated = True

        store.create_user(
            username=username,
            password=password,
            role=Role.admin,
        )

        logger.info("Created admin user '%s'", username)
        if generated:
            logger.info(
                "Generated admin password (save it now!): %s",
                password,
            )
            # Also print to stdout so it's visible in container logs
            print(f"\n{'='*60}")
            print(f"  Admin account created!")
            print(f"  Username: {username}")
            print(f"  Password: {password}")
            print(
                f"  (Set PROWLRBOT_ADMIN_PASSWORD env var to choose your own)",
            )
            print(f"{'='*60}\n")
    except Exception:
        logger.exception("Failed to create initial admin user")


def _auto_detect_provider() -> None:
    """Auto-detect and activate an LLM provider from env vars on first run.

    Checks for common API keys in the environment and configures the first
    one found as the active provider. This ensures chat works out of the
    box when deploying with API keys set as secrets.
    """
    try:
        data = load_providers_json()
        if data.active_llm.provider_id:
            return  # already configured

        # Priority order: Anthropic > OpenAI > Groq > Ollama
        providers_to_check = [
            ("anthropic", "ANTHROPIC_API_KEY", "claude-sonnet-4-6"),
            ("openai", "OPENAI_API_KEY", "gpt-4o"),
            ("groq", "GROQ_API_KEY", "llama-3.3-70b-versatile"),
        ]

        for provider_id, env_var, default_model in providers_to_check:
            api_key = os.environ.get(env_var, "")
            if not api_key:
                continue

            # Store the API key in providers.json
            update_provider_settings(provider_id, api_key=api_key)
            set_active_llm(provider_id, default_model)
            logger.info(
                "Auto-detected %s from %s — activated %s",
                provider_id,
                env_var,
                default_model,
            )
            return

        # Check for Ollama (local, no API key needed — just check connectivity)
        ollama_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        try:
            import httpx

            resp = httpx.get(f"{ollama_url}/api/tags", timeout=3)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                if models:
                    model_name = models[0].get("name", "llama3.1")
                    set_active_llm("ollama", model_name)
                    logger.info(
                        "Auto-detected Ollama at %s — activated %s",
                        ollama_url,
                        model_name,
                    )
                    return
        except Exception:
            pass  # Ollama not running, that's fine

        logger.warning(
            "No LLM provider API key found in environment. "
            "Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or configure via Settings > Models.",
        )
    except Exception:
        logger.exception("Failed to auto-detect LLM provider")


@asynccontextmanager
async def lifespan(app: FastAPI):  # pylint: disable=too-many-statements
    # Ensure at least one admin user exists for fresh installs
    _ensure_admin_user()

    # Auto-detect and activate LLM provider from env vars
    _auto_detect_provider()

    # Clean up stale temp files from previous runs
    try:
        from .runner.query_error_dump import cleanup_old_error_dumps

        cleanup_old_error_dumps()
    except Exception:
        pass

    await runner.start()

    # --- MCP client manager init (independent module, hot-reloadable) ---
    config = load_config()
    mcp_manager = MCPClientManager()
    if hasattr(config, "mcp"):
        try:
            await mcp_manager.init_from_config(config.mcp)
            runner.set_mcp_manager(mcp_manager)
            logger.debug("MCP client manager initialized")
        except Exception:
            logger.exception("Failed to initialize MCP manager")

    # --- channel connector init/start (from config.json) ---
    channel_manager = ChannelManager.from_config(
        process=make_process_from_runner(runner),
        config=config,
        on_last_dispatch=update_last_dispatch,
    )
    await channel_manager.start_all()

    # --- cron init/start ---
    repo = JsonJobRepository(get_jobs_path())
    cron_manager = CronManager(
        repo=repo,
        runner=runner,
        channel_manager=channel_manager,
        timezone="UTC",
    )
    await cron_manager.start()

    # --- chat manager init and connect to runner.session ---
    chat_repo = JsonChatRepository(get_chats_path())
    chat_manager = ChatManager(
        repo=chat_repo,
    )

    runner.set_chat_manager(chat_manager)

    # --- config file watcher (channels + heartbeat hot-reload on change) ---
    config_watcher = ConfigWatcher(
        channel_manager=channel_manager,
        cron_manager=cron_manager,
    )
    await config_watcher.start()

    # --- MCP config watcher (auto-reload MCP clients on change) ---
    mcp_watcher = None
    if hasattr(config, "mcp"):
        try:
            mcp_watcher = MCPConfigWatcher(
                mcp_manager=mcp_manager,
                config_loader=load_config,
                config_path=get_config_path(),
            )
            await mcp_watcher.start()
            logger.debug("MCP config watcher started")
        except Exception:
            logger.exception("Failed to start MCP watcher")

    # expose to endpoints
    app.state.event_bus = event_bus
    app.state.runner = runner
    app.state.channel_manager = channel_manager
    app.state.cron_manager = cron_manager
    app.state.chat_manager = chat_manager
    app.state.config_watcher = config_watcher
    app.state.mcp_manager = mcp_manager
    app.state.mcp_watcher = mcp_watcher

    try:
        yield
    finally:
        # stop order: watchers -> cron -> channels -> mcp -> runner
        try:
            await config_watcher.stop()
        except Exception:
            pass
        if mcp_watcher:
            try:
                await mcp_watcher.stop()
            except Exception:
                pass
        try:
            await cron_manager.stop()
        finally:
            await channel_manager.stop_all()
            if mcp_manager:
                try:
                    await mcp_manager.close_all()
                except Exception:
                    pass
            await runner.stop()


app = FastAPI(
    lifespan=lifespan,
    docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url="/redoc" if DOCS_ENABLED else None,
    openapi_url="/openapi.json" if DOCS_ENABLED else None,
)

# Apply CORS middleware if CORS_ORIGINS is set
if CORS_ORIGINS:
    origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]
    # Never allow credentials with wildcard origins — browsers block it and
    # it signals a misconfiguration.
    use_credentials = "*" not in origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=use_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-CSRF-Token",
            "X-Session-Token",
        ],
    )


# --- Security middleware (order: SecurityHeaders outermost, RateLimit, CSRF innermost) ---
# Starlette applies middleware in LIFO order, so add innermost first.
app.add_middleware(CSRFMiddleware)
app.add_middleware(AuthRateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Console static dir: env, or prowlrbot package data (console), or cwd.
_CONSOLE_STATIC_ENV = "PROWLRBOT_CONSOLE_STATIC_DIR"


def _resolve_console_static_dir() -> str:
    if os.environ.get(_CONSOLE_STATIC_ENV):
        return os.environ[_CONSOLE_STATIC_ENV]
    # Shipped dist lives in prowlrbot package as static data (not a Python pkg).
    pkg_dir = Path(__file__).resolve().parent.parent
    candidate = pkg_dir / "console"
    if candidate.is_dir() and (candidate / "index.html").exists():
        return str(candidate)
    cwd = Path(os.getcwd())
    for subdir in ("console/dist", "console_dist"):
        candidate = cwd / subdir
        if candidate.is_dir() and (candidate / "index.html").exists():
            return str(candidate)
    return str(cwd / "console" / "dist")


_CONSOLE_STATIC_DIR = _resolve_console_static_dir()
_CONSOLE_INDEX = (
    Path(_CONSOLE_STATIC_DIR) / "index.html" if _CONSOLE_STATIC_DIR else None
)
logger.info(f"STATIC_DIR: {_CONSOLE_STATIC_DIR}")


@app.get("/")
def read_root():
    if _CONSOLE_INDEX and _CONSOLE_INDEX.exists():
        return FileResponse(_CONSOLE_INDEX)
    return {"message": "Hello World"}


@app.get("/api/version")
def get_version():
    """Return the current ProwlrBot version."""
    return {"version": __version__}


from fastapi import Depends

# --- API Authentication ---
auth_config = AuthConfig(
    enabled=bool(PROWLRBOT_API_TOKEN_HASH),
    token_hash=PROWLRBOT_API_TOKEN_HASH,
)
auth_dep = AuthDependency(auth_config)

app.include_router(api_router, prefix="/api", dependencies=[Depends(auth_dep)])

# --- WebSocket (real-time dashboard events) ---
event_bus = EventBus()
app.include_router(create_websocket_router(event_bus))

# Register as global singleton so subsystems (e.g. XPTracker) can push events.
from ..dashboard.events import set_global_event_bus as _set_global_event_bus

_set_global_event_bus(event_bus)

# --- War Room WebSocket (real-time war room events) ---
from ..hub.websocket import warroom_ws


@app.websocket("/ws/warroom")
async def ws_warroom(ws):
    await warroom_ws(ws)


app.include_router(
    agent_app.router,
    prefix="/api/agent",
    tags=["agent"],
    dependencies=[Depends(auth_dep)],
)

# --- A2A Protocol (agent-to-agent discovery + tasks) ---
from ..protocols.a2a_server import router as a2a_router

# A2A endpoints are auth-protected (except /.well-known/agent.json which is
# public for agent discovery per A2A spec).
app.include_router(a2a_router, dependencies=[Depends(auth_dep)])

# --- ROAR Protocol (unified agent communication) ---
from ..protocols.roar import AgentCard, AgentIdentity
from ..protocols.sdk import ROARServer, create_roar_router

_roar_identity = AgentIdentity(
    display_name="ProwlrBot",
    agent_type="agent",
    capabilities=["execute", "delegate", "monitor", "stream"],
)
roar_server = ROARServer(
    _roar_identity,
    description="ProwlrBot — Always watching. Always ready.",
    skills=["code", "monitor", "chat", "mcp", "a2a"],
    channels=["console", "discord", "telegram"],
)


# Public ROAR endpoints (no auth) so health checks and discovery work
@app.get("/roar/health", tags=["roar"])
def _roar_health() -> dict:
    """ROAR protocol health check. Used by Fly and external agents."""
    return {"status": "ok", "protocol": "roar/1.0"}


@app.get("/roar/card", tags=["roar"])
def _roar_card(request: Request) -> dict:
    """Return this agent's ROAR card for discovery (identity, endpoints)."""
    base = str(request.base_url).rstrip("/")
    card = AgentCard(
        identity=roar_server.identity,
        description=roar_server._description,
        skills=roar_server._skills,
        channels=roar_server._channels,
        endpoints={
            "http": f"{base}/roar/message",
            "websocket": f"{base}/roar/ws",
            "events": f"{base}/roar/events",
        },
    )
    return card.model_dump(by_alias=True)


app.include_router(
    create_roar_router(roar_server),
    dependencies=[Depends(auth_dep)],
)

# Wire EXECUTE and DELEGATE intents through AgentRunner
from ..protocols.roar import MessageIntent, ROARMessage as _ROARMessage


async def _roar_agent_handler(msg: _ROARMessage) -> _ROARMessage:
    """Route ROAR EXECUTE/DELEGATE messages through ProwlrBot's AgentRunner.

    Extracts the task text from the payload, runs it through the agent,
    and returns a RESPOND message with the result.
    """
    from agentscope_runtime.engine.schemas.agent_schemas import (
        AgentRequest,
        Message,
        TextContent,
    )

    task_text = (
        msg.payload.get("task")
        or msg.payload.get("prompt")
        or msg.payload.get("text")
        or str(msg.payload)
    )

    agent_request = AgentRequest(
        input=[
            Message(role="user", content=[TextContent(text=str(task_text))]),
        ],
        session_id=f"roar_{msg.id}",
        user_id=msg.from_identity.did,
    )

    last_text = ""
    async for agent_msg, _is_last in runner.stream_query(agent_request):
        text = getattr(agent_msg, "content", None)
        if isinstance(text, str):
            last_text = text
        elif hasattr(agent_msg, "get_text_content"):
            last_text = agent_msg.get_text_content() or last_text

    return _ROARMessage(
        **{"from": roar_server.identity, "to": msg.from_identity},
        intent=MessageIntent.RESPOND,
        payload={"result": last_text},
        context={"in_reply_to": msg.id},
    )


roar_server.on(MessageIntent.EXECUTE)(_roar_agent_handler)
roar_server.on(MessageIntent.DELEGATE)(_roar_agent_handler)

# Terminal WebSocket (PTY) — Unix only
try:
    from .routers.terminal import router as _terminal_router

    app.include_router(_terminal_router)
except ImportError:
    pass  # pty not available (Windows)

# Wire ROAR EventBus into A2A SSE streaming
from ..protocols.a2a_server import set_event_bus as _a2a_set_event_bus

_a2a_set_event_bus(roar_server.event_bus)

# Mount console: root static files (logo.png etc.) then assets, then SPA
# fallback.
if os.path.isdir(_CONSOLE_STATIC_DIR):
    _console_path = Path(_CONSOLE_STATIC_DIR)

    @app.get("/logo.png")
    def _console_logo():
        f = _console_path / "logo.png"
        if f.is_file():
            return FileResponse(f, media_type="image/png")

        raise HTTPException(status_code=404, detail="Not Found")

    @app.get("/prowlrbot-symbol.svg")
    def _console_icon():
        f = _console_path / "prowlrbot-symbol.svg"
        if f.is_file():
            return FileResponse(f, media_type="image/svg+xml")

        raise HTTPException(status_code=404, detail="Not Found")

    _assets_dir = _console_path / "assets"
    if _assets_dir.is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=str(_assets_dir)),
            name="assets",
        )

    @app.get("/{full_path:path}")
    def _console_spa(full_path: str):
        # Never serve SPA for API/protocol paths (let them 404 if not registered)
        if full_path.startswith(("api/", "roar/", "ws/")) or full_path in (
            "roar",
            "api",
            "ws",
        ):
            raise HTTPException(status_code=404, detail="Not Found")
        if _CONSOLE_INDEX and _CONSOLE_INDEX.exists():
            return FileResponse(_CONSOLE_INDEX)

        raise HTTPException(status_code=404, detail="Not Found")
