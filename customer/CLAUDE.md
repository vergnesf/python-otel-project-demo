# CLAUDE.md — customer

## What this service does

Kafka **producer** — generates random `Order` events and publishes them to the `orders` topic
every 5–60 seconds (configurable). Injects random errors at a configurable rate to produce
realistic, noisy telemetry for observability learning.

## Tech stack

- Pure Python, no HTTP framework
- `confluent-kafka` — Kafka producer client
- `common-models` — shared `Order` and `WoodType` Pydantic models (editable install)
- `opentelemetry-distro` + `opentelemetry-exporter-otlp` — auto-instrumentation

## Entry point

`customer/customer_producer.py` — run via `opentelemetry-instrument` wrapper in Docker.

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | required | Kafka broker address |
| `INTERVAL_SECONDS` | 5–60 random | Publish interval |
| `ERROR_RATE` | `0.1` | Fraction of messages that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `customer` | Telemetry service name |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Integration

Publishes to → `orders` Kafka topic → consumed by `ordercheck`

## What I learned building this

Kafka producer patterns in Python, OTEL auto-instrumentation of background processes,
and structured error injection for generating meaningful traces and logs.
