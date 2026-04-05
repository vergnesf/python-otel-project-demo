# ms-beerstock

Flask REST API — manages finished beer stock inventory in a PostgreSQL database.

## Overview

Output counterpart to `ms-cellar` (which tracks input ingredients). Receives finished beer
from `ms-brewery` when brews are approved, and ships stock when orders are dispatched.

```
ms-brewery (APPROVED) → POST /beerstock      (stock added)
ms-dispatch           → POST /beerstock/ship (stock shipped)
```

## Key env vars

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `OTEL_SERVICE_NAME` | `ms-beerstock` |
| `LOG_LEVEL` | Logging verbosity |

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/beerstock` | Add finished beer stock (accumulates per style) |
| GET | `/beerstock` | List all beer stocks |
| GET | `/beerstock/<brew_style>` | Get stock by brew style |
| POST | `/beerstock/ship` | Decrease stock when an order ships |
| GET | `/health` | Health check |

## OTEL

`beerstock.http.duration` (Histogram, unit=s) — HTTP request duration per endpoint,
attributes: `http.method`, `http.route`, `http.status_code`.
