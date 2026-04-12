# ms-dispatch

Kafka consumer service — dispatches retail beer orders by calling `ms-beerstock`.

Consumes the `beer-orders` topic (produced by `ms-retailer`) and calls `POST /beerstock/ship`
on `ms-beerstock` to fulfill each order. Closes the full brewery pipeline end-to-end.

## Pipeline position

```
ms-retailer → [beer-orders] → ms-dispatch → ms-beerstock API
```

## Business logic

1. Consume `beer-orders` Kafka topic
2. For each order, call `POST /beerstock/ship` with `brew_style` and `quantity`
3. On HTTP 200 → log shipment confirmed (`dispatch.status=shipped`)
4. On HTTP 400 → log backorder, do not crash (`dispatch.status=backorder`)
5. `ERROR_RATE` injection for observability testing

## OTEL patterns introduced

- **Cross-pipeline span link**: links dispatch span to the original retailer span via W3C trace context from Kafka headers
- `retailer.name` span attribute propagated from message payload
- `dispatch.status` span attribute: `"shipped"` or `"backorder"`

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | required | Kafka broker address |
| `API_URL_BEERSTOCK` | `http://ms-beerstock:5002` | BeerStock API base URL |
| `ERROR_RATE` | `0.1` | Fraction of messages that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `ms-dispatch` | Telemetry service name |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Running locally

```bash
uv run pytest          # smoke tests
uv run ruff check .    # linting
```
