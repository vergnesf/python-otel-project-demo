# CLAUDE.md — order

## What this service does

Flask **REST API** — manages orders in a PostgreSQL database. Exposes CRUD endpoints
for creating, reading, and updating order records. Receives orders from `ordercheck`
and serves order data to `ordermanagement`.

## Tech stack

- **Flask** (intentional choice — synchronous, SQLAlchemy-compatible, no migration to FastAPI planned)
- `flask-sqlalchemy` — ORM for PostgreSQL
- `flasgger` — Swagger/OpenAPI docs auto-generated from docstrings
- `psycopg2-binary` — PostgreSQL driver
- `common-models` — shared `Order` and `WoodType` Pydantic models (editable install)
- `opentelemetry-distro` + `opentelemetry-exporter-otlp` — auto-instrumentation

## Entry point

`order/main.py` → `order/__init__.py` (`create_app()` factory pattern). Port **5000**.

## Key files

- `order/models.py` — SQLAlchemy ORM models
- `order/schemas.py` — Pydantic schemas
- `order/crud.py` — DB operations
- `order/routes/orders.py` — Flask Blueprint with all endpoints

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/orders` | Create order |
| GET | `/orders` | List all orders |
| GET | `/orders/<id>` | Get one order |
| PUT | `/orders/<id>` | Update order status |
| GET | `/orders/status/registered` | Filter registered orders |
| GET | `/health` | Health check |

## Key env vars

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `OTEL_SERVICE_NAME` | `order` |
| `LOG_LEVEL` | Logging verbosity |

## What I learned building this

Flask app factory pattern, SQLAlchemy ORM with Flask integration, auto-generated
Swagger docs with Flasgger, and OTEL instrumentation of synchronous REST APIs.
