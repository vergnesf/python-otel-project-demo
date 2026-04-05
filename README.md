# Python OpenTelemetry Demo 🐍

> A microservices platform for learning Python auto-instrumentation with OpenTelemetry and AI-powered observability analysis

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-enabled-blueviolet)](https://opentelemetry.io/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)](https://www.docker.com/)

## Quick Start

For a complete guide (Docker, Podman, GPU setup), see [GETTING_STARTED.md](GETTING_STARTED.md).

The compose configuration is split across multiple files. Use the Taskfile helpers to bring the full stack up and down in the correct order (requires [go-task](https://taskfile.dev), install: `mise use task@latest` or `brew install go-task`):

```bash
task compose-up    # observability → db → kafka → ai-tools → ai → apps → traefik
task compose-down  # stops services in reverse order
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Business Layer (KEEPER)                                    │
│  brewer   → kafka → brewcheck     → brewery → postgres     │
│  supplier → kafka → ingredientcheck → cellar → postgres    │
│  retailer → kafka → (dispatch, coming soon)                │
│  brewmaster (background worker)                             │
└─────────────────────────────────────────────────────────────┘
                          ↓ OTLP
┌─────────────────────────────────────────────────────────────┐
│  Observability Stack (Grafana, Loki, Mimir, Tempo)         │
└─────────────────────────────────────────────────────────────┘
                          ↑ MCP Protocol
┌─────────────────────────────────────────────────────────────┐
│  AI Agentic Network (Orchestrator + Specialized Agents)     │
└─────────────────────────────────────────────────────────────┘
```

See [Architecture](docs/architecture.md) for full details.

## Project Structure

```
├── lib-models/            # Shared business models (Pydantic v2)
├── lib-ai/                # Shared AI utilities (MCP client, LLM config)
├── ms-brewer/             # Brew orders producer (Kafka)
├── ms-brewery/            # Brewery management API (Flask + PostgreSQL)
├── ms-cellar/             # Ingredient stock API (Flask + PostgreSQL)
├── ms-supplier/           # Ingredient deliveries producer (Kafka)
├── ms-retailer/           # Retail beer orders producer (Kafka)
├── ms-brewcheck/          # Brew order validator (Kafka consumer)
├── ms-ingredientcheck/    # Ingredient delivery validator (Kafka consumer)
├── ms-brewmaster/         # Brew orchestration worker
├── agent-orchestrator/    # AI Agent: main coordinator
├── agent-logs/            # AI Agent: Loki log analysis
├── agent-metrics/         # AI Agent: Mimir metrics analysis
├── agent-traces/          # AI Agent: Tempo traces analysis
├── agent-ui/              # Web UI for agents
├── config/                # Grafana, Loki, Mimir, Tempo configuration
└── docs/                  # Documentation
```

## Access Points

**All services via Traefik on port 8081**

| Service | URL |
|---------|-----|
| Grafana | http://localhost:8081/grafana/ |
| Agents Web UI | http://localhost:8081/agents/ui/ |
| Orchestrator API | http://localhost:8081/agents/orchestrator/ |
| Order Service | http://localhost:8081/apps/order/ |
| Stock Service | http://localhost:8081/apps/stock/ |
| AKHQ (Kafka UI) | http://localhost:8081/akhq/ |
| Adminer (DB) | http://localhost:8081/adminer/ |
| Traefik Dashboard | http://localhost:8082 |

**Default Grafana credentials**: `admin` / `admin`

## AI Agents

Open http://localhost:8081/agents/ui/ and ask in natural language:

- "Show me errors in the order service"
- "What's the CPU usage of the brewery service?"
- "Analyze slow traces in the last hour"

For setup (Grafana service account token), see [GETTING_STARTED.md](GETTING_STARTED.md).

## Technology Stack

- **Python 3.14** + **UV** — runtime and package management
- **OpenTelemetry** — auto-instrumentation (traces, metrics, logs)
- **Grafana Stack** — Loki, Mimir, Tempo, Grafana
- **Kafka** — message streaming
- **Flask** + **PostgreSQL** — business REST APIs
- **FastAPI** — AI agent services
- **LangChain** — LLM framework

---
