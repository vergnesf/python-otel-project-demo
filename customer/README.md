# Customer Service

> **Status:** `KEEPER` — Stable service. Expected to stay functional and tested.

Kafka producer that simulates customer orders being placed in the system.

## Why I built this

To learn Kafka producer patterns in Python, OTEL auto-instrumentation of background
processes, and how structured error injection generates meaningful traces and logs.

## 📋 Overview

- **Type**: Kafka Producer
- **Topic**: `orders`
- **Frequency**: Configurable interval (default: 60 seconds)
- **Error Simulation**: Configurable error rate (default: 10%)
- **Dependencies**: Kafka broker, common-models

## 🚀 Running the Service

```bash
# With Docker (recommended)
docker-compose up customer

# Local development
cd customer/ && uv sync
uv run python -m customer.customer_producer
```

## 🔧 Configuration

```bash
KAFKA_BOOTSTRAP_SERVERS=broker:29092
INTERVAL_SECONDS=60     # How often to send orders (seconds)
ERROR_RATE=0.1          # Fraction of orders that will fail (0.0–1.0)
LOG_LEVEL=INFO
OTEL_SERVICE_NAME=customer
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

## 📊 What it generates

Random orders with wood types (oak, maple, birch, elm, pine) and quantities (1–100 units).
Randomly fails at `ERROR_RATE` to produce noisy, realistic telemetry.

## 🔄 Integration

Publishes to → `orders` Kafka topic → consumed by `ordercheck`

## 📈 Observability

Auto-instrumented via `opentelemetry-instrument`. Logs → Loki, Metrics → Mimir, Traces → Tempo.

## 🧪 Testing

```bash
uv run pytest
uv run pytest --cov=customer --cov-report=html
```
