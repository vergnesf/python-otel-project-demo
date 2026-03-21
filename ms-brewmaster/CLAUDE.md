# CLAUDE.md — ms-brewmaster

## What this service does

Background **worker** — the brewmaster orchestrates the brew cycle. On each cycle it:
1. Fetches all `REGISTERED` brews from the Brewery API
2. Attempts to consume ingredients via the Cellar API
3. Updates each brew status (`READY` or `BLOCKED`)
4. Injects random errors to generate realistic telemetry

Runs in an infinite loop with a configurable interval.

## Tech stack

- Pure Python, no HTTP framework
- `requests` — HTTP client for Brewery and Cellar API calls
- `lib-models` — shared `BrewStatus`, `InsufficientIngredientError`, `IngredientNotFoundError` (editable install)
- `opentelemetry-distro` + `opentelemetry-exporter-otlp` — auto-instrumentation

## Entry point

`brewmaster/brewmaster.py` — run via `opentelemetry-instrument` wrapper in Docker.

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `API_URL_BREWS` | `http://brewery:5000` | Brewery API base URL |
| `API_URL_CELLAR` | `http://cellar:5001` | Cellar API base URL |
| `INTERVAL_SECONDS` | `5` | Loop interval in seconds |
| `ERROR_RATE` | `0.1` | Fraction of cycles that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `ms-brewmaster` | Telemetry service name |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Integration

Reads from → `http://brewery:5000/brews/status/registered`
Writes to → `http://cellar:5001/ingredients/decrease`
Writes to → `http://brewery:5000/brews/<id>` (status update)

## OTEL

Span name: `"process brew"` (SpanKind default — HTTP client span).
Span attribute: `brew.style` set from the brew response when present.
Typed exceptions from lib-models (`InsufficientIngredientError`, `IngredientNotFoundError`) are
recorded on the span when ingredient operations fail.

## Design decision: polling vs event-driven

`ms-brewmaster` polls `ms-brewery` every 5 seconds via HTTP (`GET /brews/status/registered`).
This is the **only synchronous polling loop** in an otherwise event-driven system.

**Why polling was chosen:**
- Simpler to implement — no Kafka consumer group to manage
- Demonstrates the REST worker pattern as a contrast to Kafka consumers
- Both patterns coexisting in the same lab is pedagogically valuable

No change planned — the polling pattern is intentional for learning purposes.

## What I learned building this

Polling workers with OTEL instrumentation, chaining HTTP calls in a distributed
trace, and simulating realistic business process failures for observability testing.
Typed exception handling from lib-models replaces generic ValueError/RuntimeError.
