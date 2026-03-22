# CLAUDE.md — ms-quality-control

## What this service does

Kafka **consumer** — performs quality control on finished brews. Consumes the `brews-ready`
topic (published by `ms-brewery` when a brew transitions to `READY`) and updates brew status
to `APPROVED` or `REJECTED` via the Brewery REST API.

Introduces a new OTEL pattern: **binary validation outcome** with `quality.check.passed`
and `quality.reject_reason` span attributes.

## Tech stack

- Pure Python, no HTTP framework
- `confluent-kafka` — Kafka consumer client (group: `quality-control-group`)
- `requests` — HTTP client to call the Brewery API
- `lib-models` — shared `BrewStatus` (editable install)
- `opentelemetry-distro` + `opentelemetry-exporter-otlp` — auto-instrumentation

## Entry point

`quality_control/quality_consumer.py` — run via `opentelemetry-instrument` wrapper in Docker.

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | required | Kafka broker address |
| `API_URL` | `http://brewery:5000` | Brewery API base URL (appends `/brews`) |
| `REJECT_RATE` | `0.1` | Fraction of brews rejected (0.0–1.0) |
| `ERROR_RATE` | `0.1` | Fraction of messages that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `ms-quality-control` | Telemetry service name |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Integration

Consumes from ← `brews-ready` Kafka topic (published by `ms-brewery` on READY transition)
Writes to  → `PUT http://ms-brewery:5000/brews/<id>` (status: APPROVED or REJECTED)

## OTEL patterns

- Span name: `"process brews-ready"` (SpanKind.CONSUMER)
- Span links: W3C trace context extracted from Kafka headers → linked to producer span
- Span attributes: `quality.check.passed` (bool), `quality.reject_reason` (str, only on reject),
  `brew.style`, `messaging.*` semconv attributes
- Metrics: `brews.quality_checked`, `brews.quality_rejected`, `brews.quality_errors`

## Reject reasons (simulated)

`color_off`, `bitterness_high`, `clarity_poor` — randomly selected on rejection.

## What I learned building this

Binary outcome spans with conditional attributes, linking consumer traces to Flask API
producers via Kafka headers, and combining REJECT_RATE with ERROR_RATE for richer telemetry.
