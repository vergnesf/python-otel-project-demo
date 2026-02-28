# Stock Service

> **Status:** `KEEPER` — Stable service. Expected to stay functional and tested.

Flask REST API that manages wood stock inventory in a PostgreSQL database.

## Why I built this

To learn how two symmetric Flask APIs can share a database, how Flasgger generates
Swagger docs automatically, and how REST and Kafka services appear differently in traces.

## 📋 Overview

- **Type**: REST API (Flask + SQLAlchemy)
- **Port**: 5001
- **Database**: PostgreSQL
- **Framework**: Flask (intentional — synchronous, SQLAlchemy-compatible, no migration to FastAPI planned)

## 🚀 Running the Service

```bash
# With Docker (recommended)
docker-compose up stock

# Local development
cd stock/ && uv sync
uv run opentelemetry-instrument \
    --traces_exporter otlp \
    --metrics_exporter otlp \
    --service_name stock \
    --exporter_otlp_endpoint http://localhost:4317 \
    python -m stock.main
```

## 🔧 Configuration

```bash
DATABASE_URL=postgresql://postgres:yourpassword@postgres:5432/mydatabase
HOST=0.0.0.0
PORT=5001
LOG_LEVEL=INFO
OTEL_SERVICE_NAME=stock
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

## 📊 API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/stocks` | Create stock entry |
| GET | `/stocks` | List all stock |
| GET | `/stocks/<wood_type>` | Get stock by wood type |
| PUT | `/stocks/<wood_type>` | Update quantity |
| POST | `/stocks/decrease` | Decrease stock (called by ordermanagement) |

Swagger UI: `http://localhost:5001/apidocs/`

## 📦 Dependencies

- `flask` + `flask-sqlalchemy` — web framework + ORM
- `flasgger` — auto-generated Swagger/OpenAPI docs
- `psycopg2-binary` — PostgreSQL adapter
- `common-models` — shared business models

## 🔄 Integration

Receives from ← `suppliercheck` (POST /stocks)
Stock decreased by → `ordermanagement` (POST /stocks/decrease)

## 📈 Observability

Auto-instrumented via `opentelemetry-instrument`. Logs → Loki, Metrics → Mimir, Traces → Tempo.

## 🧪 Testing

```bash
uv run pytest
uv run pytest --cov=stock --cov-report=html
```
