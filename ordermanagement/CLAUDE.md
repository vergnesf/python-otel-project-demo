# CLAUDE.md — ordermanagement

## What this service does

Background **worker** — the orchestrator of the business loop. On each cycle it:
1. Fetches all `REGISTERED` orders from the Order API
2. Attempts to decrease stock via the Stock API
3. Updates each order status (`SHIPPED`, `BLOCKED`, or `CLOSED`)
4. Injects random errors to generate realistic telemetry

Runs in an infinite loop with a configurable interval.

## Tech stack

- Pure Python, no HTTP framework
- `requests` — HTTP client for Order and Stock API calls
- `common-models` — shared Pydantic models (editable install)
- `opentelemetry-distro` + `opentelemetry-exporter-otlp` — auto-instrumentation

## Entry point

`ordermanagement/ordermanagement.py` — run via `opentelemetry-instrument` wrapper in Docker.

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `ORDER_SERVICE_URL` | `http://order:5000` | Order API base URL |
| `STOCK_SERVICE_URL` | `http://stock:5001` | Stock API base URL |
| `INTERVAL_SECONDS` | `5` | Loop interval |
| `ERROR_RATE` | `0.1` | Fraction of cycles that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `ordermanagement` | Telemetry service name |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Integration

Reads from → `http://order:5000/orders/status/registered`
Writes to → `http://stock:5001/stocks/decrease`
Writes to → `http://order:5000/orders/<id>` (status update)

## What I learned building this

Polling workers with OTEL instrumentation, chaining HTTP calls in a distributed
trace, and simulating realistic business process failures for observability testing.
