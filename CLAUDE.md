# CLAUDE.md — python-otel-project-demo

## Project Nature

Personal **learning lab**, not a production app. Simplicity over engineering.
Each service exists to learn a specific Python/OTEL/infra concept.

## Architecture

Two-layer model:
- **Business layer (KEEPER)** — generates activity and OTEL telemetry → Grafana
- **Agent layer** — reads observability data via MCP Grafana (future / in progress)

## KEEPER Services

| Service | Type | Framework |
|---------|------|-----------|
| `customer` | Kafka producer | none |
| `supplier` | Kafka producer | none |
| `ordercheck` | Kafka consumer | none |
| `suppliercheck` | Kafka consumer | none |
| `ordermanagement` | Background worker | none |
| `order` | REST API + DB | Flask + SQLAlchemy |
| `stock` | REST API + DB | Flask + SQLAlchemy |
| `common-models` | Shared library | Pydantic v2 |
| `common-ai` | Shared AI library | LangChain + MCP |
| `config` | Infra config files | YAML |

## Active Services

- `benchmark` — ACTIVE: test suite for AI agent APIs (latency, throughput, multi-model comparison)
- `agent-traduction` — ACTIVE: translation agent (FastAPI)

## Framework Convention

- **Flask** for KEEPER HTTP services (`order`, `stock`) — synchronous, SQLAlchemy-based. No migration to FastAPI planned.
- **FastAPI** for all agent services — async, LLM-friendly.

## Tools

- **Python 3.14+** and **UV** — see `.github/instructions/python.instructions.md` for full conventions.
  Critical rule: always `uv run <cmd>`, never call `python`/`pip`/`pytest` directly.
- **Docker Compose** — 7 split files orchestrated via `Makefile`
- **Ruff** — linting, line-length=100, rules: E, F, W, I (configured in root `pyproject.toml`)
- **Black** — formatting (`uvx ruff check <project>` / `uv run black <project>`)
- **Pyright** — type checking

## Key Makefile Targets

```bash
make compose-up     # Start full stack (observability → db → kafka → ai-tools → ai → apps → traefik)
make compose-down   # Stop all services (reverse order)
make lint           # Ruff check across all 14 projects
make tools-format   # Black format across all projects
make models-init    # Pull Ollama AI models (mistral, llama, qwen, etc.)
```

## Environment Setup

Copy `.env.example` to `.env` before starting — it contains Docker image tags and
the `GRAFANA_SERVICE_ACCOUNT_TOKEN` placeholder required for the agent layer.

## Git Workflow (mandatory)

- **Always branch + PR** — never commit directly to `main`
- **Conventional Commits** format — see `.github/instructions/commit-message.instructions.md`
- PRs reviewed by a BMAD persona before merging (BMAD is the AI-assisted workflow framework used in this project — see `_bmad/`)

## OpenTelemetry Pattern

All KEEPER services are auto-instrumented via the `opentelemetry-instrument` wrapper in their Dockerfile `CMD`.
Key env vars: `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_TRACES/METRICS/LOGS_EXPORTER`.
Telemetry flows: logs → Loki, metrics → Mimir, traces → Tempo, UI → Grafana (port 3000).

## Error Injection

`ERROR_RATE` env var (0.0–1.0, default 0.1) injects random failures in Kafka producers, consumers,
and the ordermanagement worker. The Flask REST APIs (`order`, `stock`) do not use `ERROR_RATE`.
This is intentional — generates realistic, noisy telemetry for learning OTEL.

## Shared Libraries

- `common-models` — Pydantic models shared across KEEPER services (editable install)
- `common-ai` — LLM config, MCP Grafana client, agent Pydantic models (for agent services only)

## Infrastructure Access (local dev)

All services are behind **Traefik** (port 8081). Direct access:
- Grafana: `http://localhost:3000`
- Order API: `http://localhost:5000`
- Stock API: `http://localhost:5001`

Via Traefik (`http://localhost:8081`):
- Kafka UI (AKHQ): `http://localhost:8081/akhq/`
- Traefik dashboard: `http://localhost:8082`
