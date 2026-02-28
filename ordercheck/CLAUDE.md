# CLAUDE.md — ordercheck

## What this service does

Kafka **consumer** — reads `Order` events from the `orders` topic, validates them,
then forwards valid orders to the `order` REST API via HTTP POST. Part of the
order validation pipeline between the producer and the database.

## Tech stack

- Pure Python, no HTTP framework exposed
- `confluent-kafka` — Kafka consumer client (group: `order-check-group`)
- `requests` — HTTP client to call the Order API
- `common-models` — shared `Order` Pydantic models (editable install)
- `opentelemetry-distro` + `opentelemetry-exporter-otlp` — auto-instrumentation

## Entry point

`ordercheck/ordercheck_consumer.py` — run via `opentelemetry-instrument` wrapper in Docker.

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | required | Kafka broker address |
| `ORDER_SERVICE_URL` | `http://order:5000` | Target Order API |
| `ERROR_RATE` | `0.1` | Fraction of messages that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `ordercheck` | Telemetry service name |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Integration

Consumes from ← `orders` Kafka topic (produced by `customer`)
Forwards to → `http://order:5000/orders` (POST)

## What I learned building this

Kafka consumer group patterns, bridging Kafka and REST, and distributed trace
propagation across async message boundaries with OTEL.
