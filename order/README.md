# Order Service

> **Status:** `KEEPER` — Stable service. Expected to stay functional and tested.

Flask REST API that manages customer orders in a PostgreSQL database.

## Why I built this

To learn the Flask app factory pattern, SQLAlchemy ORM integration, auto-generated
Swagger docs with Flasgger, and OTEL instrumentation of synchronous REST APIs.

## 📋 Overview

- **Type**: REST API (Flask + SQLAlchemy)
- **Port**: 5000
- **Database**: PostgreSQL
- **Framework**: Flask (intentional — synchronous, SQLAlchemy-compatible, no migration to FastAPI planned)

## 🚀 Running the Service

```bash
# With Docker (recommended)
docker-compose up order

# Local development
cd order/ && uv sync
uv run opentelemetry-instrument \
    --traces_exporter otlp \
    --metrics_exporter otlp \
    --service_name order \
    --exporter_otlp_endpoint http://localhost:4317 \
    python -m order.main
```

## 🔧 Configuration

```bash
DATABASE_URL=postgresql://postgres:yourpassword@postgres:5432/mydatabase
HOST=0.0.0.0
PORT=5000
LOG_LEVEL=INFO
OTEL_SERVICE_NAME=order
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

## 📊 API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/orders` | Create order |
| GET | `/orders` | List all orders |
| GET | `/orders/<id>` | Get one order |
| PUT | `/orders/<id>` | Update order status |
| GET | `/orders/status/registered` | Filter registered orders |
| GET | `/health` | Health check |

Swagger UI: `http://localhost:5000/apidocs/`

## 📦 Dependencies

- `flask` + `flask-sqlalchemy` — web framework + ORM
- `flasgger` — auto-generated Swagger/OpenAPI docs
- `psycopg2-binary` — PostgreSQL adapter
- `common-models` — shared business models

## 🔄 Integration

Receives from ← `ordercheck` (POST /orders)
Serves to → `ordermanagement` (GET /orders/status/registered)
Updated by → `ordermanagement` (PUT /orders/<id>)

## 📈 Observability

Auto-instrumented via `opentelemetry-instrument`. Logs → Loki, Metrics → Mimir, Traces → Tempo.

## 🧪 Testing

```bash
uv run pytest
uv run pytest --cov=order --cov-report=html
```
