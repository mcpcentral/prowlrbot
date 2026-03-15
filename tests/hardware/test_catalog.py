# -*- coding: utf-8 -*-
# tests/hardware/test_catalog.py
from prowlrbot.hardware.catalog import (
    MODEL_CATALOG,
    ModelEntry,
    QuantVariant,
    get_model,
)


def test_catalog_not_empty():
    assert len(MODEL_CATALOG) >= 20


def test_model_has_quant_variants():
    llama = get_model("llama-3.1-8b")
    assert llama is not None
    assert len(llama.quant_variants) >= 2
    q4 = next(v for v in llama.quant_variants if v.quant == "Q4_K_M")
    fp16 = next(v for v in llama.quant_variants if v.quant == "fp16")
    assert q4.ram_gb < fp16.ram_gb


def test_moe_model_has_active_params():
    """MoE models must use active_params_b for bandwidth calc, not params_b."""
    gpt_oss = get_model("gpt-oss-20b")
    assert gpt_oss is not None
    assert gpt_oss.is_moe is True
    assert gpt_oss.active_params_b is not None
    assert gpt_oss.active_params_b < gpt_oss.params_b


def test_model_capability_tags():
    qwen_coder = get_model("qwen2.5-coder-7b")
    assert "coding" in qwen_coder.capability_tags
