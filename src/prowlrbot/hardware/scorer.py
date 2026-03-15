# -*- coding: utf-8 -*-
"""ModelScorer — grades every catalog model S/A/B/C/D/F for a given HardwareProfile.

Scoring is quant-aware: the scorer picks the highest-quality quantization variant
that fits in available memory, then estimates tok/s from memory bandwidth.
MoE models use active_params_b for bandwidth calculations.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from prowlrbot.hardware.catalog import MODEL_CATALOG, ModelEntry, QuantVariant
from prowlrbot.hardware.detector import HardwareProfile


class Grade(str, Enum):
    S = "S"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


_GRADE_LABELS: dict[Grade, str] = {
    Grade.S: "Runs great",
    Grade.A: "Runs well",
    Grade.B: "Decent",
    Grade.C: "Tight fit",
    Grade.D: "Barely runs",
    Grade.F: "Too heavy",
}


@dataclass
class ModelScore:
    model_id: str
    grade: Grade
    score: int  # 0-100
    best_quant: Optional[str]  # e.g. "Q4_K_M", None if F
    required_gb: float
    available_gb: float
    tok_per_sec: float  # 0 if F
    memory_ratio: float  # required / available
    cpu_offload_possible: bool
    label: str  # human-readable grade description


def _grade_from_score(score: int) -> Grade:
    """Map a numeric score (0-100) to a letter grade."""
    if score >= 90:
        return Grade.S
    if score >= 75:
        return Grade.A
    if score >= 60:
        return Grade.B
    if score >= 40:
        return Grade.C
    if score >= 20:
        return Grade.D
    return Grade.F


class ModelScorer:
    """Scores catalog models against a hardware profile."""

    def __init__(self, profile: HardwareProfile) -> None:
        self.profile = profile

    def available_memory_gb(self) -> float:
        """Return effective available memory in GB for model weights."""
        if self.profile.unified_memory:
            # Apple Silicon: unified memory, use 80% of RAM
            return self.profile.ram_gb * 0.80
        if self.profile.gpu_vram_gb is not None:
            # Discrete GPU: use 95% of VRAM
            return self.profile.gpu_vram_gb * 0.95
        # CPU-only inference
        return self.profile.ram_gb * 0.60

    def _estimate_tok_per_sec(
        self,
        model: ModelEntry,
        variant: QuantVariant,
        cpu_offload: bool = False,
    ) -> float:
        """Estimate tokens per second for a given variant on this hardware."""
        bw = self.profile.estimated_bandwidth_gbps
        if model.is_moe and model.active_params_b:
            bw = bw * (model.active_params_b / model.params_b)
        if self.profile.gpu_vram_gb is None:
            bw = max(bw, 20.0)
        tok_per_sec = variant.tok_per_sec_per_100gbps * bw / 100.0
        if cpu_offload:
            tok_per_sec *= 0.25
        return tok_per_sec

    def _raw_score(self, memory_ratio: float, tok_per_sec: float) -> int:
        """Compute raw 0-100 score from memory ratio and tok/s."""
        if memory_ratio < 0.15:
            mem_score = 100
        elif memory_ratio > 1.0:
            mem_score = 0
        else:
            mem_score = int(100 - (memory_ratio - 0.15) / 0.85 * 80)

        if tok_per_sec >= 50:
            tok_score = 100
        elif tok_per_sec >= 20:
            tok_score = 80
        elif tok_per_sec >= 10:
            tok_score = 60
        elif tok_per_sec >= 5:
            tok_score = 40
        elif tok_per_sec >= 2:
            tok_score = 20
        else:
            tok_score = 0

        return int(mem_score * 0.6 + tok_score * 0.4)

    def _pick_best_variant(
        self,
        variants: list[QuantVariant],
        model: ModelEntry,
        available: float,
    ) -> QuantVariant:
        """From a list of fitting variants, return the one with the best score."""
        best: Optional[QuantVariant] = None
        best_score = -1
        for variant in variants:
            tok = self._estimate_tok_per_sec(model, variant)
            ratio = variant.ram_gb / max(available, 0.1)
            s = self._raw_score(ratio, tok)
            if s > best_score:
                best_score = s
                best = variant
        return best  # type: ignore[return-value]  # variants is non-empty

    def score_model(self, model: ModelEntry) -> ModelScore:
        """Score a single model against this scorer's hardware profile."""
        available = self.available_memory_gb()

        # Sort variants by ram_gb descending (highest quality first)
        sorted_desc = sorted(
            model.quant_variants,
            key=lambda v: v.ram_gb,
            reverse=True,
        )

        # Step 1: find best variant that fits in available GPU/unified memory.
        # Among all fitting variants, pick the one that yields the best score
        # (highest tok/s weighted against memory efficiency).
        fitting_variants = [v for v in sorted_desc if v.ram_gb <= available]

        best_variant: Optional[QuantVariant] = None
        cpu_offload_possible = False

        if fitting_variants:
            best_variant = self._pick_best_variant(
                fitting_variants,
                model,
                available,
            )

        # Step 2: if nothing fits in VRAM/unified, try CPU offload
        if best_variant is None:
            cpu_ram_budget = self.profile.ram_gb * 0.70
            sorted_asc = sorted(model.quant_variants, key=lambda v: v.ram_gb)
            for variant in sorted_asc:
                if variant.ram_gb <= cpu_ram_budget:
                    best_variant = variant
                    cpu_offload_possible = True
                    break

        # Step 3: if still nothing fits, return F
        if best_variant is None:
            largest_variant = sorted_desc[0]  # largest ram_gb
            return ModelScore(
                model_id=model.id,
                grade=Grade.F,
                score=0,
                best_quant=None,
                required_gb=largest_variant.ram_gb,
                available_gb=available,
                tok_per_sec=0.0,
                memory_ratio=largest_variant.ram_gb / max(available, 0.1),
                cpu_offload_possible=False,
                label=_GRADE_LABELS[Grade.F],
            )

        # Step 4: compute memory ratio
        memory_ratio = best_variant.ram_gb / max(available, 0.1)

        # Step 5: estimate tok/s
        tok_per_sec = self._estimate_tok_per_sec(
            model,
            best_variant,
            cpu_offload_possible,
        )

        # Step 6: score formula
        raw_score = self._raw_score(memory_ratio, tok_per_sec)
        if cpu_offload_possible:
            raw_score = min(raw_score, 35)

        grade = _grade_from_score(raw_score)

        return ModelScore(
            model_id=model.id,
            grade=grade,
            score=raw_score,
            best_quant=best_variant.quant,
            required_gb=best_variant.ram_gb,
            available_gb=available,
            tok_per_sec=round(tok_per_sec, 2),
            memory_ratio=round(memory_ratio, 4),
            cpu_offload_possible=cpu_offload_possible,
            label=_GRADE_LABELS[grade],
        )

    def score_all(self) -> list[ModelScore]:
        """Score every model in MODEL_CATALOG, sorted by score descending."""
        scores = [self.score_model(model) for model in MODEL_CATALOG]
        return sorted(scores, key=lambda s: s.score, reverse=True)
