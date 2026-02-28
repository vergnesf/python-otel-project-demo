# CLAUDE.md — suppliercheck

## What this service does

Kafka **consumer** — reads `Stock` events from the `stocks` topic and forwards them
to the `stock` REST API via HTTP POST. Symmetric counterpart to `ordercheck`
in the supplier pipeline.

## Tech stack

- Pure Python, no HTTP framework exposed
- `confluent-kafka` — Kafka consumer client (group: `stock-check-group`)
- `requests` — HTTP client to call the Stock API
- `opentelemetry-distro` + `opentelemetry-exporter-otlp` — auto-instrumentation
- Note: does not depend on `common-models` (uses raw dict payloads)

## Entry point

`suppliercheck/suppliercheck_consumer.py` — run via `opentelemetry-instrument` wrapper in Docker.

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | required | Kafka broker address |
| `STOCK_SERVICE_URL` | `http://stock:5001` | Target Stock API |
| `ERROR_RATE` | `0.1` | Fraction of messages that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `suppliercheck` | Telemetry service name |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Integration

Consumes from ← `stocks` Kafka topic (produced by `supplier`)
Forwards to → `http://stock:5001/stocks` (POST)

## What I learned building this

Comparing Kafka consumer patterns with and without a shared model library,
and how symmetric service pairs appear in distributed traces.
