# -*- coding: utf-8 -*-
"""ProwlrHub HTTP Bridge — cross-machine war room coordination.

SQLite can't be shared across Mac and WSL. This bridge exposes the
war room engine over HTTP so remote Claude Code terminals can participate.

Run on the machine that hosts the database:
    python -m prowlrbot.hub.bridge

Remote terminals connect by setting PROWLR_HUB_URL in their MCP config.

Security: Set PROWLR_HUB_SECRET to enable Bearer token authentication.
Without it, the bridge is open (suitable for local-only use).
"""

# NOTE: intentionally no `from __future__ import annotations` here.
# FastAPI needs runtime-evaluable type annotations to detect Pydantic
# BaseModel parameters as request bodies (not query params).

import asyncio
import hmac
import logging
import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .engine import WarRoomEngine
from .status_page import STATUS_HTML
from .websocket import broadcast_ws, warroom_ws

logger = logging.getLogger(__name__)

# Max items returned by any list endpoint
_MAX_LIMIT = 500
_VALID_PRIORITIES = {"critical", "high", "normal", "low"}

# Default allowed origins — override with PROWLR_CORS_ORIGINS env var
# (comma-separated list of origins, e.g. "http://myhost:8088,http://myhost:5173")
_DEFAULT_ORIGINS = [
    "http://localhost:8088",
    "http://127.0.0.1:8088",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def _get_allowed_origins() -> list[str]:
    custom = os.environ.get("PROWLR_CORS_ORIGINS", "")
    if custom:
        return [o.strip() for o in custom.split(",") if o.strip()]
    return list(_DEFAULT_ORIGINS)


# For CSRF check on POST requests (open mode)
_ALLOWED_ORIGINS = set(
    _DEFAULT_ORIGINS[:2],
)  # only main app origins, not dev server

# Rate limiter — created lazily in create_bridge_app() so env vars are checked at runtime
limiter: Limiter = None  # type: ignore[assignment]


# --- Security middleware ---


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response


class CSRFMiddleware(BaseHTTPMiddleware):
    """Block cross-origin POST requests in open mode (no Bearer auth).

    When PROWLR_HUB_SECRET is unset, there's no auth layer protecting
    state-changing endpoints. This middleware validates the Origin header
    on POST requests to prevent CSRF attacks from malicious sites.
    """

    async def dispatch(self, request, call_next):
        if request.method == "POST" and not _get_hub_secret():
            origin = request.headers.get("origin", "")
            # Allow requests with no Origin (same-origin, curl, MCP clients)
            allowed = set(_get_allowed_origins())
            if origin and origin not in allowed:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Cross-origin request blocked"},
                )
        return await call_next(request)


# --- Authentication ---


def _get_hub_secret() -> str:
    return os.environ.get("PROWLR_HUB_SECRET", "")


async def verify_auth(request: Request):
    """Verify Bearer token if PROWLR_HUB_SECRET is set."""
    secret = _get_hub_secret()
    if not secret:
        return  # Open mode when no secret configured

    # Allow unauthenticated access to health, status page, and docs
    if request.url.path in (
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    ):
        return

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication")

    token = auth[7:]
    if not hmac.compare_digest(token, secret):
        raise HTTPException(status_code=403, detail="Invalid token")


# --- Request models with input validation ---


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    capabilities: List[str] = Field(default=["general"], max_length=20)


class ClaimRequest(BaseModel):
    task_id: str = Field(default="", max_length=64)
    title: str = Field(default="", max_length=512)
    file_scopes: List[str] = Field(default=[], max_length=50)
    description: str = Field(default="", max_length=8192)
    priority: str = Field(default="normal", max_length=16)


class UpdateRequest(BaseModel):
    task_id: str = Field(..., max_length=64)
    progress_note: str = Field(..., max_length=4096)


class CompleteRequest(BaseModel):
    task_id: str = Field(..., max_length=64)
    summary: str = Field(default="", max_length=8192)


