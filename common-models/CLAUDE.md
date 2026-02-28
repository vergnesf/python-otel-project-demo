# CLAUDE.md — common-models

## What this library does

Shared **Pydantic v2 models** used across all KEEPER business services.
Installed as an editable local package (`path = "../common-models", editable = true`)
in every service that needs it.

## Tech stack

- `pydantic>=2.12.4` — data models and validation
- No framework, no HTTP, no Kafka — pure data definitions

## Models

```
common_models/models.py
├── WoodType (Enum)     — OAK, MAPLE, BIRCH, ELM, PINE
├── OrderStatus (Enum)  — READY, SHIPPED, BLOCKED, CLOSED, UNKNOWN, REGISTERED
├── Stock               — wood_type: WoodType, quantity: int
├── Order               — wood_type: WoodType, quantity: int
└── OrderTracking       — id, order_status, wood_type, quantity, date
```

All models include a `to_json()` method for Kafka serialization.

## Adding new models

1. Edit `common_models/models.py`
2. The editable install means all dependent services pick up changes immediately
3. Run `uv run ruff check .` before committing

## What I learned building this

Shared library patterns with UV editable installs, Pydantic v2 model design,
and how to avoid duplicating data contracts across microservices.
