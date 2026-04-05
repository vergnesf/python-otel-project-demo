# CLAUDE.md — ms-retailer

## What this service does

Kafka **producer** — simulates retailers (bars, restaurants) placing beer orders on the `beer-orders` topic
every 10 seconds (configurable). Injects random errors at a configurable rate to produce
realistic, noisy telemetry for observability learning.

## Tech stack

- Pure Python, no HTTP framework
- `confluent-kafka` — Kafka producer client
- `lib-models` — shared `BeerOrder`, `BrewStyle` Pydantic models (editable install)
- `opentelemetry-distro` + `opentelemetry-exporter-otlp` — auto-instrumentation

## Entry point

`retailer/retailer_producer.py` — run via `opentelemetry-instrument` wrapper in Docker.

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | required | Kafka broker address |
| `INTERVAL_SECONDS` | `10` (code) / `10` (docker-compose) | Publish interval in seconds |
| `ERROR_RATE` | `0.1` | Fraction of messages that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `ms-retailer` | Telemetry service name |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Models

- `BeerOrder` — represents a retail beer order (brew_style, quantity, retailer_name)
- `BrewStyle` — enum: LAGER, IPA, STOUT, WHEAT_BEER

## OTEL patterns introduced

- Span `send beer-order` · SpanKind: `PRODUCER`
- Span attributes: `retailer.name`, `brew.style` — business context in traces
- W3C trace context injected into Kafka headers (same pattern as `ms-brewer`)
- `beer_orders.created` counter — messages successfully enqueued
- `beer_orders.failed` counter — simulated (ERROR_RATE) + real Kafka failures
- Broker-confirmed delivery failures also increment `beer_orders.failed` via `delivery_report` callback

## Integration

Publishes to → `beer-orders` Kafka topic → to be consumed by `ms-dispatch` (issue #110)

## What I learned building this

Second producer alongside `ms-brewer` — observing two producers simultaneously in Grafana,
business-context span attributes (`retailer.name`), and proper KafkaException handling
within an active span context.
