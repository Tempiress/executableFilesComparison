"""
System resource monitoring (CPU / GPU).

Provides:
  - get_gpu_memory()         — free GPU memory in MB
  - get_gpu_utilization()    — (gpu%, mem%) or (0, 0)
  - wait_for_gpu_memory()    — block until sufficient GPU memory available
  - start_resource_logger()  — background thread logging CPU/GPU usage
  - benchmark_step()         — decorator to time a function call
"""

import datetime
import os
import threading
import time
from typing import Tuple

import psutil
import torch

try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False


def get_gpu_memory() -> int:
    """Free GPU memory in MB, or 0 if unavailable."""
    if not NVML_AVAILABLE:
        return 0
    try:
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        return info.free // 1024 // 1024
    except Exception:
        return 0


def get_gpu_utilization() -> Tuple[int, int]:
    """Returns (gpu_percent, memory_percent) or (0, 0)."""
    if not NVML_AVAILABLE:
        return 0, 0
    try:
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        return util.gpu, util.memory
    except Exception:
        return 0, 0


def wait_for_gpu_memory(timeout_seconds: int = 60, min_free_mb: int = 2048) -> bool:
    """Block until GPU has at least *min_free_mb* free, or timeout."""
    start = time.time()
    while time.time() - start < timeout_seconds:
        free_mb = get_gpu_memory()
        if free_mb >= min_free_mb:
            return True
        time.sleep(1)
    return False


def start_resource_logger(log_file: str, interval_seconds: int = 5) -> threading.Thread:
    """Start a daemon thread that periodically logs CPU/GPU stats.

    Returns the running thread.
    """

    def _logger():
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "a") as f:
            f.write("timestamp,cpu_percent,gpu_util,free_gpu_mb,datetime\n")
            while True:
                cpu_pct = psutil.cpu_percent(interval=interval_seconds, percpu=False)
                gpu_util, gpu_mem_util = get_gpu_utilization()
                free_mb = get_gpu_memory()
                now = datetime.datetime.now().isoformat()
                f.write(f"{time.time()},{cpu_pct},{gpu_util},{free_mb},{now}\n")
                f.flush()

    thread = threading.Thread(target=_logger, daemon=True)
    return thread


def benchmark_step(step_name: str, func, *args, **kwargs):
    """Time a function call and print the duration."""
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    print(f"[BENCHMARK] {step_name}: {elapsed:.2f}s")
    return result, elapsed
