# CLAUDE.md — ms-brewer

## What this service does

Kafka **producer** — generates random `BrewOrder` events and publishes them to the `brew-orders` topic
every 5–60 seconds (configurable). Injects random errors at a configurable rate to produce
realistic, noisy telemetry for observability learning.

## Tech stack

- Pure Python, no HTTP framework
- `confluent-kafka` — Kafka producer client
- `lib-models` — shared `BrewOrder`, `BrewStyle`, `IngredientType` Pydantic models (editable install)
- `opentelemetry-distro` + `opentelemetry-exporter-otlp` — auto-instrumentation

## Entry point

`brewer/brewer_producer.py` — run via `opentelemetry-instrument` wrapper in Docker.

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------| 
| `KAFKA_BOOTSTRAP_SERVERS` | required | Kafka broker address |
| `INTERVAL_SECONDS` | `60` (code) / `5` (docker-compose) | Publish interval in seconds |
| `ERROR_RATE` | `0.1` | Fraction of messages that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `brewer` | Telemetry service name |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Models

- `BrewOrder` — represents a brew order event (ingredient_type, quantity, brew_style)
- `BrewStyle` — enum: LAGER, IPA, STOUT, WHEAT_BEER
- `IngredientType` — enum: MALT, HOPS, YEAST, WHEAT, BARLEY

## Integration

Publishes to → `brew-orders` Kafka topic → consumed by `ms-brewcheck`

## What I learned building this

Kafka producer patterns in Python, OTEL auto-instrumentation of background processes,
and structured error injection for generating meaningful traces and logs.
