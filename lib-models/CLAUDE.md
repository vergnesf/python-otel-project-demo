# CLAUDE.md — lib-models

## What this library does

Shared **Pydantic v2 models** used across all KEEPER business services.
Installed as an editable local package (`path = "../lib-models", editable = true`)
in every service that needs it.

## Tech stack

- `pydantic>=2.12.4` — data models and validation
- No framework, no HTTP, no Kafka — pure data definitions

## Models

```
lib_models/models.py
├── WoodType (Enum)          — OAK, MAPLE, BIRCH, ELM, PINE
├── OrderStatus (Enum)       — READY, SHIPPED, BLOCKED, CLOSED, UNKNOWN, REGISTERED
├── Stock                    — wood_type: WoodType, quantity: int
├── Order                    — wood_type: WoodType, quantity: int
├── OrderTracking            — id, order_status, wood_type, quantity, date
├── InsufficientStockError   — raised when stock is too low
└── StockNotFoundError       — raised when stock entry does not exist
```

Serialization uses Pydantic's `model_dump()` and `model_dump_json()` directly — no custom `to_json()` method.

## Adding new models

1. Edit `lib_models/models.py`
2. The editable install means all dependent services pick up changes immediately
3. Run `uv run ruff check .` before committing

## What I learned building this

Shared library patterns with UV editable installs, Pydantic v2 model design,
and how to avoid duplicating data contracts across microservices.
