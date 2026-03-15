# -*- coding: utf-8 -*-
"""API endpoints for agent templates."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from ...constant import WORKING_DIR
from ...templates.store import AgentTemplate, TemplateStore

router = APIRouter(prefix="/templates", tags=["templates"])

_store = TemplateStore(db_path=WORKING_DIR / "templates.db")


@router.get("", response_model=List[AgentTemplate])
async def list_templates(
    category: Optional[str] = None,
    builtin_only: bool = False,
) -> List[AgentTemplate]:
    return _store.list_templates(category=category, builtin_only=builtin_only)


@router.get("/search", response_model=List[AgentTemplate])
async def search_templates(query: str) -> List[AgentTemplate]:
    return _store.search(query)


@router.get("/{template_id}", response_model=AgentTemplate)
async def get_template(template_id: str) -> AgentTemplate:
    template = _store.get(template_id)
    if not template:
        raise HTTPException(404, f"Template '{template_id}' not found")
    return template


@router.post("", response_model=AgentTemplate)
async def create_template(template: AgentTemplate) -> AgentTemplate:
    return _store.create(template)


@router.put("/{template_id}", response_model=AgentTemplate)
async def update_template(
    template_id: str,
    updates: Dict[str, Any],
) -> AgentTemplate:
    template = _store.update(template_id, **updates)
    if not template:
        raise HTTPException(
            404,
            "Template not found or is a built-in template",
        )
    return template


@router.delete("/{template_id}")
async def delete_template(template_id: str) -> Dict[str, str]:
    if not _store.delete(template_id):
        raise HTTPException(
            404,
            "Template not found or is a built-in template",
        )
    return {"status": "deleted"}


@router.post("/{template_id}/download")
async def download_template(template_id: str) -> AgentTemplate:
    template = _store.get(template_id)
    if not template:
        raise HTTPException(404, f"Template '{template_id}' not found")
    _store.record_download(template_id)
    return template
