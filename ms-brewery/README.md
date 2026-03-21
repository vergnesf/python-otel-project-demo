# ms-brewery

> **Status:** `KEEPER` — Stable service. Expected to stay functional and tested.

Flask REST API that manages brew orders in a PostgreSQL database.

## Why I built this

To learn the Flask app factory pattern, SQLAlchemy ORM integration, auto-generated
Swagger docs with Flasgger, and OTEL instrumentation of synchronous REST APIs.

## Overview

- **Type**: REST API (Flask + SQLAlchemy)
- **Port**: 5000
- **Database**: PostgreSQL
- **Framework**: Flask (intentional — synchronous, SQLAlchemy-compatible, no migration to FastAPI planned)

## Running the Service

```bash
# With Docker (recommended)
docker-compose up ms-brewery

# Local development
cd ms-brewery/ && uv sync
uv run opentelemetry-instrument \
    --traces_exporter otlp \
    --metrics_exporter otlp \
    --service_name brewery \
    --exporter_otlp_endpoint http://localhost:4317 \
    python brewery/main.py
```

## Configuration

```bash
DATABASE_URL=postgresql://postgres:yourpassword@postgres:5432/mydatabase
HOST=0.0.0.0
PORT=5000
LOG_LEVEL=INFO
OTEL_SERVICE_NAME=brewery
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/brews` | Create brew order |
| GET | `/brews` | List all brews |
| GET | `/brews/<id>` | Get one brew |
| PUT | `/brews/<id>` | Update brew status |
| GET | `/brews/status/<status>` | Filter brews by status |
| GET | `/health` | Health check |

Swagger UI: `http://localhost:5000/apidocs/` _(requires full stack running with PostgreSQL)_

## Dependencies

- `flask` + `flask-sqlalchemy` — web framework + ORM
- `flasgger` — auto-generated Swagger/OpenAPI docs
- `psycopg2-binary` — PostgreSQL adapter
- `lib-models` — shared brewery domain models (IngredientType, BrewStatus, BrewStyle)

## Integration

Receives from ← `ms-brewcheck` (POST /brews)
Serves to → `ms-brewmaster` (GET /brews/status/registered)
Updated by → `ms-brewmaster` (PUT /brews/<id>)

## Observability

Auto-instrumented via `opentelemetry-instrument`. Logs → Loki, Metrics → Mimir, Traces → Tempo.

## Testing

```bash
uv run python -m pytest tests/ -v
uv run python -m ruff check brewery/ tests/
```
