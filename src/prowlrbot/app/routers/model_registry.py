# -*- coding: utf-8 -*-
"""API routes for the model registry."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Body, HTTPException, Path, Query
from pydantic import BaseModel, Field

from ...model_registry.models import (
    ModelCapability,
    ModelComparison,
    ModelEntry,
    ModelType,
)
from ...model_registry.registry import ModelRegistry

router = APIRouter(prefix="/model-registry", tags=["model-registry"])


def _get_registry() -> ModelRegistry:
    """Return a ModelRegistry instance (lazy singleton)."""
    if not hasattr(_get_registry, "_instance"):
        _get_registry._instance = ModelRegistry()
    return _get_registry._instance


# -- Request / Response schemas --


class RegisterModelRequest(BaseModel):
    name: str = Field(..., description="Model name, e.g. 'gpt-4o'")
    provider: str = Field(..., description="Provider id, e.g. 'openai'")
    model_type: ModelType = Field(default=ModelType.chat)
    capabilities: list[ModelCapability] = Field(default_factory=list)
    context_window: int = Field(default=4096)
    max_output_tokens: int = Field(default=4096)
    cost_per_1k_input: float = Field(default=0.0)
    cost_per_1k_output: float = Field(default=0.0)
    is_local: bool = Field(default=False)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UpdateModelRequest(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model_type: Optional[ModelType] = None
    capabilities: Optional[list[ModelCapability]] = None
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    cost_per_1k_input: Optional[float] = None
    cost_per_1k_output: Optional[float] = None
    is_local: Optional[bool] = None
    metadata: Optional[dict[str, Any]] = None


class CompareRequest(BaseModel):
    model_ids: list[str] = Field(
        ...,
        description="List of model IDs to compare",
    )


# -- Endpoints --


@router.post(
    "/models",
    response_model=ModelEntry,
    summary="Register a new model",
    status_code=201,
)
async def register_model(
    body: RegisterModelRequest = Body(...),
) -> ModelEntry:
    registry = _get_registry()
    entry = ModelEntry(**body.model_dump())
    try:
        return registry.register(entry)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/models",
    response_model=list[ModelEntry],
    summary="List registered models",
)
async def list_models(
    type: Optional[ModelType] = Query(default=None, alias="type"),
    provider: Optional[str] = Query(default=None),
    capability: Optional[ModelCapability] = Query(default=None),
) -> list[ModelEntry]:
    registry = _get_registry()
    return registry.list_models(
        model_type=type,
        provider=provider,
        capability=capability,
    )


@router.get(
    "/models/{model_id}",
    response_model=ModelEntry,
    summary="Get a model by ID",
)
async def get_model(
    model_id: str = Path(...),
) -> ModelEntry:
    registry = _get_registry()
    entry = registry.get(model_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found",
        )
    return entry


@router.put(
    "/models/{model_id}",
    response_model=ModelEntry,
    summary="Update a model",
)
async def update_model(
    model_id: str = Path(...),
    body: UpdateModelRequest = Body(...),
) -> ModelEntry:
    registry = _get_registry()
    kwargs = {k: v for k, v in body.model_dump().items() if v is not None}
    if not kwargs:
        raise HTTPException(status_code=400, detail="No fields to update")
    entry = registry.update(model_id, **kwargs)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found",
        )
    return entry


@router.delete(
    "/models/{model_id}",
    summary="Delete a model",
)
async def delete_model(
    model_id: str = Path(...),
) -> dict[str, bool]:
    registry = _get_registry()
    deleted = registry.delete(model_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found",
        )
    return {"deleted": True}


@router.get(
    "/search",
    response_model=list[ModelEntry],
    summary="Search models by name",
)
async def search_models(
    query: str = Query(..., description="Search term"),
) -> list[ModelEntry]:
    registry = _get_registry()
    return registry.search(query)


@router.post(
    "/compare",
    response_model=ModelComparison,
    summary="Compare models side by side",
)
async def compare_models(
    body: CompareRequest = Body(...),
) -> ModelComparison:
    registry = _get_registry()
    return registry.compare(body.model_ids)


@router.get(
    "/recommend/{task}",
    response_model=list[ModelEntry],
    summary="Get recommended models for a task",
)
async def recommend_models(
    task: str = Path(..., description="Task type: chat, code, or vision"),
) -> list[ModelEntry]:
    registry = _get_registry()
    return registry.get_recommended(task)
