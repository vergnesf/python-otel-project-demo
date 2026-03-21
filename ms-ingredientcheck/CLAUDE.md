# CLAUDE.md — ms-ingredientcheck

## What this service does

Kafka **consumer** — reads `IngredientStock` events from the `ingredient-deliveries` topic and forwards them
to the `cellar` REST API via HTTP POST. Symmetric counterpart to `ms-brewcheck`
in the supplier pipeline.

## Tech stack

- Pure Python, no HTTP framework exposed
- `confluent-kafka` — Kafka consumer client (group: `ingredient-check-group`)
- `requests` — HTTP client to call the Cellar API
- `opentelemetry-distro` + `opentelemetry-exporter-otlp` — auto-instrumentation

## Entry point

`ingredientcheck/ingredientcheck_consumer.py` — run via `opentelemetry-instrument` wrapper in Docker.

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------| 
| `KAFKA_BOOTSTRAP_SERVERS` | required | Kafka broker address |
| `API_URL` | `http://cellar:5001` | Target Cellar API base URL (appends `/ingredients`) |
| `ERROR_RATE` | `0.1` | Fraction of messages that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `ms-ingredientcheck` | Telemetry service name |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Integration

Consumes from ← `ingredient-deliveries` Kafka topic (produced by `ms-supplier`)
Forwards to → `http://cellar:5001/ingredients` (POST)

## What I learned building this

How two symmetric Kafka consumer services can diverge in dependency management
over time, and why keeping symmetric services truly symmetric avoids confusion.
