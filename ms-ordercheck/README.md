# Ordercheck Service

> **Status:** `KEEPER` — Stable service. Expected to stay functional and tested.

Kafka consumer that reads orders from the `orders` topic and forwards them to the Order REST API.

## Why I built this

To learn Kafka consumer group patterns, bridging Kafka and REST as a pass-through bridge,
and how distributed traces propagate across async message boundaries with OTEL.

## 📋 Overview

- **Type**: Kafka Consumer (pass-through — no schema validation; error simulation via `ERROR_RATE`)
- **Topic**: `orders`
- **Consumer Group**: `order-check-group`
- **Error Simulation**: Configurable error rate (default: 10%)
- **Dependencies**: Kafka broker, Order Service API

## 🚀 Running the Service

```bash
# With Docker (recommended)
docker-compose up ordercheck

# Local development
cd ordercheck/ && uv sync
uv run python -m ordercheck.ordercheck_consumer
```

## 🔧 Configuration

```bash
KAFKA_BOOTSTRAP_SERVERS=broker:29092
API_URL=http://order:5000
ERROR_RATE=0.1    # Fraction of messages that fail (0.0–1.0)
LOG_LEVEL=INFO
OTEL_SERVICE_NAME=ordercheck
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

## 📊 Processing flow

1. **Consume**: Read order JSON from Kafka `orders` topic
2. **Simulate Errors**: Randomly fail based on `ERROR_RATE`
3. **Forward**: POST raw JSON payload to Order Service API
4. **Log**: Record result for observability

> Note: No schema validation is performed — raw dict payloads are forwarded as-is.

## 🔄 Integration

Consumes from ← `orders` Kafka topic (produced by `customer`)
Forwards to → `http://order:5000/orders` (POST)

## 📈 Observability

Auto-instrumented via `opentelemetry-instrument`. Logs → Loki, Metrics → Mimir, Traces → Tempo.

## 🧪 Testing

> Note: `tests/` currently contains only an empty `__init__.py` — smoke tests tracked in issue #17.

```bash
uv run pytest
uv run pytest --cov=ordercheck --cov-report=html
```
