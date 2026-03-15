#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bridge API server that receives authenticated job requests from workers."""

import hashlib
import hmac
import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import Config
from capabilities import CapabilityExecutor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global executor instance
executor: Optional[CapabilityExecutor] = None


class ExecuteRequest(BaseModel):
    """Request to execute a capability."""

    job_id: str
    capability: str
    parameters: dict = {}


class ExecuteResponse(BaseModel):
    """Response from capability execution."""

    job_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None
    executed_at: float


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    global executor
    # Startup
    Config.validate()
    executor = CapabilityExecutor()
    logger.info(f"Bridge API started on {Config.HOST}:{Config.PORT}")
    yield
    # Shutdown
    logger.info("Bridge API shutting down")


app = FastAPI(
    title="AI Swarm Bridge API",
    description="Secure bridge for executing capabilities on macOS",
    version="1.0.0",
    lifespan=lifespan,
)


def verify_hmac_signature(request_body: bytes, signature: str) -> bool:
    """Verify HMAC-SHA256 signature of request body."""
    if not signature:
        return False
    expected = hmac.new(
        Config.HMAC_SECRET.encode(),
        request_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@app.middleware("http")
async def hmac_auth_middleware(request: Request, call_next):
    """Middleware to verify HMAC signatures and IP allowlist."""
    # Skip auth for health check
    if request.url.path == "/health":
        return await call_next(request)

    # Check IP allowlist
    allowed_ips = Config.get_allowed_ips()
    client_ip = request.client.host if request.client else "unknown"
    if allowed_ips and client_ip not in allowed_ips:
        logger.warning(f"Request from unauthorized IP: {client_ip}")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "IP not authorized"},
        )

    # Read and verify signature
    body = await request.body()
    signature = request.headers.get("X-Swarm-Signature", "")

    if not verify_hmac_signature(body, signature):
        logger.warning(f"Invalid signature from {client_ip}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Invalid signature"},
        )

    # Store body for route handler
    request.state.body = body
    return await call_next(request)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/capabilities")
async def list_capabilities():
    """List available capabilities."""
    caps = executor.list_capabilities() if executor else []
    return {"capabilities": caps}


@app.post("/execute", response_model=ExecuteResponse)
async def execute_capability(request: Request):
    """Execute a capability with the given parameters."""
    if not executor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Executor not initialized",
        )

    try:
        # Parse request body
        body = request.state.body
        data = json.loads(body)
        exec_request = ExecuteRequest(**data)

        logger.info(
            f"Executing {exec_request.capability} for job {exec_request.job_id}",
        )

        # Execute the capability
        result = await executor.execute(
            exec_request.capability,
            exec_request.parameters,
        )

        return ExecuteResponse(
            job_id=exec_request.job_id,
            status="success",
            result=result,
            executed_at=time.time(),
        )

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON",
        )
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        return ExecuteResponse(
            job_id=data.get("job_id", "unknown"),
            status="error",
            error=str(e),
            executed_at=time.time(),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=Config.HOST, port=Config.PORT)
