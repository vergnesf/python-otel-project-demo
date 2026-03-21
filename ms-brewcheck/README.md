# ms-brewcheck

Kafka consumer service — reads `BrewOrder` events from the `brew-orders` topic and forwards them to the ms-brewery REST API.

## Overview

Pass-through bridge: consumes from `brew-orders` Kafka topic, POSTs each message to `ms-brewery` at `/brews`.

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | required | Kafka broker address |
| `API_URL` | `http://brewery:5000` | Target Brewery API base URL |
| `ERROR_RATE` | `0.1` | Fraction of messages that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `brewcheck` | Telemetry service name |

## Integration

Consumes from ← `brew-orders` topic (produced by `ms-brewer`)
Forwards to → `http://brewery:5000/brews` (POST, ms-brewery)
