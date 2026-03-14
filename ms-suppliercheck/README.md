# Suppliercheck Service

> **Status:** `KEEPER` — Stable service. Expected to stay functional and tested.

Kafka consumer that reads stock updates from the `stocks` topic and forwards them to the Stock REST API.

## Why I built this

To learn how symmetric Kafka consumer services can silently diverge in dependency management
over time, and why keeping symmetric services truly symmetric avoids confusion.

## 📋 Overview

- **Type**: Kafka Consumer (pass-through — no schema validation; error simulation via `ERROR_RATE`)
- **Topic**: `stocks`
- **Consumer Group**: `stock-check-group`
- **Error Simulation**: Configurable error rate (default: 10%)
- **Dependencies**: Kafka broker, Stock Service API

## 🚀 Running the Service

```bash
# With Docker (recommended)
docker-compose up suppliercheck

# Local development
cd suppliercheck/ && uv sync
uv run python -m suppliercheck.suppliercheck_consumer
```

## 🔧 Configuration

```bash
KAFKA_BOOTSTRAP_SERVERS=broker:29092
API_URL=http://stock:5001
ERROR_RATE=0.1    # Fraction of messages that fail (0.0–1.0)
LOG_LEVEL=INFO
OTEL_SERVICE_NAME=suppliercheck
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

## 📊 Processing flow

1. **Consume**: Read stock JSON from Kafka `stocks` topic
2. **Simulate Errors**: Randomly fail based on `ERROR_RATE`
3. **Forward**: POST raw JSON payload to Stock Service API
4. **Log**: Record result for observability

## 🔄 Integration

Consumes from ← `stocks` Kafka topic (produced by `supplier`)
Forwards to → `http://stock:5001/stocks` (POST)

## 📈 Observability

Auto-instrumented via `opentelemetry-instrument`. Logs → Loki, Metrics → Mimir, Traces → Tempo.

## 🧪 Testing

> Note: `tests/` currently contains only an empty `__init__.py` — smoke tests tracked in issue #17.

```bash
uv run pytest
uv run pytest --cov=suppliercheck --cov-report=html
```
