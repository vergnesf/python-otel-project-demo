#!/usr/bin/env python3
"""
Benchmark tests for different AI models.
"""

import asyncio
from pathlib import Path
import statistics
import time

import psutil
import pytest
import yaml

from .test_orchestrator_integration import (
    run_agent_routing,
    run_response_validation,
    run_complete_workflow,
    check_orchestrator_available,
    list_available_models,
    Colors,
    BASE_URL,
    TIMEOUT,
)
from common_ai import get_model_params, unload_ollama_model

MODELS = [
    "mistral:7b",
    "llama3.2:3b",
    "qwen3:0.6b",
    "granite4:3b",
    "mistral-nemo:12b",
    "qwen2.5:7b",
    "phi4:14b",
]


def load_model_configs():
    """Load model configurations from config/ai/model-params.yml"""
    config_file = Path(__file__).parent.parent.parent / "config" / "ai" / "model-params.yml"
    try:
        with open(config_file, "r") as f:
            config_data = yaml.safe_load(f)

        model_configs = {}
        models_section = config_data.get("models", {})

        for model_name, model_data in models_section.items():
            context_size = model_data.get("context_size", "N/A")
            model_configs[model_name] = {"context_size": context_size}

        return model_configs
    except Exception as e:
        print(
            f"{Colors.YELLOW}⚠️  Could not load model configs from config/ai/model-params.yml: {e}{Colors.END}"
        )
        return {}


MODEL_CONFIGS = load_model_configs()

pytestmark = pytest.mark.integration

_AVAILABLE_MODELS: list[str] | None = None


async def _get_available_models() -> list[str]:
    """Return and cache available models from Ollama."""
    global _AVAILABLE_MODELS
    if _AVAILABLE_MODELS is None:
        _AVAILABLE_MODELS = await list_available_models()
    return _AVAILABLE_MODELS


def _select_models(available_models: list[str]) -> list[str]:
    """Select benchmark models that are actually available."""
    selected = [model for model in MODELS if model in available_models]
    return selected or available_models[:1]


def _memory_usage_mb() -> float:
    """Return current process memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / (1024 * 1024)


async def _time_stage(label: str, coro: asyncio.Future) -> float:
    """Measure duration for an awaited stage."""
    start = time.perf_counter()
    await coro
    duration = time.perf_counter() - start
    print(f"  {Colors.BLUE}{label}{Colors.END}: {duration:.2f}s")
    return duration


@pytest.mark.asyncio
@pytest.mark.parametrize("model", MODELS)
async def test_benchmark_model_workflow(model: str) -> None:
    """Benchmark routing, validation, and workflow for each model."""
    await check_orchestrator_available()
    available_models = await _get_available_models()
    selected_models = _select_models(available_models)

    if model not in selected_models:
        pytest.skip(f"Model {model} not available in Ollama.")

    model_params = get_model_params(model)
    context_size = MODEL_CONFIGS.get(model, {}).get("context_size", "N/A")

    print(f"\n{Colors.BOLD}Benchmarking model: {model}{Colors.END}")
    print(f"  Context size: {context_size}")
    print(f"  Params: {model_params}")
    print(f"  Orchestrator: {BASE_URL} (timeout={TIMEOUT}s)")

    memory_before = _memory_usage_mb()
    timings = []

    try:
        timings.append(
            await _time_stage(
                "Routing",
                run_agent_routing(model=model, model_params=model_params),
            )
        )
        timings.append(
            await _time_stage(
                "Validation",
                run_response_validation(model=model, model_params=model_params),
            )
        )
        timings.append(
            await _time_stage(
                "Workflow",
                run_complete_workflow(model=model, model_params=model_params),
            )
        )
    finally:
        await unload_ollama_model(model)

    memory_after = _memory_usage_mb()
    total_time = sum(timings)
    avg_time = statistics.mean(timings)
    stddev_time = statistics.pstdev(timings) if len(timings) > 1 else 0.0

    print(f"  Total time: {total_time:.2f}s")
    print(f"  Avg stage: {avg_time:.2f}s (σ={stddev_time:.2f}s)")
    print(f"  Memory delta: {memory_after - memory_before:.2f} MB")
