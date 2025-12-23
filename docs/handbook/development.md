````markdown
# Development Handbook (condensed)

Quick start for local development and iterations.

## Shared modules
- `common-models/`: business models used by microservices
- `common-ai/`: MCP client, LLM helpers, agent models

## Install & run
```bash
# From a service directory (example: order/)
cd order/
# Install deps
uv sync
# Run service
uv run uvicorn order.main:app --reload
```

## Running agents
```bash
cd agent-logs/
uv sync
uv run uvicorn agent_logs.main:app --reload --port 8002
```

## Shared-module editable installs (recommended)
```bash
cd agent-logs/
uv pip install -e ../common-ai/
uv pip install -e ../common-models/  # if needed
```

## Useful commands
- Format: `uv run ruff format .`
- Tests: `uv run pytest`
- Type check: `uv run mypy .` (if configured)

````