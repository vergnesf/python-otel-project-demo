# ms-retailer

Kafka producer service — simulates retailers placing beer orders on the `beer-orders` topic.

## Overview

Part of the brewery KEEPER layer (Phase 2). Simulates bars and restaurants ordering beer
at random intervals, with configurable error injection for realistic OTEL telemetry.

Symmetric counterpart to `ms-brewer` on the output side of the brewery pipeline:
`ms-retailer → [beer-orders] → ms-dispatch → ms-beerstock`

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | required | Kafka broker address |
| `INTERVAL_SECONDS` | `10` | Publish interval in seconds |
| `ERROR_RATE` | `0.1` | Fraction of messages that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `ms-retailer` | Telemetry service name |

## Integration

Publishes to → `beer-orders` topic → to be consumed by `ms-dispatch` (#110)
