# ms-ingredientcheck

Kafka consumer service — reads `IngredientStock` events from the `ingredient-deliveries` topic and forwards them to the ms-cellar REST API.

## Overview

Pass-through bridge: consumes from `ingredient-deliveries` Kafka topic, POSTs each message to `ms-cellar` at `/ingredients`.

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | required | Kafka broker address |
| `API_URL` | `http://cellar:5001` | Target Cellar API base URL |
| `ERROR_RATE` | `0.1` | Fraction of messages that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `ingredientcheck` | Telemetry service name |

## Integration

Consumes from ← `ingredient-deliveries` topic (produced by `ms-supplier`)
Forwards to → `http://cellar:5001/ingredients` (POST, ms-cellar)
