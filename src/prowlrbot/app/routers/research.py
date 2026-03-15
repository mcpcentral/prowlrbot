# -*- coding: utf-8 -*-
"""API endpoints for AutoResearch workflows."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...constant import WORKING_DIR
from ...research.engine import ResearchEngine
from ...research.models import (
    ResearchProject,
    ResearchSummary,
    SourceType,
)
from ...research.store import ResearchStore

router = APIRouter(prefix="/research", tags=["research"])

_store = ResearchStore(db_path=WORKING_DIR / "research.db")
_engine = ResearchEngine(store=_store)


class CreateProjectRequest(BaseModel):
    topic: str
    objective: str = ""
    max_sources: int = 20


class AddSourceRequest(BaseModel):
    title: str
    content: str
    url: str = ""
    source_type: SourceType = SourceType.WEB


@router.post("/projects", response_model=ResearchProject)
async def create_project(req: CreateProjectRequest) -> ResearchProject:
    return _engine.create_project(req.topic, req.objective, req.max_sources)


@router.get("/projects", response_model=List[ResearchSummary])
async def list_projects(
    status: Optional[str] = None,
    limit: int = 50,
) -> List[ResearchSummary]:
    return _store.list_projects(status=status, limit=limit)


@router.get("/projects/{project_id}", response_model=ResearchProject)
async def get_project(project_id: str) -> ResearchProject:
    project = _store.get_project(project_id)
    if not project:
        raise HTTPException(404, f"Research project '{project_id}' not found")
    return project


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str) -> Dict[str, str]:
    if not _store.delete_project(project_id):
        raise HTTPException(404, f"Research project '{project_id}' not found")
    return {"status": "deleted"}


@router.post("/projects/{project_id}/sources", response_model=ResearchProject)
async def add_source(
    project_id: str,
    req: AddSourceRequest,
) -> ResearchProject:
    project = _engine.add_source(
        project_id,
        req.title,
        req.content,
        req.url,
        req.source_type,
    )
    if not project:
        raise HTTPException(404, f"Research project '{project_id}' not found")
    return project


@router.post("/projects/{project_id}/analyze", response_model=ResearchProject)
async def analyze_project(project_id: str) -> ResearchProject:
    project = _engine.analyze(project_id)
    if not project:
        raise HTTPException(404, f"Research project '{project_id}' not found")
    return project


@router.post(
    "/projects/{project_id}/synthesize",
    response_model=ResearchProject,
)
async def synthesize_project(project_id: str) -> ResearchProject:
    project = _engine.synthesize(project_id)
    if not project:
        raise HTTPException(404, f"Research project '{project_id}' not found")
    return project


@router.get("/projects/{project_id}/context")
async def get_llm_context(project_id: str) -> Dict[str, str]:
    context = _engine.get_context_for_llm(project_id)
    if not context:
        raise HTTPException(404, f"Research project '{project_id}' not found")
    return {"context": context}
