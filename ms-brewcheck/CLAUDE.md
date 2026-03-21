# CLAUDE.md — ms-brewcheck

## What this service does

Kafka **consumer** — reads `BrewOrder` events from the `brew-orders` topic and forwards them
to the `brewery` REST API via HTTP POST. No business validation logic — it is a
pass-through bridge between the Kafka topic and the REST API.

## Tech stack

- Pure Python, no HTTP framework exposed
- `confluent-kafka` — Kafka consumer client (group: `brew-check-group`)
- `requests` — HTTP client to call the Brewery API
- `opentelemetry-distro` + `opentelemetry-exporter-otlp` — auto-instrumentation

## Entry point

`brewcheck/brewcheck_consumer.py` — run via `opentelemetry-instrument` wrapper in Docker.

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------| 
| `KAFKA_BOOTSTRAP_SERVERS` | required | Kafka broker address |
| `API_URL` | `http://brewery:5000` | Target Brewery API base URL (appends `/brews`) |
| `ERROR_RATE` | `0.1` | Fraction of messages that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `brewcheck` | Telemetry service name |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Integration

Consumes from ← `brew-orders` Kafka topic (produced by `ms-brewer`)
Forwards to → `http://brewery:5000/brews` (POST)

## What I learned building this

Kafka consumer group patterns, bridging Kafka and REST as a pass-through,
and distributed trace propagation across async message boundaries with OTEL.