class FailRequest(BaseModel):
    task_id: str = Field(..., max_length=64)
    reason: str = Field(default="", max_length=4096)


class LockRequest(BaseModel):
    path: str = Field(..., min_length=1, max_length=1024)


class ConflictRequest(BaseModel):
    paths: List[str] = Field(..., max_length=50)


class BroadcastRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4096)


class FindingRequest(BaseModel):
    key: str = Field(..., min_length=1, max_length=256)
    value: str = Field(..., max_length=65536)


# --- Path validation ---


def _verify_session(
    engine: WarRoomEngine,
    agent_id: str,
    request: Request,
) -> None:
    """Verify the X-Session-Token header matches the agent's session_id.

    This prevents agent impersonation — knowing an agent_id alone is not
    enough to act on its behalf. The session_id is only returned at registration.
    """
    token = request.headers.get("X-Session-Token", "")
    if not token:
        raise HTTPException(status_code=401, detail="Missing session token")
    row = engine._conn.execute(
        "SELECT session_id FROM agents WHERE agent_id=?",
        (agent_id,),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    if not hmac.compare_digest(token, row["session_id"]):
        raise HTTPException(status_code=403, detail="Invalid session token")


def _validate_lock_path(path: str) -> str:
    """Reject path traversal and absolute paths."""
    if "\x00" in path:
        raise HTTPException(status_code=400, detail="Invalid path")
    if path.startswith("/") or path.startswith("\\"):
        raise HTTPException(
            status_code=400,
            detail="Absolute paths not allowed",
        )
    normalized = os.path.normpath(path)
    if normalized.startswith(".."):
        raise HTTPException(
            status_code=400,
            detail="Path traversal not allowed",
        )
    return normalized


def _clamp_limit(limit: int) -> int:
    return max(1, min(limit, _MAX_LIMIT))


def create_bridge_app() -> FastAPI:
    """Create a FastAPI app that exposes the war room engine over HTTP."""
    global limiter
    limiter = Limiter(
        key_func=get_remote_address,
        enabled=not bool(os.environ.get("PROWLR_NO_RATE_LIMIT")),
    )

    db_path = os.environ.get("PROWLR_HUB_DB", None)
    engine = WarRoomEngine(db_path)
    engine.get_or_create_default_room()

    _sweep_interval_sec = 60
    _sweep_ttl_minutes = 5

    async def _sweep_loop():
        while True:
            await asyncio.sleep(_sweep_interval_sec)
            try:
                await asyncio.to_thread(
                    engine.sweep_dead_agents,
                    _sweep_ttl_minutes,
                )
            except Exception as e:
                logger.warning("Sweep dead agents failed: %s", e)

    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        sweep_task = asyncio.create_task(_sweep_loop())
        logger.info(
            "Dead agent sweep started (every %ds, TTL %d min)",
            _sweep_interval_sec,
            _sweep_ttl_minutes,
        )
        try:
            yield
        finally:
            sweep_task.cancel()
            try:
                await sweep_task
            except asyncio.CancelledError:
                pass

    app = FastAPI(
        title="ProwlrHub Bridge",
        version="1.0.0",
        dependencies=[Depends(verify_auth)],
        lifespan=_lifespan,
    )
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Try again later."},
        )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CSRFMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_get_allowed_origins(),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
        allow_credentials=False,
    )

    # Wire engine events → WebSocket broadcast
    def _on_engine_event(event: dict):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(broadcast_ws(event))
        except RuntimeError:
            pass  # No event loop yet

    engine.set_event_callback(_on_engine_event)

    # WebSocket endpoint for real-time war room events
    @app.websocket("/ws/warroom")
    async def ws_warroom(ws):
        await warroom_ws(ws)

    @app.get("/", response_class=HTMLResponse)
    async def status_page():
        """Standalone war room status page."""
        return STATUS_HTML

    def _active_agents_only(agents: list) -> list:
        """Filter to agents that are not disconnected (for display/counts)."""
        return [a for a in agents if a.get("status") != "disconnected"]

    @app.get("/health")
    def health():
        room = engine.get_or_create_default_room()
        all_agents = engine.get_agents(room["room_id"])
        agents_active = _active_agents_only(all_agents)
        tasks = engine.get_mission_board(room["room_id"])
        return {
            "status": "ok",
            "room_id": room["room_id"],
            "agents": len(agents_active),
            "tasks": len(tasks),
        }

    @app.post("/register")
    @limiter.limit("10/minute")
    def register(request: Request, req: RegisterRequest):
        room = engine.get_or_create_default_room()
        result = engine.register_agent(
            req.name,
            room["room_id"],
            req.capabilities,
        )
        return result

    @app.post("/heartbeat/{agent_id}")
    @limiter.limit("30/minute")
    def heartbeat(request: Request, agent_id: str):
        _verify_session(engine, agent_id, request)
        engine.heartbeat(agent_id)
        return {"ok": True}

    @app.get("/board")
    @limiter.limit("60/minute")
    def mission_board(request: Request, status: str = ""):
        room = engine.get_or_create_default_room()
        tasks = engine.get_mission_board(room["room_id"])
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        return {"tasks": tasks}

    @app.post("/claim/{agent_id}")
    @limiter.limit("20/minute")
    def claim_task(request: Request, agent_id: str, req: ClaimRequest):
        _verify_session(engine, agent_id, request)
        if req.priority not in _VALID_PRIORITIES:
            raise HTTPException(status_code=400, detail="Invalid priority")
        room = engine.get_or_create_default_room()
        task_id = req.task_id
        if not task_id and req.title:
            task = engine.create_task(
                room["room_id"],
                req.title,
                description=req.description,
                file_scopes=req.file_scopes,
                priority=req.priority,
            )
            task_id = task["task_id"]
        result = engine.claim_task(task_id, agent_id, room["room_id"])
        if result.success:
            return {"success": True, "lock_token": result.lock_token}
        return {
            "success": False,
            "reason": result.reason,
            "conflicts": result.conflicts,
        }

    @app.post("/update/{agent_id}")
    @limiter.limit("30/minute")
    def update_task(request: Request, agent_id: str, req: UpdateRequest):
        _verify_session(engine, agent_id, request)
        engine.update_task(req.task_id, agent_id, req.progress_note)
        return {"ok": True}

    @app.post("/complete/{agent_id}")
    @limiter.limit("20/minute")
    def complete_task(request: Request, agent_id: str, req: CompleteRequest):
        _verify_session(engine, agent_id, request)
        ok = engine.complete_task(req.task_id, agent_id, req.summary)
        return {"ok": ok}

    @app.post("/fail/{agent_id}")
    @limiter.limit("20/minute")
    def fail_task(request: Request, agent_id: str, req: FailRequest):
        _verify_session(engine, agent_id, request)
        ok = engine.fail_task(req.task_id, agent_id, req.reason)
        return {"ok": ok}

    @app.post("/lock/{agent_id}")
    @limiter.limit("30/minute")
    def lock_file(request: Request, agent_id: str, req: LockRequest):
        _verify_session(engine, agent_id, request)
        safe_path = _validate_lock_path(req.path)
        room = engine.get_or_create_default_room()
        result = engine.lock_file(safe_path, agent_id, room["room_id"])
        if result.success:
            return {"success": True, "lock_token": result.lock_token}
        return {
            "success": False,
            "reason": result.reason,
            "owner": result.owner,
        }

    @app.post("/unlock/{agent_id}")
    @limiter.limit("30/minute")
    def unlock_file(request: Request, agent_id: str, req: LockRequest):
        _verify_session(engine, agent_id, request)
        safe_path = _validate_lock_path(req.path)
        room = engine.get_or_create_default_room()
        ok = engine.unlock_file(safe_path, agent_id, room["room_id"])
        return {"ok": ok}

    @app.post("/conflicts")
    @limiter.limit("30/minute")
    def check_conflicts(request: Request, req: ConflictRequest):
        room = engine.get_or_create_default_room()
        conflicts = engine.check_conflicts(req.paths, room["room_id"])
        return {"conflicts": conflicts}

    @app.get("/agents")
    @limiter.limit("60/minute")
    def get_agents(request: Request, include_disconnected: bool = False):
        room = engine.get_or_create_default_room()
        agents = engine.get_agents(room["room_id"])
        if not include_disconnected:
            agents = _active_agents_only(agents)
        return {"agents": agents}

    @app.post("/broadcast/{agent_id}")
    @limiter.limit("20/minute")
    def broadcast(request: Request, agent_id: str, req: BroadcastRequest):
        _verify_session(engine, agent_id, request)
        room = engine.get_or_create_default_room()
        engine.broadcast_status(room["room_id"], agent_id, req.message)
        return {"ok": True}

    @app.post("/findings/{agent_id}")
    @limiter.limit("30/minute")
    def share_finding(request: Request, agent_id: str, req: FindingRequest):
        _verify_session(engine, agent_id, request)
        room = engine.get_or_create_default_room()
        engine.set_context(room["room_id"], agent_id, req.key, req.value)
        return {"ok": True}

    @app.get("/context")
    @limiter.limit("60/minute")
    def get_context(request: Request, key: str = ""):
        room = engine.get_or_create_default_room()
        return {"context": engine.get_context(room["room_id"], key)}

    @app.get("/events")
    @limiter.limit("60/minute")
    def get_events(request: Request, limit: int = 20, event_type: str = ""):
        room = engine.get_or_create_default_room()
        return {
            "events": engine.get_events(
                room["room_id"],
                _clamp_limit(limit),
                event_type,
            ),
        }

    # --- JSON API endpoints for dashboard consumption ---

    @app.get("/api/agents")
    @limiter.limit("60/minute")
    def api_agents(request: Request, include_disconnected: bool = False):
        room = engine.get_or_create_default_room()
        agents = engine.get_agents(room["room_id"])
        if not include_disconnected:
            agents = _active_agents_only(agents)
        return agents

    @app.get("/api/board")
    @limiter.limit("60/minute")
    def api_board(request: Request, status: str = ""):
        room = engine.get_or_create_default_room()
        tasks = engine.get_mission_board(room["room_id"])
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        return tasks

    @app.get("/api/events")
    @limiter.limit("60/minute")
    def api_events(request: Request, limit: int = 50, event_type: str = ""):
        room = engine.get_or_create_default_room()
        return engine.get_events(
            room["room_id"],
            _clamp_limit(limit),
            event_type,
        )

    @app.get("/api/context")
    @limiter.limit("60/minute")
    def api_context(request: Request, key: str = ""):
        room = engine.get_or_create_default_room()
        return engine.get_context(room["room_id"], key)

    @app.get("/api/conflicts")
    @limiter.limit("60/minute")
    def api_conflicts(request: Request):
        room = engine.get_or_create_default_room()
        room_id = room["room_id"]
        rows = engine._conn.execute(
            """SELECT fl.*, a.name as agent_name
               FROM file_locks fl
               LEFT JOIN agents a ON fl.agent_id = a.agent_id
               WHERE fl.room_id=?
               ORDER BY fl.acquired_at DESC""",
            (room_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    return app


def run_bridge():
    """Run the HTTP bridge server."""
    import uvicorn

    host = os.environ.get("PROWLR_BRIDGE_HOST", "127.0.0.1")
    port = int(os.environ.get("PROWLR_BRIDGE_PORT", "8099"))

    logging.basicConfig(level=logging.INFO)
    logger.info("ProwlrHub Bridge starting on %s:%d", host, port)

    app = create_bridge_app()
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_bridge()
