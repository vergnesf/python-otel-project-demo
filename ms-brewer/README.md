# ms-brewer

Kafka producer service — generates random `BrewOrder` events and publishes them to the `brew-orders` topic.

## Overview

Part of the brewery KEEPER layer. Simulates a brewer placing brew orders at random intervals,
with configurable error injection for realistic OTEL telemetry.

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | required | Kafka broker address |
| `INTERVAL_SECONDS` | `60` | Publish interval in seconds |
| `ERROR_RATE` | `0.1` | Fraction of messages that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `brewer` | Telemetry service name |

## Integration

Publishes to → `brew-orders` topic → consumed by `ms-brewcheck`
