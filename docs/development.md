# Local Development Guide

> NOTE: A condensed developer handbook is available at `docs/handbook/development.md`.
> Please prefer the handbook for quick commands and local workflows. This file keeps the full reference.

## Shared Modules

This project uses two shared modules for code reuse:

### common-models/

**Business domain models** used by all business microservices:

- `WoodType` - Enum of wood types (oak, maple, birch, elm, pine)
- `OrderStatus` - Order lifecycle states  
- `Stock`, `Order`, `OrderTracking` - Core business entities

```python
# Import in business services
from common_models import WoodType, OrderStatus, Stock, Order
```

**Used by**: `order`, `stock`, `customer`, `supplier`, `ordercheck`, `suppliercheck`, `ordermanagement`

### common-ai/

**AI utilities** used exclusively by intelligent agents:

- `MCPGrafanaClient` - Unified client for querying Loki/Mimir/Tempo via MCP
- `get_llm()` - LLM configuration helper for LangChain
- `AgentRequest`, `AgentResponse`, `AgentType` - Agent communication models
- `OrchestratorResponse` - Synthesized responses from orchestrator

```python
# Import in AI agents
from common_ai import MCPGrafanaClient, get_llm, AgentRequest
```

**Used by**: `agent-orchestrator`, `agent-logs`, `agent-metrics`, `agent-traces`

## Running Services Locally

Each microservice and agent is set up with **UV** for dependency management.

### Setup

```bash
# Navigate to a service directory
cd order/

# Install dependencies
uv sync

# Run tests
uv run pytest
```

### Running with OpenTelemetry

To run a microservice with auto-instrumentation:

```bash
uv run opentelemetry-instrument \
    --traces_exporter otlp \
    --metrics_exporter otlp \
    --service_name order \
    --exporter_otlp_endpoint http://localhost:4318 \
    --log_level info \
    python -m order.main
```

### Running an Agent

```bash
cd agent-logs/

# Install dependencies (including common-ai)
uv sync

# Run the agent
uv run uvicorn agent_logs.main:app --reload --port 8002
```

## Development with Shared Modules

When developing locally, shared modules must be available:

**Option 1: Install as editable (recommended)**
```bash
# For business services
cd order/
uv pip install -e ../common-models/

# For AI agents
cd agent-logs/
uv pip install -e ../common-models/  # If needed
uv pip install -e ../common-ai/
```

**Option 2: Use PYTHONPATH**
```bash
export PYTHONPATH=/path/to/project:$PYTHONPATH
cd agent-logs/
uv run uvicorn agent_logs.main:app --reload
```

**Note**: In Docker, shared modules are installed automatically during build via `uv pip install -e`.

## Adding Dependencies

Edit the service's `pyproject.toml`:

```toml
[project]
dependencies = [
    "fastapi>=0.115.0",
    "new-package>=1.0.0",  # Add your dependency
]
```

Then run:
```bash
uv sync  # Install new dependencies
```

**Important**: 
- Business services should NOT add `common-ai` dependencies (httpx, langchain)
- AI agents should NOT need `common-models` (it's already in `common-ai` if needed)
- Keep dependencies minimal and separated by concern

## Code Quality

Run formatters and linters:

```bash
# Format code (if ruff is configured)
uv run ruff format .

# Lint code
uv run ruff check .

# Type check (if mypy is configured)
uv run mypy .
```

## AI/LLM Integrations

### Ollama (recommended for local models)

🤖 Ollama lets you run and manage AI models locally with first-class support for single-process runtimes and a small REST API. It's compatible with Podman and Docker and is recommended for local development in this project.

For installation and setup instructions, refer to the Ollama docs: https://docs.ollama.com/quickstart and the API reference at https://docs.ollama.com/api

## GPU Support with NVIDIA Container Toolkit

For AI/LLM features acceleration, you may want GPU support in Docker. This requires the NVIDIA Container Toolkit.

### Prerequisites 📋

First, check if your GPU is detected:

```bash
nvidia-smi
```

You should see your GPU information. If this command fails, install NVIDIA drivers first.

### Installing NVIDIA Container Toolkit

For Fedora/RHEL/CentOS:

```bash
# Configure the production repository
curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | \
  sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo

# Install the toolkit
sudo dnf install -y nvidia-container-toolkit
```

### Configuring Docker

After installation, configure Docker to use the NVIDIA runtime:

```bash
# Configure the container runtime
sudo nvidia-ctk runtime configure --runtime=docker

# Restart Docker daemon
sudo systemctl restart docker
```

### Testing GPU Support

Test that Docker can access your GPU:

```bash
# Test with a simple CUDA container
docker run --rm --gpus all nvidia/cuda:11.0.3-base-ubuntu20.04 nvidia-smi
```

If successful, you should see your GPU information displayed within the container.

For more details, see the [official NVIDIA Container Toolkit documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).
