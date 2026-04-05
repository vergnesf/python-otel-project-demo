# ms-fermentation

Background worker — simulates fermentation timing for brews in progress.

## Overview

Polls `ms-brewery` for brews in `BREWING` status and transitions them to `READY` once
the configured fermentation time elapses. Introduces OTEL span events and progress attributes.

```
ms-brewery (BREWING) → polls → ms-fermentation → PUT ms-brewery (READY)
```

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `API_URL_BREWS` | `http://brewery:5000` | Brewery API base URL |
| `FERMENTATION_SECONDS` | `30` | Simulated fermentation time per brew |
| `INTERVAL_SECONDS` | `10` | Polling interval in seconds |
| `ERROR_RATE` | `0.1` | Fraction of completions that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `ms-fermentation` | Telemetry service name |

## OTEL

Span name: `"ferment brew"` (SpanKind INTERNAL).

Unique patterns in this service:
- **Span events**: `fermentation.started` on first observation, `fermentation.complete` on transition
- **Progress attribute**: `fermentation.progress_pct` updated each polling cycle
