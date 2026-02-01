"""Configuration settings for benchmark project."""

# Service URLs (localhost:8080 - benchmark runs outside docker-compose)
# Traefik container port 80 is mapped to host port 8080
ORCHESTRATOR_URL = "http://localhost:8080/agents/orchestrator"
AGENT_LOGS_URL = "http://localhost:8080/agents/logs"
AGENT_METRICS_URL = "http://localhost:8080/agents/metrics"
AGENT_TRACES_URL = "http://localhost:8080/agents/traces"
TRANSLATION_URL = "http://localhost:8080/agents/traduction"

# Benchmark Settings
BENCHMARK_TIMEOUT = 600  # seconds (10 minutes for AI requests)
NUM_TEST_REQUESTS = 3  # Number of test requests per model to validate consistency

# Default models for benchmarking (complete list from test_benchmark_models.py)
BENCHMARK_MODELS = [
    "qwen3:0.6b",  # Temporary: testing with one small model
    # "mistral:7b",
    # "llama3.2:3b",
    # "granite4:3b",
    # "mistral-nemo:12b",
    # "qwen2.5:7b",
    # "phi4:14b",
]

# Logging
LOG_LEVEL = "INFO"
