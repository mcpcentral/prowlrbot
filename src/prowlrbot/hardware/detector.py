"""HardwareDetector — detects machine specs via psutil + nvidia-smi/rocm-smi/sysctl.

Provides exact OS-level values rather than unreliable browser WebGPU detection.
"""
from __future__ import annotations

import json
import platform
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import psutil


_BANDWIDTH_TABLE: dict[str, float] = {
    "rtx 4090": 1008.0,
    "rtx 4080": 736.0,
    "rtx 4070 ti": 504.0,
    "rtx 4070": 504.0,
    "rtx 4060": 272.0,
    "rtx 3090": 936.0,
    "rtx 3080": 760.0,
    "rtx 3070": 448.0,
    "rtx 3060": 360.0,
    "rx 7900 xtx": 960.0,
    "rx 7900 xt": 800.0,
    "rx 6900 xt": 512.0,
    "rx 6800 xt": 512.0,
    "m4 ultra": 800.0,
    "m4 max": 546.0,
    "m4 pro": 273.0,
    "m4": 120.0,
    "m3 ultra": 800.0,
    "m3 max": 400.0,
    "m3 pro": 153.6,
    "m3": 100.0,
    "m2 ultra": 800.0,
    "m2 max": 400.0,
    "m2 pro": 200.0,
    "m2": 100.0,
    "m1 ultra": 800.0,
    "m1 max": 400.0,
    "m1 pro": 200.0,
    "m1": 68.25,
}


@dataclass
class HardwareProfile:
    """Detected hardware profile for a machine."""

    ram_gb: float
    cpu_cores: int
    cpu_arch: str
    platform: str
    gpu_name: Optional[str] = None
    gpu_vram_gb: Optional[float] = None
    gpu_vendor: str = "unknown"
    estimated_bandwidth_gbps: float = 0.0
    is_apple_silicon: bool = False
    unified_memory: bool = False


