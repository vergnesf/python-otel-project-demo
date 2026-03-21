# CLAUDE.md — ms-brewery

## What this service does

Flask **REST API** — manages brew orders in a PostgreSQL database. Exposes CRUD endpoints
for creating, reading, and updating brew records. Receives brew orders from `ms-brewcheck`
and serves brew data to `ms-brewmaster`.

## Tech stack

- **Flask** (intentional choice — synchronous, SQLAlchemy-compatible, no migration to FastAPI planned)
- `flask-sqlalchemy` — ORM for PostgreSQL
- `flasgger` — Swagger/OpenAPI docs auto-generated from docstrings
- `psycopg2-binary` — PostgreSQL driver
- `lib-models` — shared `BrewOrder`, `BrewStatus`, `BrewStyle`, `IngredientType` Pydantic models (editable install)
- `opentelemetry-distro` + `opentelemetry-exporter-otlp` — auto-instrumentation

## Entry point

`brewery/main.py` → `brewery/__init__.py` (`create_app()` factory pattern). Port **5000**.

## Key files

- `brewery/models.py` — SQLAlchemy ORM model (`BrewModel`, table `brews`)
- `brewery/schemas.py` — Pydantic schemas (`BrewCreate`, `Brew`)
- `brewery/crud.py` — DB operations
- `brewery/routes/brews.py` — Flask Blueprint with all endpoints

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/brews` | Create brew order |
| GET | `/brews` | List all brews |
| GET | `/brews/<id>` | Get one brew |
| PUT | `/brews/<id>` | Update brew status |
| GET | `/brews/status/<status>` | Filter brews by status |
| GET | `/health` | Health check |

## Key env vars

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `OTEL_SERVICE_NAME` | `ms-brewery` |
| `LOG_LEVEL` | Logging verbosity |

## What I learned building this

Flask app factory pattern, SQLAlchemy ORM with Flask integration, auto-generated
Swagger docs with Flasgger, and OTEL instrumentation of synchronous REST APIs.
