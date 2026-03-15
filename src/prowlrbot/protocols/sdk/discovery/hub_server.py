# -*- coding: utf-8 -*-
"""Hub server — REST API for federated agent discovery.

Serves as the backend that ``HubClient`` talks to. Uses the
in-memory ``AgentDirectory`` internally for storage.

Endpoints:
  - POST   /agents      — Register an agent card
  - GET    /agents/:did  — Look up by DID
  - GET    /agents?q=    — Search by capability
  - DELETE /agents/:did  — Unregister

Usage::

    from fastapi import FastAPI
    from prowlrbot.protocols.sdk.discovery.hub_server import create_hub_router

    app = FastAPI()
    app.include_router(create_hub_router(api_key="my-secret-key"))
"""

from __future__ import annotations

import hmac as _hmac
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from ...roar import AgentCard, AgentDirectory, AgentIdentity, DiscoveryEntry

logger = logging.getLogger(__name__)

# Limits to prevent abuse
_MAX_FIELD_LENGTH = 500
_MAX_LIST_LENGTH = 50
_MAX_AGENTS = 10_000


class RegisterRequest(BaseModel):
    """Request body for agent registration."""

    did: str = ""
    display_name: str = ""
    agent_type: str = "agent"
    description: str = ""
    skills: List[str] = Field(default_factory=list)
    channels: List[str] = Field(default_factory=list)
    endpoints: Dict[str, str] = Field(default_factory=dict)
    capabilities: List[str] = Field(default_factory=list)

    @field_validator("did", "display_name", "agent_type", "description")
    @classmethod
    def validate_string_length(cls, v: str) -> str:
        if len(v) > _MAX_FIELD_LENGTH:
            raise ValueError(
                f"Field exceeds maximum length of {_MAX_FIELD_LENGTH}",
            )
        return v

    @field_validator("skills", "channels", "capabilities")
    @classmethod
    def validate_list_length(cls, v: list) -> list:
        if len(v) > _MAX_LIST_LENGTH:
            raise ValueError(
                f"List exceeds maximum length of {_MAX_LIST_LENGTH}",
            )
        for item in v:
            if isinstance(item, str) and len(item) > _MAX_FIELD_LENGTH:
                raise ValueError(
                    f"List item exceeds maximum length of {_MAX_FIELD_LENGTH}",
                )
        return v

    @field_validator("endpoints")
    @classmethod
    def validate_endpoints(cls, v: dict) -> dict:
        if len(v) > _MAX_LIST_LENGTH:
            raise ValueError(
                f"Endpoints exceeds maximum count of {_MAX_LIST_LENGTH}",
            )
        for key, val in v.items():
            if len(key) > _MAX_FIELD_LENGTH or len(val) > _MAX_FIELD_LENGTH:
                raise ValueError(
                    f"Endpoint key/value exceeds maximum length of {_MAX_FIELD_LENGTH}",
                )
        return v


def _entry_to_dict(entry: DiscoveryEntry) -> Dict[str, Any]:
    """Serialize a DiscoveryEntry to the hub response format."""
    card = entry.agent_card
    return {
        "did": card.identity.did,
        "display_name": card.identity.display_name,
        "agent_type": card.identity.agent_type,
        "description": card.description,
        "skills": card.skills,
        "channels": card.channels,
        "endpoints": card.endpoints,
        "capabilities": card.identity.capabilities,
        "registered_at": entry.registered_at,
        "last_seen": entry.last_seen,
    }


def create_hub_router(api_key: str = "") -> APIRouter:
    """Create a FastAPI router implementing the Discovery Hub API.

    Args:
        api_key: API key for authentication. When set, all requests must
            include a matching ``X-API-Key`` header. Empty string disables
            auth (NOT recommended for production).

    Returns:
        An APIRouter with agent registration, lookup, search, and
        unregister endpoints.
    """
    if not api_key:
        logger.warning(
            "Hub server created WITHOUT an API key — all endpoints are unauthenticated. "
            "Set an api_key for production deployments.",
        )

    router = APIRouter(tags=["hub"])
    directory = AgentDirectory()

    def _check_api_key(key: Optional[str]) -> None:
        """Raise 401 if API key is required but missing/invalid."""
        if api_key:
            if not key or not _hmac.compare_digest(key, api_key):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or missing API key",
                )

    @router.post("/agents")
    async def register_agent(
        body: RegisterRequest,
        x_api_key: Optional[str] = Header(None),
    ) -> Dict[str, Any]:
        """Register an agent card with the hub."""
        _check_api_key(x_api_key)

        # Enforce max agents limit
        if len(directory.list_all()) >= _MAX_AGENTS:
            raise HTTPException(
                status_code=507,
                detail=f"Hub agent limit reached ({_MAX_AGENTS})",
            )

        identity = AgentIdentity(
            did=body.did or "",
            display_name=body.display_name,
            agent_type=body.agent_type,
            capabilities=body.capabilities,
        )
        if body.did:
            identity.did = body.did

        card = AgentCard(
            identity=identity,
            description=body.description,
            skills=body.skills,
            channels=body.channels,
            endpoints=body.endpoints,
        )

        entry = directory.register(card)
        logger.info(
            "Hub: registered agent %s (%s)",
            identity.did,
            body.display_name,
        )
        return _entry_to_dict(entry)

    @router.get("/agents/{did:path}")
    async def lookup_agent(
        did: str,
        x_api_key: Optional[str] = Header(None),
    ) -> Dict[str, Any]:
        """Look up an agent by DID."""
        _check_api_key(x_api_key)

        entry = directory.lookup(did)
        if entry is None:
            raise HTTPException(status_code=404, detail="Agent not found")
        return _entry_to_dict(entry)

    @router.get("/agents")
    async def search_agents(
        q: str = "",
        x_api_key: Optional[str] = Header(None),
    ) -> Dict[str, Any]:
        """Search for agents by capability or list all."""
        _check_api_key(x_api_key)

        if q:
            entries = directory.search(q)
        else:
            entries = directory.list_all()

        return {
            "agents": [_entry_to_dict(e) for e in entries],
            "count": len(entries),
        }

    @router.delete("/agents/{did:path}")
    async def unregister_agent(
        did: str,
        x_api_key: Optional[str] = Header(None),
    ) -> Dict[str, Any]:
        """Unregister an agent from the hub."""
        _check_api_key(x_api_key)

        removed = directory.unregister(did)
        if not removed:
            raise HTTPException(status_code=404, detail="Agent not found")
        logger.info("Hub: unregistered agent %s", did)
        return {"status": "removed", "did": did}

    return router
