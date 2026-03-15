# -*- coding: utf-8 -*-
"""Audit trail API endpoints."""

from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, Response

from prowlrbot.security.audit import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


def _get_audit_log() -> AuditLog:
    """Return a short-lived AuditLog handle.

    Each request opens its own connection so we avoid threading issues
    with SQLite.  WAL mode ensures readers do not block writers.
    """
    return AuditLog()


@router.get("/logs")
async def get_audit_logs(
    actor: Optional[str] = Query(None, description="Filter by actor"),
    action: Optional[str] = Query(None, description="Filter by action"),
    target: Optional[str] = Query(None, description="Filter by target"),
    result: Optional[str] = Query(None, description="Filter by result"),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Max entries to return",
    ),
):
    """Query the audit trail with optional filters."""
    audit = _get_audit_log()
    try:
        entries = audit.query(
            actor=actor,
            action=action,
            target=target,
            result=result,
            limit=limit,
        )
        return [entry.model_dump() for entry in entries]
    finally:
        audit.close()


@router.get("/export")
async def export_audit_log(
    format: str = Query("json", description="Export format (json)"),
):
    """Export the full audit log."""
    audit = _get_audit_log()
    try:
        data = audit.export(format=format)
        return Response(
            content=data,
            media_type="application/json",
            headers={
                "Content-Disposition": "attachment; filename=audit_log.json",
            },
        )
    finally:
        audit.close()
