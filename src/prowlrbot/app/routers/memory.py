# -*- coding: utf-8 -*-
"""Memory API router — exposes tiered agent memory to the console.

Connects the frontend Memory page to the ArchiveDB (long-term) and
MemoryTierManager (promotion logic). Short-term memory lives in-process
and is not directly queryable via API.
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ...agents.memory.archive_db import ArchiveDB
from ...agents.memory.tier_manager import MemoryTierManager
from ...auth.middleware import get_current_user
from ...constant import WORKING_DIR

router = APIRouter(prefix="/memory", tags=["memory"])

# Lazy singleton — initialized on first request
_archive: Optional[ArchiveDB] = None
_tier_mgr: Optional[MemoryTierManager] = None


def _get_archive() -> ArchiveDB:
    global _archive, _tier_mgr
    if _archive is None:
        db_path = os.environ.get(
            "PROWLR_MEMORY_DB",
            str(WORKING_DIR / "memory_archive.db"),
        )
        _archive = ArchiveDB(db_path)
        _tier_mgr = MemoryTierManager(_archive)
    return _archive


def _get_tier_mgr() -> MemoryTierManager:
    _get_archive()
    assert _tier_mgr is not None
    return _tier_mgr


@router.get("")
async def list_memories(
    agent_id: str = "default",
    tier: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List memory entries for an agent.

    The ``tier`` filter is informational — all persisted entries are
    considered "long" tier.  Short-term memory lives in-process and
    is not exposed via this API.
    """
    archive = _get_archive()
    entries = archive.list_by_agent(agent_id, limit=limit, offset=offset)

    # Tag all persisted entries as "long" tier (they survived promotion)
    for e in entries:
        e["tier"] = "long"

    if tier and tier != "long":
        # Short/medium tiers live in-process — return empty for now
        return []

    return entries


@router.get("/search")
async def search_memories(
    agent_id: str = "default",
    q: str = "",
    limit: int = 20,
):
    """Full-text search across an agent's memory archive."""
    if not q.strip():
        return []
    archive = _get_archive()
    results = archive.search(agent_id, q, limit=limit)
    for r in results:
        r["tier"] = "long"
    return results


class StoreRequest(BaseModel):
    agent_id: str = Field(default="default", max_length=128)
    topic: str = Field(..., min_length=1, max_length=512)
    summary: str = Field(..., min_length=1, max_length=65536)
    importance: int = Field(default=1, ge=0, le=10)


@router.post("")
async def store_memory(req: StoreRequest, _user=Depends(get_current_user)):
    """Store a new memory entry directly into the archive."""
    archive = _get_archive()
    entry_id = archive.store(
        agent_id=req.agent_id,
        topic=req.topic,
        summary=req.summary,
        importance=req.importance,
    )
    return {"id": entry_id}


@router.post("/{entry_id}/promote")
async def promote_memory(entry_id: str, _user=Depends(get_current_user)):
    """Manually promote a memory entry (bumps importance)."""
    archive = _get_archive()
    entry = archive.get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    # Record access to increase access_count (used by tier manager)
    archive.record_access(entry_id)
    return {"ok": True, "access_count": entry["access_count"] + 1}


@router.delete("/{entry_id}")
async def delete_memory(entry_id: str, _user=Depends(get_current_user)):
    """Delete a memory entry."""
    archive = _get_archive()
    ok = archive.delete(entry_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return {"ok": True}


@router.get("/stats")
async def memory_stats(agent_id: Optional[str] = None):
    """Return memory statistics."""
    archive = _get_archive()
    return {
        "total_entries": archive.count(agent_id),
        "agent_id": agent_id or "all",
    }
