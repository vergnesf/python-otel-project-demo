# CLAUDE.md — ms-dispatch

## What this service does

Kafka **consumer** — dispatches retail beer orders. Consumes the `beer-orders` topic
(produced by `ms-retailer`) and calls `POST /beerstock/ship` on `ms-beerstock` to fulfill
each order. Closes the full brewery end-to-end pipeline.

Introduces new OTEL pattern: **cross-pipeline span link** linking the dispatch consumer
span to the original retailer producer span via W3C trace context from Kafka headers.

## Tech stack

- Pure Python, no HTTP framework
- `confluent-kafka` — Kafka consumer client (group: `dispatch-group`)
- `requests` — HTTP client to call the BeerStock API
- `lib-models` — shared `BeerOrder`, `BeerStyle` (editable install)
- `opentelemetry-distro` + `opentelemetry-exporter-otlp` — auto-instrumentation

## Entry point

`dispatch/dispatch_consumer.py` — run via `opentelemetry-instrument` wrapper in Docker.

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | required | Kafka broker address |
| `API_URL_BEERSTOCK` | `http://ms-beerstock:5002` | BeerStock API base URL (appends `/beerstock/ship`) |
| `ERROR_RATE` | `0.1` | Fraction of messages that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `ms-dispatch` | Telemetry service name |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Integration

Consumes from ← `beer-orders` Kafka topic (produced by `ms-retailer`)
Calls → `POST http://ms-beerstock:5002/beerstock/ship`

## OTEL patterns

- Span name: `"process beer-orders"` (SpanKind.CONSUMER)
- Span links: W3C trace context extracted from Kafka headers → linked to retailer producer span
- Span attributes: `retailer.name`, `dispatch.status` (`"shipped"` or `"backorder"`), `messaging.*` semconv
- Metrics: `beer_orders.dispatched`, `beer_orders.backorder`, `beer_orders.dispatch_errors`

## Business outcomes (dispatch.status)

- `"shipped"` — HTTP 200 from `/beerstock/ship` (stock decremented)
- `"backorder"` — HTTP 400 from `/beerstock/ship` (insufficient stock), does NOT crash

## What I learned building this

Cross-pipeline span links via W3C context in Kafka headers, propagating business attributes
(`retailer.name`, `dispatch.status`) through the full brewery lifecycle trace.
