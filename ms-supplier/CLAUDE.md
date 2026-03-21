# CLAUDE.md — ms-supplier

## What this service does

Kafka **producer** — generates random `IngredientStock` events and publishes them to the `ingredient-deliveries` topic.
Mirrors `ms-brewer` in structure: random intervals, error injection, full OTEL instrumentation.

## Tech stack

- Pure Python, no HTTP framework
- `confluent-kafka` — Kafka producer client
- `lib-models` — shared `IngredientStock` and `IngredientType` Pydantic models (editable install)
- `opentelemetry-distro` + `opentelemetry-exporter-otlp` — auto-instrumentation

## Entry point

`supplier/supplier_producer.py` — run via `opentelemetry-instrument` wrapper in Docker.

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | required | Kafka broker address |
| `INTERVAL_SECONDS` | `60` (code) / `5` (docker-compose) | Publish interval in seconds |
| `ERROR_RATE` | `0.1` | Fraction of messages that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `ms-supplier` | Telemetry service name |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Models

- `IngredientStock` — represents an ingredient delivery event (ingredient_type, quantity)
- `IngredientType` — enum: MALT, HOPS, YEAST, WHEAT, BARLEY

## Integration

Publishes to → `ingredient-deliveries` Kafka topic → consumed by `ms-ingredientcheck`

## What I learned building this

Structuring multiple Kafka producers with a shared model library, keeping services
symmetric for easier observability comparison in Grafana.
