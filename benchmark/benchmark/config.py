"""Configuration settings for benchmark project."""

import os
from pathlib import Path
import yaml


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
            temperature = model_data.get("temperature", 0.1)
            top_k = model_data.get("top_k")
            max_tokens = model_data.get("max_tokens", 2000)
            model_configs[model_name] = {
                "context_size": context_size,
                "temperature": temperature,
                "top_k": top_k,
                "max_tokens": max_tokens,
            }

        return model_configs
    except Exception as e:
        return {}


# Service URLs via Traefik
# Override with BENCHMARK_BASE_URL env var when running inside the devcontainer:
#   export BENCHMARK_BASE_URL=http://traefik  (port 80 = web entrypoint)
_BASE_URL = os.getenv("BENCHMARK_BASE_URL", "http://localhost:8081")
ORCHESTRATOR_URL = f"{_BASE_URL}/agents/orchestrator"
AGENT_LOGS_URL = f"{_BASE_URL}/agents/logs"
AGENT_METRICS_URL = f"{_BASE_URL}/agents/metrics"
AGENT_TRACES_URL = f"{_BASE_URL}/agents/traces"
TRANSLATION_URL = f"{_BASE_URL}/agents/traduction"
OLLAMA_URL = f"{_BASE_URL}/ollama"

# Benchmark Settings
BENCHMARK_TIMEOUT = 600  # seconds (10 minutes for AI requests)
NUM_TEST_REQUESTS = 1  # Number of test requests per model to validate consistency

# Default models for benchmarking (complete list from test_benchmark_models.py)
BENCHMARK_MODELS = [
    "qwen3:0.6b",  # Temporary: testing with one small model
    "mistral:7b",
    # "llama3.2:3b",
    # "granite4:3b",
    # "mistral-nemo:12b",
    # "qwen2.5:7b",
    # "phi4:14b",
]

# Model configurations
MODEL_CONFIGS = load_model_configs()

# Logging
LOG_LEVEL = "INFO"
