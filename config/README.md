# Config

> **Status:** `KEEPER` — Stable configuration. Expected to stay functional and up to date.

Infrastructure configuration files for the observability stack.

## Contents

| Directory | Purpose |
|-----------|---------|
| `ai/` | LLM model parameters (`model-params.yml`) |
| `grafana/` | Grafana datasources (Loki, Mimir, Tempo, Prometheus) |
| `loki/` | Loki log aggregation configuration |
| `mimir/` | Mimir metrics storage configuration |
| `otel/` | OpenTelemetry Collector pipeline configuration |
| `tempo/` | Tempo distributed tracing configuration |
| `traefik/` | Traefik reverse proxy routing rules |
