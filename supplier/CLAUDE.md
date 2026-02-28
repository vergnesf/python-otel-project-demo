# CLAUDE.md — supplier

## What this service does

Kafka **producer** — generates random `Stock` events and publishes them to the `stocks` topic.
Mirrors `customer` in structure: random intervals, error injection, full OTEL instrumentation.

## Tech stack

- Pure Python, no HTTP framework
- `confluent-kafka` — Kafka producer client
- `common-models` — shared `Stock` and `WoodType` Pydantic models (editable install)
- `opentelemetry-distro` + `opentelemetry-exporter-otlp` — auto-instrumentation

## Entry point

`supplier/supplier_producer.py` — run via `opentelemetry-instrument` wrapper in Docker.

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | required | Kafka broker address |
| `INTERVAL_SECONDS` | configurable | Publish interval |
| `ERROR_RATE` | `0.1` | Fraction of messages that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `supplier` | Telemetry service name |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Integration

Publishes to → `stocks` Kafka topic → consumed by `suppliercheck`

## What I learned building this

Structuring multiple Kafka producers with a shared model library, keeping services
symmetric for easier observability comparison in Grafana.
