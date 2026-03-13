# tests/hardware/test_detector.py
"""Tests for HardwareDetector — platform-agnostic unit tests with mocks."""
import pytest
from unittest.mock import patch, MagicMock
from prowlrbot.hardware.detector import HardwareDetector, HardwareProfile


def test_hardware_profile_fields():
    profile = HardwareProfile(
        ram_gb=16.0,
        cpu_cores=8,
        cpu_arch="x86_64",
        platform="linux",
        gpu_name="NVIDIA RTX 3060",
        gpu_vram_gb=12.0,
        gpu_vendor="nvidia",
        estimated_bandwidth_gbps=360.0,
        is_apple_silicon=False,
        unified_memory=False,
    )
    assert profile.ram_gb == 16.0
    assert profile.gpu_vram_gb == 12.0
    assert not profile.unified_memory


def test_detector_returns_profile():
    detector = HardwareDetector()
    profile = detector.detect()
    assert isinstance(profile, HardwareProfile)
    assert profile.ram_gb > 0
    assert profile.cpu_cores > 0


def test_detector_handles_missing_nvidia_smi(monkeypatch):
    """nvidia-smi absent → gpu_vram_gb is None, gpu_vendor is 'unknown'."""
    def _raise(*a, **kw):
        raise FileNotFoundError("nvidia-smi not found")
    monkeypatch.setattr("subprocess.run", _raise)
    detector = HardwareDetector()
    profile = detector._detect_nvidia()
    assert profile is None


def test_detector_apple_silicon(monkeypatch):
    """platform=darwin + arm64 + sysctl → is_apple_silicon=True."""
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr("platform.machine", lambda: "arm64")
    detector = HardwareDetector()
    assert detector._is_apple_silicon()
