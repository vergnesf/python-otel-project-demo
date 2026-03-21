# CLAUDE.md — ms-cellar

## What this service does

Flask **REST API** — manages ingredient stock inventory in a PostgreSQL database.
Receives ingredient deliveries from `ms-ingredientcheck` and handles stock decreases
requested by `ms-brewmaster` when brews are fulfilled.

## Tech stack

- **Flask** (intentional choice — synchronous, SQLAlchemy-compatible, no migration to FastAPI planned)
- `flask-sqlalchemy` — ORM for PostgreSQL
- `flasgger` — Swagger/OpenAPI docs auto-generated from docstrings
- `psycopg2-binary` — PostgreSQL driver
- `lib-models` — shared `IngredientType`, `InsufficientIngredientError`, `IngredientNotFoundError` (editable install)
- `opentelemetry-distro` + `opentelemetry-exporter-otlp` — auto-instrumentation

## Entry point

`cellar/main.py` → `cellar/__init__.py` (`create_app()` factory pattern). Port **5001**.

## Key files

- `cellar/models.py` — SQLAlchemy ORM model (`IngredientStockModel`, table `ingredient_stocks`)
- `cellar/schemas.py` — Pydantic schemas (`IngredientCreate`, `Ingredient`, `IngredientDecrease`)
- `cellar/crud.py` — DB operations (raises typed `IngredientNotFoundError` / `InsufficientIngredientError`)
- `cellar/routes/cellar.py` — Flask Blueprint with all endpoints

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/ingredients` | Create or accumulate ingredient stock |
| GET | `/ingredients` | List all ingredient stocks |
| GET | `/ingredients/<ingredient_type>` | Get stock by ingredient type |
| POST | `/ingredients/decrease` | Decrease stock (called by ms-brewmaster) |
| GET | `/health` | Health check |

## Key env vars

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `OTEL_SERVICE_NAME` | `ms-cellar` |
| `LOG_LEVEL` | Logging verbosity |

## What I learned building this

Structuring two symmetric Flask APIs sharing a database, Flasgger integration,
and how REST and Kafka services appear differently in distributed traces.
Typed exception handling from lib-models replaces generic ValueError.
