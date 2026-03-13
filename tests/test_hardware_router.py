# -*- coding: utf-8 -*-
"""Tests for GET /api/hardware and GET /api/hardware/model-grades."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from prowlrbot.app.routers.hardware import router as hardware_router


@pytest.fixture
def test_client():
    """Minimal FastAPI app wired with the hardware router."""
    app = FastAPI()
    app.include_router(hardware_router)
    return TestClient(app)


def test_hardware_endpoint_returns_profile(test_client):
    resp = test_client.get("/hardware")
    assert resp.status_code == 200
    data = resp.json()
    assert "ram_gb" in data
    assert data["ram_gb"] > 0
    assert "platform" in data
    assert "cpu_cores" in data
    assert "gpu_vendor" in data


def test_model_grades_endpoint(test_client):
    resp = test_client.get("/hardware/model-grades")
    assert resp.status_code == 200
    grades = resp.json()
    assert isinstance(grades, list)
    assert len(grades) >= 10
    first = grades[0]
    assert "model_id" in first
    assert "grade" in first
    assert "tok_per_sec" in first
    assert "best_quant" in first
    assert "label" in first


def test_model_grades_sorted_by_score(test_client):
    resp = test_client.get("/hardware/model-grades")
    grades = resp.json()
    scores = [g["score"] for g in grades]
    assert scores == sorted(scores, reverse=True)


def test_reverse_lookup_known_model(test_client):
    resp = test_client.get("/hardware/reverse-lookup/llama-3.1-8b")
    assert resp.status_code == 200
    data = resp.json()
    assert "min_vram_gb" in data
    assert "recommended_setup" in data
    assert data["min_vram_gb"] > 0


def test_reverse_lookup_unknown_model(test_client):
    resp = test_client.get("/hardware/reverse-lookup/nonexistent-model-xyz")
    assert resp.status_code == 404
