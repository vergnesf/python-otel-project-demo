# Config

> **Status:** `KEEPER` — Stable configuration. Expected to stay functional and up to date.

Static infrastructure configuration files for all observability and routing services.
Not a Python service — YAML files mounted as volumes into Docker containers.

## Why I built this

To learn that each observability backend (Loki, Mimir, Tempo) has a different data model
and config syntax, and that routing everything through the OTEL Collector as a single
ingestion point dramatically simplifies service configuration.

## Contents

| Directory | Purpose |
|-----------|---------|
| `ai/` | Ollama model parameters (`model-params.yml`) |
| `grafana/` | Grafana datasources (Loki, Mimir, Tempo) |
| `loki/` | Loki log aggregation configuration |
| `mimir/` | Mimir metrics storage configuration |
| `otel/` | OTEL Collector pipeline (receives OTLP on :4317, exports to all backends) |
| `tempo/` | Tempo distributed tracing configuration |
| `traefik/` | Traefik reverse proxy routing rules and static config |

## Usage

Edit a config file, then restart the affected container — no rebuild needed:

```bash
docker-compose restart <service-name>
```
