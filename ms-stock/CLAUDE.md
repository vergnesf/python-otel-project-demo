# CLAUDE.md — stock

## What this service does

Flask **REST API** — manages wood stock inventory in a PostgreSQL database.
Receives stock entries from `suppliercheck` and handles stock decreases
requested by `ordermanagement` when orders are fulfilled.

## Tech stack

- **Flask** (intentional choice — synchronous, SQLAlchemy-compatible, no migration to FastAPI planned)
- `flask-sqlalchemy` — ORM for PostgreSQL
- `flasgger` — Swagger/OpenAPI docs auto-generated from docstrings
- `psycopg2-binary` — PostgreSQL driver
- `common-models` — shared `Stock` and `WoodType` Pydantic models (editable install)
- `opentelemetry-distro` + `opentelemetry-exporter-otlp` — auto-instrumentation

## Entry point

`stock/main.py` → `stock/__init__.py` (`create_app()` factory pattern). Port **5001**.

## Key files

- `stock/models.py` — SQLAlchemy ORM models
- `stock/schemas.py` — Pydantic schemas
- `stock/crud.py` — DB operations
- `stock/routes/stocks.py` — Flask Blueprint with all endpoints

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/stocks` | Create stock entry |
| GET | `/stocks` | List all stock |
| GET | `/stocks/<wood_type>` | Get stock by wood type |
| PUT | `/stocks/<wood_type>` | Update quantity |
| POST | `/stocks/decrease` | Decrease stock (called by ordermanagement) |

## Key env vars

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `OTEL_SERVICE_NAME` | `stock` |
| `LOG_LEVEL` | Logging verbosity |

## What I learned building this

Structuring two symmetric Flask APIs sharing a database, Flasgger integration,
and how REST and Kafka services appear differently in distributed traces.
