# Experiments

Learning journal — what was explored and when.

## 2026

- **2026-02**: Decided to keep Flask for `order` and `stock` KEEPER services (synchronous, SQLAlchemy-based), and FastAPI for all agent services (async, LLM-friendly). No migration planned — see [#23](https://github.com/vergnesf/python-otel-project-demo/issues/23)
- **2026-02**: Experimented with BMAD agentic workflow method for project management
- **2026-02**: Added MCP Grafana integration for AI agents to query observability data
- **2026-02**: Built AI agentic network (orchestrator + logs/metrics/traces agents) using LangChain + local LLMs via Ollama

## 2025

- Migrated to UV as Python package manager
- Added OpenTelemetry auto-instrumentation across all business services
- Set up full Grafana observability stack (Loki, Mimir, Tempo)
- Added Kafka message streaming between producers and consumers
- Started project to learn Python microservices patterns