class HardwareDetector:
    """Detects machine hardware specs using OS-level tools."""

    def detect(self) -> HardwareProfile:
        """Main entry point — returns a fully populated HardwareProfile."""
        ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 1)
        cpu_cores = psutil.cpu_count(logical=False) or psutil.cpu_count() or 1
        cpu_arch = platform.machine()
        plat = platform.system().lower()

        is_apple = self._is_apple_silicon()
        unified_memory = is_apple

        gpu_info: Optional[dict] = None
        if is_apple:
            gpu_info = self._detect_apple()
        else:
            for detector in (self._detect_nvidia, self._detect_amd, self._detect_intel):
                gpu_info = detector()
                if gpu_info is not None:
                    break

        gpu_name: Optional[str] = None
        gpu_vram_gb: Optional[float] = None
        gpu_vendor: str = "unknown"
        bandwidth: float = 0.0

        if gpu_info is not None:
            gpu_name = gpu_info.get("name")
            gpu_vram_gb = gpu_info.get("vram_gb")
            gpu_vendor = gpu_info.get("vendor", "unknown")
            if gpu_name:
                bandwidth = self._estimate_bandwidth(gpu_name)
            if bandwidth == 0.0 and is_apple:
                bandwidth = self._apple_bandwidth(ram_gb)

        return HardwareProfile(
            ram_gb=ram_gb,
            cpu_cores=cpu_cores,
            cpu_arch=cpu_arch,
            platform=plat,
            gpu_name=gpu_name,
            gpu_vram_gb=gpu_vram_gb,
            gpu_vendor=gpu_vendor,
            estimated_bandwidth_gbps=bandwidth,
            is_apple_silicon=is_apple,
            unified_memory=unified_memory,
        )

    def _is_apple_silicon(self) -> bool:
        """Return True when running on Apple Silicon (Darwin + arm64)."""
        return platform.system() == "Darwin" and platform.machine() == "arm64"

    def _detect_nvidia(self) -> Optional[dict]:
        """Query nvidia-smi for GPU name and VRAM.

        Returns dict with keys name, vram_gb, vendor, or None on any error.
        """
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            line = result.stdout.strip().splitlines()[0]
            name, vram_mib = line.split(",", 1)
            name = name.strip()
            vram_gb = round(float(vram_mib.strip()) / 1024, 2)
            return {"name": name, "vram_gb": vram_gb, "vendor": "nvidia"}
        except Exception:
            return None

    def _detect_amd(self) -> Optional[dict]:
        """Query rocm-smi for AMD GPU info.

        Returns dict with keys name, vram_gb, vendor, or None on any error.
        """
        try:
            result = subprocess.run(
                ["rocm-smi", "--showproductname", "--showmeminfo", "vram", "--json"],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
            # rocm-smi JSON shape varies by version; handle common layouts
            # Typical key: "card0" with sub-keys
            card_key = next(iter(data))
            card = data[card_key]
            name = card.get("Card series") or card.get("Card model") or card_key
            vram_bytes_str = (
                card.get("VRAM Total Memory (B)")
                or card.get("vram_total_memory")
                or "0"
            )
            vram_gb = round(int(vram_bytes_str) / (1024 ** 3), 2)
            return {"name": name, "vram_gb": vram_gb, "vendor": "amd"}
        except Exception:
            return None

    def _detect_intel(self) -> Optional[dict]:
        """Detect Intel GPU via sysfs DRM entries.

        Returns dict with keys name, vram_gb, vendor, or None on any error.
        """
        try:
            drm_path = Path("/sys/class/drm")
            for card_dir in sorted(drm_path.glob("card*/device")):
                vendor_file = card_dir / "vendor"
                if not vendor_file.exists():
                    continue
                vendor_id = vendor_file.read_text().strip().lower()
                if vendor_id != "0x8086":
                    continue
                # Found Intel GPU
                vram_gb: Optional[float] = None
                vram_file = card_dir / "mem_info_vram_total"
                if vram_file.exists():
                    vram_bytes = int(vram_file.read_text().strip())
                    vram_gb = round(vram_bytes / (1024 ** 3), 2)
                name_file = card_dir / "device_name"
                name = name_file.read_text().strip() if name_file.exists() else "Intel GPU"
                return {"name": name, "vram_gb": vram_gb, "vendor": "intel"}
            return None
        except Exception:
            return None

    def _detect_apple(self) -> Optional[dict]:
        """Query system_profiler for Apple GPU info.

        Uses unified memory (psutil RAM) as vram_gb since Apple Silicon has no
        discrete VRAM.  Returns dict or None on any error.
        """
        try:
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType", "-json"],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
            displays = data.get("SPDisplaysDataType", [])
            if not displays:
                return None
            gpu_entry = displays[0]
            name = gpu_entry.get("sppci_model") or gpu_entry.get("_name") or "Apple GPU"
            # Unified memory — use total system RAM
            ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 1)
            return {"name": name, "vram_gb": ram_gb, "vendor": "apple"}
        except Exception:
            return None

    def _estimate_bandwidth(self, gpu_name: str) -> float:
        """Return estimated memory bandwidth in GB/s for a GPU name.

        Uses substring matching against _BANDWIDTH_TABLE (longest key wins to
        avoid partial matches like "m1" inside "m1 pro").
        """
        lower = gpu_name.lower()
        # Sort by key length descending so longer/more specific keys match first
        for key in sorted(_BANDWIDTH_TABLE, key=len, reverse=True):
            if key in lower:
                return _BANDWIDTH_TABLE[key]
        return 0.0

    def _apple_bandwidth(self, ram_gb: float) -> float:
        """Estimate Apple Silicon memory bandwidth based on RAM tier."""
        if ram_gb >= 192:
            return 800.0
        if ram_gb >= 96:
            return 546.0
        if ram_gb >= 64:
            return 400.0
        if ram_gb >= 36:
            return 273.0
        if ram_gb >= 24:
            return 200.0
        return 100.0
