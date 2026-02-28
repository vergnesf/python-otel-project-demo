# Ordermanagement Service

> **Status:** `KEEPER` — Stable service. Expected to stay functional and tested.

Background worker that orchestrates the business loop: fetches registered orders,
decreases stock, and updates order statuses on each cycle.

## Why I built this

To learn polling worker patterns with OTEL instrumentation, chaining multiple HTTP calls
into a single distributed trace, and simulating realistic business process failures.

## 📋 Overview

- **Type**: Background Worker (infinite loop)
- **Frequency**: Configurable interval (default: 5 seconds)
- **Error Simulation**: Configurable error rate (default: 10%)
- **Dependencies**: Order Service API, Stock Service API, common-models

## 🚀 Running the Service

```bash
# With Docker (recommended)
docker-compose up ordermanagement

# Local development
cd ordermanagement/ && uv sync
uv run python -m ordermanagement.ordermanagement
```

## 🔧 Configuration

```bash
API_URL_ORDERS=http://order:5000
API_URL_STOCKS=http://stock:5001
INTERVAL_SECONDS=5    # How often to check for orders (seconds)
ERROR_RATE=0.1        # Fraction of cycles that fail (0.0–1.0)
LOG_LEVEL=INFO
OTEL_SERVICE_NAME=ordermanagement
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

## 📊 Processing flow

1. **Fetch**: GET registered orders from Order Service
2. **Decrease stock**: POST `/stocks/decrease` for each order's wood type and quantity
3. **Update status**: PUT order status to `SHIPPED`, `BLOCKED`, or `CLOSED`
4. **Simulate errors**: Randomly fail steps based on `ERROR_RATE`
5. **Wait**: Sleep for `INTERVAL_SECONDS` before next cycle

## 🔄 Integration

Reads from → `http://order:5000/orders/status/registered`
Writes to → `http://stock:5001/stocks/decrease`
Writes to → `http://order:5000/orders/<id>` (status update)

## 📈 Observability

Auto-instrumented via `opentelemetry-instrument`. Logs → Loki, Metrics → Mimir, Traces → Tempo.

## 🧪 Testing

```bash
uv run pytest
uv run pytest --cov=ordermanagement --cov-report=html
```
