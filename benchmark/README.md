# Benchmark Suite

> **Status:** `ACTIVE` — In active development. Functional and open to improvements.

Comprehensive benchmark suite for AI agent APIs with multi-model performance comparison.

## Features

- 🚀 Multi-model benchmarking (Mistral, Llama, Qwen, Granite, etc.)
- 📊 Performance metrics (latency, memory, accuracy)
- 🔄 Agent API testing via HTTP endpoints
- 📈 Detailed results reporting and analysis
- ⚡ Async execution with proper resource management

## Quick Start

### Installation

```bash
uv sync
```

### Running Benchmarks

```bash
# Simplest way - using the CLI entry point
uv run benchmark

# Or directly with the module
uv run python -m benchmark.main
```

### Configuration

All configuration (service URLs, timeouts, models list) is centralized in `benchmark/config.py` for easy modification.

## Architecture

- **`benchmark/config.py`**: Centralized configuration (URLs, timeouts, models)
- **`benchmark/agents/`**: Individual agent benchmark implementations
- **`benchmark/metrics.py`**: Performance metrics collection
- **`benchmark/models.py`**: Pydantic request/response models
- **`benchmark/main.py`**: Main entry point that runs all benchmarks

## Dependencies

- `httpx`: Async HTTP client
- `pydantic`: Data validation
- `pyyaml`: YAML configuration
- `psutil`: System resource monitoring
- `common-ai`: Shared AI utilities

## Project Structure

```
benchmark/
├── benchmark/
│   ├── __init__.py
│   ├── config.py              # Configuration (URLs, timeouts, models)
│   ├── models.py              # Pydantic request/response models
│   ├── agent_requests.py      # Agent API request models
│   ├── metrics.py             # Metrics collection and analysis
│   ├── main.py                # Main benchmark runner
│   └── agents/
│       ├── __init__.py
│       ├── orchestrator.py    # Orchestrator agent benchmarks
│       ├── logs.py            # Logs agent benchmarks
│       ├── metrics.py         # Metrics agent benchmarks
│       ├── traces.py          # Traces agent benchmarks
│       └── translation.py     # Translation agent benchmarks
├── pyproject.toml
└── README.md
```

## Benchmark Workflow

1. **Model Loading**: Select and configure AI models
2. **Agent Requests**: Send requests to agent APIs
3. **Performance Measurement**:
   - Response latency (p50, p95, p99)
   - Memory usage (delta)
   - Token throughput
   - Error rates
4. **Results Aggregation**: Collect and analyze metrics
5. **Reporting**: Generate detailed reports

## API Endpoints Tested

- **Orchestrator**: `POST /analyze` - Full workflow analysis
- **Logs Agent**: `POST /analyze` - Log analysis via Loki
- **Metrics Agent**: `POST /analyze` - Metrics analysis via Mimir
- **Traces Agent**: `POST /analyze` - Trace analysis via Tempo
- **Translation Agent**: `POST /translate` - Language translation

## Development

```bash
# Format code
uv run black benchmark tests

# Lint
uv run ruff check benchmark tests

# Type checking
uv run pyright
```
