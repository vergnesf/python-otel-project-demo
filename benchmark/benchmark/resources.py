"""Resource tracking utilities for benchmarks."""

from __future__ import annotations

from dataclasses import dataclass

import psutil

try:
    import pynvml  # type: ignore

    _NVML_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    pynvml = None
    _NVML_AVAILABLE = False

_NVML_INITIALIZED = False


def init_nvml() -> bool:
    """Initialize NVML if available."""
    global _NVML_INITIALIZED
    if not _NVML_AVAILABLE or pynvml is None:
        return False
    if _NVML_INITIALIZED:
        return True
    try:
        pynvml.nvmlInit()
        _NVML_INITIALIZED = True
        return True
    except Exception:
        return False


def get_gpu_metrics() -> dict | None:
    """Return GPU utilization and memory usage for the first GPU."""
    if not init_nvml() or pynvml is None:
        return None
    try:
        device_count = pynvml.nvmlDeviceGetCount()
        if device_count == 0:
            return None
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        return {
            "gpu_util": float(util.gpu),
            "vram_used_mb": float(mem.used) / (1024 * 1024),
            "vram_total_mb": float(mem.total) / (1024 * 1024),
        }
    except Exception:
        return None


@dataclass
class ResourceTracker:
    """Track peak resource usage during a benchmark run."""

    process: psutil.Process
    cpu_max: float = 0.0
    ram_max_mb: float = 0.0
    gpu_util_max: float | None = None
    vram_max_mb: float | None = None

    def sample(self) -> None:
        """Sample current resource usage and update peaks."""
        cpu = self.process.cpu_percent(interval=None)
        ram_mb = self.process.memory_info().rss / (1024 * 1024)
        self.cpu_max = max(self.cpu_max, cpu)
        self.ram_max_mb = max(self.ram_max_mb, ram_mb)

        gpu_metrics = get_gpu_metrics()
        if gpu_metrics is not None:
            util = gpu_metrics.get("gpu_util")
            vram_mb = gpu_metrics.get("vram_used_mb")
            if util is not None:
                self.gpu_util_max = util if self.gpu_util_max is None else max(
                    self.gpu_util_max, util
                )
            if vram_mb is not None:
                self.vram_max_mb = vram_mb if self.vram_max_mb is None else max(
                    self.vram_max_mb, vram_mb
                )


def start_resource_tracker() -> ResourceTracker:
    """Create a resource tracker and prime CPU measurement."""
    process = psutil.Process()
    process.cpu_percent(interval=None)
    return ResourceTracker(process=process)


def format_optional_metric(value: float | None, unit: str) -> str:
    """Format optional metric value with unit."""
    if value is None:
        return "N/A"
    return f"{value:.2f}{unit}"
