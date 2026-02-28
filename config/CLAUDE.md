# CLAUDE.md — config

## What this directory does

Static **infrastructure configuration files** for all observability and routing services.
Not a Python service — contains only YAML config files mounted into Docker containers.

## Structure

```
config/
├── ai/
│   └── model-params.yml      — Ollama model parameters (temperature, context, etc.)
├── grafana/
│   └── datasources/
│       └── default.yaml      — Grafana datasources (Loki, Mimir, Tempo)
├── loki/
│   └── loki-config.yml       — Loki log aggregation config
├── mimir/
│   └── mimir-config.yml      — Mimir metrics storage config
├── otel/
│   └── otel-conf.yml         — OTEL Collector pipeline (receivers, processors, exporters)
├── tempo/
│   └── tempo.yml             — Tempo distributed tracing config
└── traefik/
    ├── traefik.yml            — Traefik static config
    └── dynamic_conf.yml       — Traefik dynamic routing rules (service URLs, path prefixes)
```

## Usage

Files are mounted as volumes in the relevant Docker Compose service definitions.
Edit config files here and restart the affected container — no rebuild needed.

## Key OTEL Collector config (`otel/otel-conf.yml`)

Receives traces/metrics/logs via OTLP (gRPC port 4317) and exports to:
- Loki (logs), Mimir (metrics), Tempo (traces)

## What I learned building this

Each backend (Loki, Mimir, Tempo) has a different data model and config syntax.
Wiring them all through the OTEL Collector as a single ingestion point was the
key insight — services only need to know one endpoint (`otel-collector:4317`),
not four separate backends.
