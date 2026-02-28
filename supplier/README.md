# Supplier Service

> **Status:** `KEEPER` — Stable service. Expected to stay functional and tested.

Kafka producer that simulates supplier stock updates being sent to the system.

## Why I built this

To learn how to structure multiple symmetric Kafka producers sharing a model library,
and how keeping services symmetric makes observability comparison in Grafana much easier.

## 📋 Overview

- **Type**: Kafka Producer
- **Topic**: `stocks`
- **Frequency**: Configurable interval (60s in code, 5s in docker-compose)
- **Error Simulation**: Configurable error rate (default: 10%)
- **Dependencies**: Kafka broker, common-models

## 🚀 Running the Service

```bash
# With Docker (recommended)
docker-compose up supplier

# Local development
cd supplier/ && uv sync
uv run python -m supplier.supplier_producer
```

## 🔧 Configuration

```bash
KAFKA_BOOTSTRAP_SERVERS=broker:29092
INTERVAL_SECONDS=60     # How often to send stock updates (seconds)
ERROR_RATE=0.1          # Fraction of updates that will fail (0.0–1.0)
LOG_LEVEL=INFO
OTEL_SERVICE_NAME=supplier
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

## 📊 What it generates

Random stock updates with wood types (oak, maple, birch, elm, pine) and quantities (1–100 units).
Randomly fails at `ERROR_RATE` to produce noisy, realistic telemetry.

## 🔄 Integration

Publishes to → `stocks` Kafka topic → consumed by `suppliercheck`

## 📈 Observability

Auto-instrumented via `opentelemetry-instrument`. Logs → Loki, Metrics → Mimir, Traces → Tempo.

## 🧪 Testing

```bash
uv run pytest
uv run pytest --cov=supplier --cov-report=html
```
