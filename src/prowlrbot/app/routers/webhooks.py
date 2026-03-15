# -*- coding: utf-8 -*-
"""FastAPI router for webhook builder CRUD and trigger ingestion."""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ...auth.middleware import get_current_user
from ...webhooks.models import TriggerType, WebhookRule
from ...webhooks.store import WebhookStore
from ...webhooks.executor import WebhookExecutor
from ...constant import WORKING_DIR

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# ------------------------------------------------------------------
# Request / response helpers
# ------------------------------------------------------------------


class ToggleRequest(BaseModel):
    enabled: bool


class TriggerRequest(BaseModel):
    """Incoming webhook trigger payload."""

    trigger_type: TriggerType
    data: Dict[str, Any] = Field(default_factory=dict)


class TriggerResponse(BaseModel):
    matched: int
    results: list[Dict[str, Any]]


# ------------------------------------------------------------------
# Dependency helpers
# ------------------------------------------------------------------


def _get_store(request: Request) -> WebhookStore:
    """Return the WebhookStore, creating one lazily on app state."""
    store: Optional[WebhookStore] = getattr(
        request.app.state,
        "webhook_store",
        None,
    )
    if store is None:
        store = WebhookStore(WORKING_DIR)
        request.app.state.webhook_store = store
    return store


def _get_executor(request: Request) -> WebhookExecutor:
    """Return the WebhookExecutor, creating one lazily on app state."""
    executor: Optional[WebhookExecutor] = getattr(
        request.app.state,
        "webhook_executor",
        None,
    )
    if executor is None:
        store = _get_store(request)
        executor = WebhookExecutor(store)
        request.app.state.webhook_executor = executor
    return executor


# ------------------------------------------------------------------
# CRUD endpoints
# ------------------------------------------------------------------


@router.get("/rules", response_model=list[WebhookRule])
async def list_rules(request: Request):
    """List all webhook rules."""
    store = _get_store(request)
    return await store.list_rules()


@router.get("/rules/{rule_id}", response_model=WebhookRule)
async def get_rule(rule_id: str, request: Request):
    """Get a single webhook rule by id."""
    store = _get_store(request)
    rule = await store.get_rule(rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="webhook rule not found")
    return rule


@router.post("/rules", response_model=WebhookRule, status_code=201)
async def create_rule(
    rule: WebhookRule,
    request: Request,
    _user=Depends(get_current_user),
):
    """Create a new webhook rule (server generates id)."""
    store = _get_store(request)
    rule = rule.model_copy(update={"id": str(uuid.uuid4())})
    return await store.create_rule(rule)


@router.put("/rules/{rule_id}", response_model=WebhookRule)
async def update_rule(
    rule_id: str,
    rule: WebhookRule,
    request: Request,
    _user=Depends(get_current_user),
):
    """Replace a webhook rule by id."""
    store = _get_store(request)
    if rule.id and rule.id != rule_id:
        raise HTTPException(status_code=400, detail="rule_id mismatch")
    rule = rule.model_copy(update={"id": rule_id})
    updated = await store.update_rule(rule)
    if updated is None:
        raise HTTPException(status_code=404, detail="webhook rule not found")
    return updated


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: str,
    request: Request,
    _user=Depends(get_current_user),
):
    """Delete a webhook rule by id."""
    store = _get_store(request)
    ok = await store.delete_rule(rule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="webhook rule not found")
    return {"deleted": True}


@router.post("/rules/{rule_id}/toggle", response_model=WebhookRule)
async def toggle_rule(
    rule_id: str,
    body: ToggleRequest,
    request: Request,
    _user=Depends(get_current_user),
):
    """Enable or disable a webhook rule."""
    store = _get_store(request)
    updated = await store.toggle_enabled(rule_id, body.enabled)
    if updated is None:
        raise HTTPException(status_code=404, detail="webhook rule not found")
    return updated


# ------------------------------------------------------------------
# Trigger ingestion
# ------------------------------------------------------------------


@router.post("/trigger", response_model=TriggerResponse)
async def receive_trigger(
    body: TriggerRequest,
    request: Request,
    _user=Depends(get_current_user),
):
    """Receive an incoming trigger and execute all matching rules."""
    executor = _get_executor(request)
    results = await executor.handle_trigger(body.trigger_type, body.data)
    return TriggerResponse(matched=len(results), results=results)
