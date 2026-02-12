"""
Vast.ai PyWorker for Realstagram AI

Thin proxy that sits between the Vast serverless routing layer
and handler.py (port 18288). Handles authentication, queueing,
benchmarking, and metrics reporting.
"""

import random
import sys

from vastai import (
    Worker,
    WorkerConfig,
    HandlerConfig,
    LogActionConfig,
    BenchmarkConfig,
)

# =============================================================================
# Configuration
# =============================================================================

MODEL_SERVER_URL = "http://127.0.0.1"
MODEL_SERVER_PORT = 18288
MODEL_LOG_FILE = "/var/log/portal/comfyui.log"

# Log patterns for ComfyUI readiness detection
MODEL_LOAD_LOG_MSGS = [
    "To see the GUI go to:",
]

MODEL_ERROR_LOG_MSGS = [
    "RuntimeError:",
    "Traceback (most recent call last):",
    "CUDA out of memory",
    "CUDA error",
]

MODEL_INFO_LOG_MSGS = [
    "Downloading",
    "Loading model",
]

# =============================================================================
# Benchmark
# =============================================================================

# Benchmark payload - a minimal generation to measure GPU performance.
# Uses low steps for speed. The benchmark image URL should be a small
# test image uploaded to your R2 storage.
# If no benchmark image is available, the benchmark will fail gracefully
# and the worker will still join the pool.

def benchmark_generator() -> dict:
    """Generate a benchmark payload."""
    return {
        "gender": "women",
        "controlnet": False,
        "image_url": "https://storage.realstagram.ai/test/women_test.png",
        "width": 1152,
        "height": 1536,
        "steps": 8,
        "cfg": 2.35,
        "eta": 0.5,
        "denoise": 1.0,
        "seed": random.randint(0, 2**32 - 1),
        "user_prompt": "",
    }


# =============================================================================
# Worker Configuration
# =============================================================================

worker_config = WorkerConfig(
    model_server_url=MODEL_SERVER_URL,
    model_server_port=MODEL_SERVER_PORT,
    model_log_file=MODEL_LOG_FILE,

    handlers=[
        HandlerConfig(
            route="/generate",
            # ComfyUI processes one workflow at a time
            allow_parallel_requests=False,
            # Max time a request can wait in queue before 429
            max_queue_time=120.0,
            # Constant workload per image generation
            workload_calculator=lambda payload: 100.0,
            # Benchmark config
            benchmark_config=BenchmarkConfig(
                generator=benchmark_generator,
                runs=1,
                concurrency=1,
            ),
        ),
    ],

    log_action_config=LogActionConfig(
        on_load=MODEL_LOAD_LOG_MSGS,
        on_error=MODEL_ERROR_LOG_MSGS,
        on_info=MODEL_INFO_LOG_MSGS,
    ),
)

# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    Worker(worker_config).run()
