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
- Does not declare `common-models` as a dependency (unlike `ordercheck`) — both services
  use raw JSON dict payloads from Kafka; the `common-models` dep in `ordercheck` is unused
  in the consumer path and should be considered technical debt.

## Entry point

`suppliercheck/suppliercheck_consumer.py` — run via `opentelemetry-instrument` wrapper in Docker.

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | required | Kafka broker address |
| `API_URL` | `http://stock:5001` | Target Stock API base URL (appends `/stocks`) |
| `ERROR_RATE` | `0.1` | Fraction of messages that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `suppliercheck` | Telemetry service name |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Integration

Consumes from ← `stocks` Kafka topic (produced by `supplier`)
Forwards to → `http://stock:5001/stocks` (POST)

## What I learned building this

How two symmetric Kafka consumer services can diverge in dependency management
over time, and why keeping symmetric services truly symmetric avoids confusion.
