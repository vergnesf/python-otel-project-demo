# CLAUDE.md — ms-fermentation

## What this service does

Background **worker** — simulates fermentation timing. Polls `ms-brewery` for brews in
`BREWING` status and transitions them to `READY` once the configured fermentation time elapses.

Introduces OTEL patterns not present in other KEEPER services:
- **Span events**: `fermentation.started` (first observation) and `fermentation.complete` (transition to READY)
- **Progress attributes**: `fermentation.progress_pct` updated on each polling cycle

## Tech stack

- Pure Python, no HTTP framework
- `requests` — HTTP client for Brewery API calls
- `lib-models` — shared `BrewStatus` (editable install)
- `opentelemetry-distro` + `opentelemetry-exporter-otlp` — auto-instrumentation

## Entry point

`fermentation/fermentation_worker.py` — run via `opentelemetry-instrument` wrapper in Docker.

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `API_URL_BREWS` | `http://brewery:5000` | Brewery API base URL |
| `FERMENTATION_SECONDS` | `30` | Simulated fermentation time per brew |
| `INTERVAL_SECONDS` | `10` | Polling interval in seconds |
| `ERROR_RATE` | `0.1` | Fraction of completions that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `fermentation` | Telemetry service name |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Integration

Reads from → `http://ms-brewery:5000/brews/status/brewing`
Writes to  → `http://ms-brewery:5000/brews/<id>` (status update to READY)

## State management

Fermentation start times are tracked in memory (`_fermentation_start: dict[int, float]`).
On first observation of a brew, the monotonic clock time is recorded. On subsequent polls,
progress is computed as `elapsed / FERMENTATION_SECONDS * 100`. State is lost on restart —
intentional for a learning lab.

## OTEL

Span name: `"ferment brew"` (SpanKind INTERNAL — default).
Span attributes: `brew.style`, `brew.ingredient_type`, `fermentation.progress_pct`.
Span events: `fermentation.started` (first poll), `fermentation.complete` (transition to READY).

## What I learned building this

Span events as lifecycle markers, progress attributes for long-running operations,
and in-memory state management across polling cycles.
