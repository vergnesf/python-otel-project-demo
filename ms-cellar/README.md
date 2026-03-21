# ms-cellar

> **Status:** `KEEPER` — Stable service. Expected to stay functional and tested.

Flask REST API that manages ingredient stock inventory in a PostgreSQL database.

## Why I built this

To learn how two symmetric Flask APIs can share a database, how Flasgger generates
Swagger docs automatically, and how REST and Kafka services appear differently in traces.

## Overview

- **Type**: REST API (Flask + SQLAlchemy)
- **Port**: 5001
- **Database**: PostgreSQL
- **Framework**: Flask (intentional — synchronous, SQLAlchemy-compatible, no migration to FastAPI planned)

## Running the Service

```bash
# With Docker (recommended)
docker-compose up ms-cellar

# Local development
cd ms-cellar/ && uv sync
uv run opentelemetry-instrument \
    --traces_exporter otlp \
    --metrics_exporter otlp \
    --service_name cellar \
    --exporter_otlp_endpoint http://localhost:4317 \
    python cellar/main.py
```

## Configuration

```bash
DATABASE_URL=postgresql://postgres:yourpassword@postgres:5432/mydatabase
HOST=0.0.0.0
PORT=5001
LOG_LEVEL=INFO
OTEL_SERVICE_NAME=cellar
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/ingredients` | Create or accumulate ingredient stock |
| GET | `/ingredients` | List all ingredient stocks |
| GET | `/ingredients/<ingredient_type>` | Get stock by ingredient type |
| POST | `/ingredients/decrease` | Decrease stock (called by ms-brewmaster) |
| GET | `/health` | Health check |

Swagger UI: `http://localhost:5001/apidocs/` _(requires full stack running with PostgreSQL)_

## Dependencies

- `flask` + `flask-sqlalchemy` — web framework + ORM
- `flasgger` — auto-generated Swagger/OpenAPI docs
- `psycopg2-binary` — PostgreSQL adapter
- `lib-models` — shared brewery domain models (IngredientType, typed exceptions)

## Integration

Receives from ← `ms-ingredientcheck` (POST /ingredients)
Updated by → `ms-brewmaster` (POST /ingredients/decrease)

## Observability

Auto-instrumented via `opentelemetry-instrument`. Logs → Loki, Metrics → Mimir, Traces → Tempo.

## Testing

```bash
uv run python -m pytest tests/ -v
uv run python -m ruff check cellar/ tests/
```
