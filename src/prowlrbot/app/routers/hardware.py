# -*- coding: utf-8 -*-
"""Hardware advisor API router.

Endpoints:
  GET /hardware              — detected hardware profile
  GET /hardware/model-grades — scored model list for this machine
  GET /hardware/reverse-lookup/{model_id} — min/ideal requirements for a model
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from prowlrbot.hardware.catalog import MODEL_CATALOG, get_model
from prowlrbot.hardware.detector import HardwareDetector
from prowlrbot.hardware.scorer import ModelScorer

router = APIRouter(prefix="/hardware", tags=["hardware"])
_detector = HardwareDetector()  # module-level singleton


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class HardwareProfileResponse(BaseModel):
    ram_gb: float
    cpu_cores: int
    cpu_arch: str
    platform: str
    gpu_name: Optional[str]
    gpu_vram_gb: Optional[float]
    gpu_vendor: str
    estimated_bandwidth_gbps: float
    is_apple_silicon: bool
    unified_memory: bool


class ModelGradeResponse(BaseModel):
    model_id: str
    name: str
    family: str
    params_b: float
    context_k: int
    grade: str
    score: int
    label: str
    best_quant: Optional[str]
    required_gb: float
    available_gb: float
    tok_per_sec: float
    memory_ratio: float
    cpu_offload_possible: bool
    capability_tags: List[str]
    is_moe: bool
    ollama_tag: Optional[str]


class ReverseLookupResponse(BaseModel):
    model_id: str
    name: str
    min_vram_gb: float
    ideal_vram_gb: float
    min_ram_gb: float
    recommended_setup: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=HardwareProfileResponse)
def get_hardware_profile() -> HardwareProfileResponse:
    """Return the detected hardware profile for this machine."""
    profile = _detector.detect()
    return HardwareProfileResponse(
        ram_gb=profile.ram_gb,
        cpu_cores=profile.cpu_cores,
        cpu_arch=profile.cpu_arch,
        platform=profile.platform,
        gpu_name=profile.gpu_name,
        gpu_vram_gb=profile.gpu_vram_gb,
        gpu_vendor=profile.gpu_vendor,
        estimated_bandwidth_gbps=profile.estimated_bandwidth_gbps,
        is_apple_silicon=profile.is_apple_silicon,
        unified_memory=profile.unified_memory,
    )


@router.get("/model-grades", response_model=List[ModelGradeResponse])
def get_model_grades(
    capability: Optional[str] = None,
    min_grade: Optional[str] = None,
) -> List[ModelGradeResponse]:
    """Return scored model grades for this machine's hardware.

    Query params:
    - capability: filter to models with this capability tag
    - min_grade:  if set, exclude models below this grade (e.g. "B" → returns S/A/B only)
    """
    profile = _detector.detect()
    scorer = ModelScorer(profile)
    scores = scorer.score_all()  # sorted by score desc

    # Build lookup of ModelEntry by id
    catalog_index = {m.id: m for m in MODEL_CATALOG}

    result: List[ModelGradeResponse] = []
    for ms in scores:
        # Capability filter
        model_entry = catalog_index.get(ms.model_id)
        if model_entry is None:
            continue

        if capability is not None and capability not in model_entry.capability_tags:
            continue

        # min_grade: exclude models below the requested grade threshold
        if min_grade is not None:
            _grade_order = ["S", "A", "B", "C", "D", "F"]
            threshold = min_grade.upper()
            if threshold in _grade_order:
                if _grade_order.index(ms.grade.value) > _grade_order.index(
                    threshold,
                ):
                    continue

        result.append(
            ModelGradeResponse(
                model_id=ms.model_id,
                name=model_entry.name,
                family=model_entry.family,
                params_b=model_entry.params_b,
                context_k=model_entry.context_k,
                grade=ms.grade.value,
                score=ms.score,
                label=ms.label,
                best_quant=ms.best_quant,
                required_gb=ms.required_gb,
                available_gb=ms.available_gb,
                tok_per_sec=ms.tok_per_sec,
                memory_ratio=ms.memory_ratio,
                cpu_offload_possible=ms.cpu_offload_possible,
                capability_tags=model_entry.capability_tags,
                is_moe=model_entry.is_moe,
                ollama_tag=model_entry.ollama_tag,
            ),
        )

    return result


@router.get("/reverse-lookup/{model_id}", response_model=ReverseLookupResponse)
def reverse_lookup(model_id: str) -> ReverseLookupResponse:
    """Return minimum and ideal hardware requirements for a specific model.

    Raises 404 if model_id is not found in the catalog.
    """
    model = get_model(model_id)
    if model is None:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found in catalog.",
        )

    variants = model.quant_variants

    # Find Q4_K_M variant → min_vram_gb
    q4_variant = next((v for v in variants if v.quant == "Q4_K_M"), None)
    min_vram_gb: float = (
        q4_variant.ram_gb if q4_variant else min(v.ram_gb for v in variants)
    )

    # Find Q8_0 variant → ideal_vram_gb (fallback: Q4 * 1.5)
    q8_variant = next((v for v in variants if v.quant == "Q8_0"), None)
    ideal_vram_gb: float = q8_variant.ram_gb if q8_variant else min_vram_gb * 1.5

    # min_ram_gb — smallest variant ram_gb / 0.60
    smallest_ram_gb = min(v.ram_gb for v in variants)
    min_ram_gb: float = round(smallest_ram_gb / 0.60, 1)

    # Build tags summary
    tags_str = ", ".join(model.capability_tags) if model.capability_tags else "general"

    recommended_setup = (
        f"For {model.name} ({tags_str}): minimum {min_vram_gb:.0f} GB VRAM (Q4_K_M), "
        f"ideal {ideal_vram_gb:.0f} GB (Q8_0). "
        f"CPU-only possible with {min_ram_gb:.0f} GB RAM (slow)."
    )

    return ReverseLookupResponse(
        model_id=model.id,
        name=model.name,
        min_vram_gb=min_vram_gb,
        ideal_vram_gb=ideal_vram_gb,
        min_ram_gb=min_ram_gb,
        recommended_setup=recommended_setup,
    )
