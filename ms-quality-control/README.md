# ms-quality-control

Kafka consumer — performs quality control on finished brews.

## Overview

Consumes the `brews-ready` topic (published by `ms-brewery` when a brew transitions to `READY`)
and updates brew status to `APPROVED` or `REJECTED` via the Brewery REST API.

```
ms-brewery (READY) → [brews-ready] → ms-quality-control → PUT ms-brewery (APPROVED | REJECTED)
```

## Key env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | required | Kafka broker address |
| `API_URL` | `http://brewery:5000` | Brewery API base URL |
| `REJECT_RATE` | `0.1` | Fraction of brews rejected (0.0–1.0) |
| `ERROR_RATE` | `0.1` | Fraction of messages that fail (0.0–1.0) |
| `OTEL_SERVICE_NAME` | `ms-quality-control` | Telemetry service name |

## OTEL

Span name: `"process brews-ready"` (SpanKind.CONSUMER).

Unique patterns in this service:
- **Span links**: W3C trace context from Kafka headers links consumer span to producer span
- **Binary outcome attributes**: `quality.check.passed` (bool), `quality.reject_reason` (on reject)
- **Metrics**: `brews.quality_checked`, `brews.quality_rejected`, `brews.quality_errors`
