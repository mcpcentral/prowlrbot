# -*- coding: utf-8 -*-
"""
Model catalog with per-quantization memory costs and MoE support.

This is the core data layer for the hardware advisor. Unlike canirun.ai,
we track quantization-specific RAM requirements and MoE active-parameter counts
so bandwidth calculations use the correct (active) parameter count.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class QuantVariant:
    quant: str  # "Q4_K_M" | "Q5_K_M" | "Q8_0" | "fp16"
    ram_gb: float  # minimum RAM/VRAM needed for weights
    kv_cache_gb: float  # additional for 8K context KV cache
    tok_per_sec_per_100gbps: float  # tok/s = this * bandwidth_gbps / 100


@dataclass
class ModelEntry:
    id: str
    name: str
    family: str
    params_b: float
    context_k: int
    quant_variants: list[QuantVariant]
    capability_tags: list[str] = field(default_factory=list)
    is_moe: bool = False
    active_params_b: Optional[float] = None  # MoE only
    added_months_ago: int = 0
    hf_repo: Optional[str] = None
    ollama_tag: Optional[str] = None


def _q(quant: str, ram_gb: float, kv_gb: float, coeff: float) -> QuantVariant:
    """Convenience constructor for QuantVariant."""
    return QuantVariant(
        quant=quant,
        ram_gb=ram_gb,
        kv_cache_gb=kv_gb,
        tok_per_sec_per_100gbps=coeff,
    )


MODEL_CATALOG: list[ModelEntry] = [
    # ── Sub-2B ─────────────────────────────────────────────────────────────
    ModelEntry(
        id="qwen3.5-0.8b",
        name="Qwen 3.5 0.8B",
        family="qwen",
        params_b=0.8,
        context_k=32,
        quant_variants=[
            _q("Q4_K_M", 0.5, 0.2, 84.0),
            _q("Q8_0", 0.8, 0.2, 50.0),
            _q("fp16", 1.6, 0.2, 25.0),
        ],
        capability_tags=["general", "fast"],
        added_months_ago=2,
        ollama_tag="qwen3.5:0.8b",
    ),
    ModelEntry(
        id="llama-3.2-1b",
        name="Llama 3.2 1B",
        family="llama",
        params_b=1.0,
        context_k=128,
        quant_variants=[
            _q("Q4_K_M", 0.5, 0.3, 84.0),
            _q("Q8_0", 1.0, 0.3, 50.0),
            _q("fp16", 2.0, 0.3, 25.0),
        ],
        capability_tags=["general", "fast"],
        added_months_ago=6,
        hf_repo="meta-llama/Llama-3.2-1B",
        ollama_tag="llama3.2:1b",
    ),
    # ── 3-4B ───────────────────────────────────────────────────────────────
    ModelEntry(
        id="llama-3.2-3b",
        name="Llama 3.2 3B",
        family="llama",
        params_b=3.0,
        context_k=128,
        quant_variants=[
            _q("Q4_K_M", 1.5, 0.5, 28.0),
            _q("Q8_0", 3.0, 0.5, 14.0),
            _q("fp16", 6.0, 0.5, 7.0),
        ],
        capability_tags=["general"],
        added_months_ago=6,
        hf_repo="meta-llama/Llama-3.2-3B",
        ollama_tag="llama3.2:3b",
    ),
    ModelEntry(
        id="qwen3-4b",
        name="Qwen 3 4B",
        family="qwen",
        params_b=4.0,
        context_k=32,
        quant_variants=[
            _q("Q4_K_M", 2.0, 0.6, 28.0),
            _q("Q8_0", 4.0, 0.6, 14.0),
            _q("fp16", 8.0, 0.6, 7.0),
        ],
        capability_tags=["general", "reasoning"],
        added_months_ago=1,
        ollama_tag="qwen3:4b",
    ),
    ModelEntry(
        id="gemma-3-4b",
        name="Gemma 3 4B",
        family="gemma",
        params_b=4.0,
        context_k=128,
        quant_variants=[
            _q("Q4_K_M", 2.0, 0.6, 28.0),
            _q("Q8_0", 4.0, 0.6, 14.0),
            _q("fp16", 8.0, 0.6, 7.0),
        ],
        capability_tags=["general", "multimodal"],
        added_months_ago=2,
        hf_repo="google/gemma-3-4b",
        ollama_tag="gemma3:4b",
    ),
    # ── 7-9B ───────────────────────────────────────────────────────────────
    ModelEntry(
        id="llama-3.1-8b",
        name="Llama 3.1 8B",
        family="llama",
        params_b=8.0,
        context_k=128,
        quant_variants=[
            _q("Q4_K_M", 4.1, 1.0, 12.0),
            _q("Q5_K_M", 5.3, 1.0, 9.5),
            _q("Q8_0", 8.5, 1.0, 6.0),
            _q("fp16", 16.0, 1.0, 3.0),
        ],
        capability_tags=["general", "coding"],
        added_months_ago=8,
        hf_repo="meta-llama/Meta-Llama-3.1-8B",
        ollama_tag="llama3.1:8b",
    ),
    ModelEntry(
        id="qwen2.5-7b",
        name="Qwen 2.5 7B",
        family="qwen",
        params_b=7.0,
        context_k=128,
        quant_variants=[
            _q("Q4_K_M", 3.6, 1.0, 12.0),
            _q("Q8_0", 7.2, 1.0, 6.0),
            _q("fp16", 14.5, 1.0, 3.0),
        ],
        capability_tags=["general", "coding"],
        added_months_ago=5,
        hf_repo="Qwen/Qwen2.5-7B-Instruct",
        ollama_tag="qwen2.5:7b",
    ),
    ModelEntry(
        id="qwen2.5-coder-7b",
        name="Qwen 2.5 Coder 7B",
        family="qwen",
        params_b=7.0,
        context_k=128,
        quant_variants=[
            _q("Q4_K_M", 3.6, 1.0, 12.0),
            _q("Q8_0", 7.2, 1.0, 6.0),
            _q("fp16", 14.5, 1.0, 3.0),
        ],
        capability_tags=["coding"],
        added_months_ago=5,
        hf_repo="Qwen/Qwen2.5-Coder-7B-Instruct",
        ollama_tag="qwen2.5-coder:7b",
    ),
    ModelEntry(
        id="mistral-7b",
        name="Mistral 7B v0.3",
        family="mistral",
        params_b=7.0,
        context_k=32,
        quant_variants=[
            _q("Q4_K_M", 3.6, 1.0, 12.0),
            _q("Q8_0", 7.2, 1.0, 6.0),
            _q("fp16", 14.5, 1.0, 3.0),
        ],
        capability_tags=["general"],
        added_months_ago=12,
        hf_repo="mistralai/Mistral-7B-Instruct-v0.3",
        ollama_tag="mistral:7b",
    ),
    ModelEntry(
        id="qwen3-8b",
        name="Qwen 3 8B",
        family="qwen",
        params_b=8.0,
        context_k=32,
        quant_variants=[
            _q("Q4_K_M", 4.1, 1.0, 11.0),
            _q("Q8_0", 8.5, 1.0, 5.5),
            _q("fp16", 16.0, 1.0, 2.8),
        ],
        capability_tags=["general", "reasoning"],
        added_months_ago=1,
        ollama_tag="qwen3:8b",
    ),
    ModelEntry(
        id="deepseek-r1-7b",
        name="DeepSeek R1 Distill 7B",
        family="deepseek",
        params_b=7.0,
        context_k=128,
        quant_variants=[
            _q("Q4_K_M", 3.6, 1.0, 12.0),
            _q("Q8_0", 7.2, 1.0, 6.0),
            _q("fp16", 14.5, 1.0, 3.0),
        ],
        capability_tags=["reasoning"],
        added_months_ago=3,
        hf_repo="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        ollama_tag="deepseek-r1:7b",
    ),
    # ── 13-14B ─────────────────────────────────────────────────────────────
    ModelEntry(
        id="phi-4-14b",
        name="Phi-4 14B",
        family="phi",
        params_b=14.0,
        context_k=16,
        quant_variants=[
            _q("Q4_K_M", 7.2, 1.5, 6.0),
            _q("Q8_0", 14.5, 1.5, 3.0),
            _q("fp16", 28.0, 1.5, 1.5),
        ],
        capability_tags=["reasoning", "general"],
        added_months_ago=4,
        hf_repo="microsoft/phi-4",
        ollama_tag="phi4:14b",
    ),
    ModelEntry(
        id="qwen2.5-14b",
        name="Qwen 2.5 14B",
        family="qwen",
        params_b=14.0,
        context_k=128,
        quant_variants=[
            _q("Q4_K_M", 7.2, 1.5, 6.0),
            _q("Q8_0", 14.5, 1.5, 3.0),
            _q("fp16", 28.0, 1.5, 1.5),
        ],
        capability_tags=["general", "coding"],
        added_months_ago=5,
        hf_repo="Qwen/Qwen2.5-14B-Instruct",
        ollama_tag="qwen2.5:14b",
    ),
    ModelEntry(
        id="gemma-3-12b",
        name="Gemma 3 12B",
        family="gemma",
        params_b=12.0,
        context_k=128,
        quant_variants=[
            _q("Q4_K_M", 6.2, 1.4, 6.5),
            _q("Q8_0", 12.5, 1.4, 3.2),
            _q("fp16", 24.0, 1.4, 1.6),
        ],
        capability_tags=["general", "multimodal"],
        added_months_ago=2,
        hf_repo="google/gemma-3-12b",
        ollama_tag="gemma3:12b",
    ),
    ModelEntry(
        id="deepseek-r1-14b",
        name="DeepSeek R1 Distill 14B",
        family="deepseek",
        params_b=14.0,
        context_k=128,
        quant_variants=[
            _q("Q4_K_M", 7.2, 1.5, 6.0),
            _q("Q8_0", 14.5, 1.5, 3.0),
            _q("fp16", 28.0, 1.5, 1.5),
        ],
        capability_tags=["reasoning"],
        added_months_ago=3,
        hf_repo="deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
        ollama_tag="deepseek-r1:14b",
    ),
    # ── 20B MoE ────────────────────────────────────────────────────────────
    ModelEntry(
        id="gpt-oss-20b",
        name="GPT-OSS 20B",
        family="gpt-oss",
        params_b=20.0,
        context_k=128,
        quant_variants=[
            _q("Q4_K_M", 10.8, 2.0, 32.0),
            _q("Q8_0", 20.0, 2.0, 16.0),
            _q("fp16", 40.0, 2.0, 8.0),
        ],
        capability_tags=["general", "reasoning"],
        is_moe=True,
        active_params_b=3.5,
        added_months_ago=1,
    ),
    # ── 24-32B ─────────────────────────────────────────────────────────────
    ModelEntry(
        id="mistral-small-24b",
        name="Mistral Small 3.1 24B",
        family="mistral",
        params_b=24.0,
        context_k=128,
        quant_variants=[
            _q("Q4_K_M", 12.3, 2.5, 3.5),
            _q("Q8_0", 24.0, 2.5, 1.8),
            _q("fp16", 48.0, 2.5, 0.9),
        ],
        capability_tags=["general", "reasoning"],
        added_months_ago=3,
        hf_repo="mistralai/Mistral-Small-3.1-24B-Instruct-2503",
        ollama_tag="mistral-small3.1:24b",
    ),
    ModelEntry(
        id="qwen2.5-coder-32b",
        name="Qwen 2.5 Coder 32B",
        family="qwen",
        params_b=32.0,
        context_k=128,
        quant_variants=[
            _q("Q4_K_M", 16.4, 3.0, 2.8),
            _q("Q8_0", 32.0, 3.0, 1.4),
            _q("fp16", 64.0, 3.0, 0.7),
        ],
        capability_tags=["coding"],
        added_months_ago=5,
        hf_repo="Qwen/Qwen2.5-Coder-32B-Instruct",
        ollama_tag="qwen2.5-coder:32b",
    ),
    ModelEntry(
        id="deepseek-r1-32b",
        name="DeepSeek R1 Distill 32B",
        family="deepseek",
        params_b=32.0,
        context_k=128,
        quant_variants=[
            _q("Q4_K_M", 16.4, 3.0, 2.8),
            _q("Q8_0", 32.0, 3.0, 1.4),
            _q("fp16", 64.0, 3.0, 0.7),
        ],
        capability_tags=["reasoning"],
        added_months_ago=3,
        hf_repo="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        ollama_tag="deepseek-r1:32b",
    ),
    # ── 30B MoE ────────────────────────────────────────────────────────────
    ModelEntry(
        id="qwen3-30b-a3b",
        name="Qwen 3 30B-A3B",
        family="qwen",
        params_b=30.0,
        context_k=128,
        quant_variants=[
            _q("Q4_K_M", 15.4, 3.0, 38.0),
            _q("Q8_0", 30.0, 3.0, 19.0),
            _q("fp16", 60.0, 3.0, 9.5),
        ],
        capability_tags=["reasoning", "coding"],
        is_moe=True,
        active_params_b=3.0,
        added_months_ago=1,
        ollama_tag="qwen3:30b-a3b",
    ),
    # ── 70B ────────────────────────────────────────────────────────────────
    ModelEntry(
        id="llama-3.3-70b",
        name="Llama 3.3 70B",
        family="llama",
        params_b=70.0,
        context_k=128,
        quant_variants=[
            _q("Q4_K_M", 35.9, 6.0, 1.4),
            _q("Q8_0", 70.0, 6.0, 0.7),
            _q("fp16", 140.0, 6.0, 0.35),
        ],
        capability_tags=["general", "reasoning", "coding"],
        added_months_ago=4,
        hf_repo="meta-llama/Llama-3.3-70B-Instruct",
        ollama_tag="llama3.3:70b",
    ),
]

_INDEX: dict[str, ModelEntry] = {m.id: m for m in MODEL_CATALOG}


def get_model(model_id: str) -> Optional[ModelEntry]:
    """Look up a model by its catalog ID. Returns None if not found."""
    return _INDEX.get(model_id)
