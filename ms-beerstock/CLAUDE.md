# CLAUDE.md — ms-beerstock

## What this service does

Flask **REST API** — manages finished beer stock inventory in a PostgreSQL database.
Output counterpart to `ms-cellar` (which tracks input ingredients). Receives finished
beer from `ms-brewery` when brews are approved, and decreases stock when orders ship.

## Tech stack

- **Flask** (intentional choice — synchronous, SQLAlchemy-compatible, no migration to FastAPI planned)
- `flask-sqlalchemy` — ORM for PostgreSQL
- `flasgger` — Swagger/OpenAPI docs auto-generated from docstrings
- `psycopg2-binary` — PostgreSQL driver
- `lib-models` — shared `BrewStyle`, `BeerStock`, `InsufficientBeerStockError` (editable install)
- `opentelemetry-distro` + `opentelemetry-exporter-otlp` — auto-instrumentation

## Entry point

`beerstock/main.py` → `beerstock/__init__.py` (`create_app()` factory pattern). Port **5002**.

## Key files

- `beerstock/models.py` — SQLAlchemy ORM model (`BeerStockModel`, table `beer_stocks`)
- `beerstock/schemas.py` — Pydantic schemas (`BeerStockCreate`, `BeerStockResponse`, `BeerStockShip`)
- `beerstock/crud.py` — DB operations (raises `InsufficientBeerStockError` on insufficient stock)
- `beerstock/routes/beerstock.py` — Flask Blueprint with all endpoints

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/beerstock` | Add finished beer stock (accumulates per style) |
| GET | `/beerstock` | List all beer stocks |
| GET | `/beerstock/<brew_style>` | Get stock by brew style |
| POST | `/beerstock/ship` | Decrease stock (called by ms-dispatch) |
| GET | `/health` | Health check |

## Key env vars

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `OTEL_SERVICE_NAME` | `ms-beerstock` |
| `LOG_LEVEL` | Logging verbosity |

## OTEL metric

`beerstock.http.duration` (Histogram, unit=s) — HTTP request duration per endpoint,
attributes: `http.method`, `http.route`, `http.status_code`.

## What I learned building this

Second symmetric Flask API — reinforces comparison against ms-cellar in Grafana dashboards.
`InsufficientBeerStockError` from lib-models maps both "not found" and "insufficient" cases to 400.
