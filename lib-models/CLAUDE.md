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
├── IngredientType (Enum)        — MALT, HOPS, YEAST, WHEAT, BARLEY
├── BrewStatus (Enum)            — REGISTERED, BREWING, READY, SHIPPED, BLOCKED, CLOSED, UNKNOWN
├── BrewStyle (Enum)             — LAGER, IPA, STOUT, WHEAT_BEER
├── IngredientStock              — ingredient_type: IngredientType, quantity: int
├── BrewOrder                    — ingredient_type: IngredientType, quantity: int, brew_style: BrewStyle
├── BrewTracking                 — id, brew_status, ingredient_type, quantity, brew_style, date
├── InsufficientIngredientError  — raised when ingredient stock is too low
└── IngredientNotFoundError      — raised when ingredient entry does not exist
```

Serialization uses Pydantic's `model_dump()` and `model_dump_json()` directly — no custom `to_json()` method.

## Adding new models

1. Edit `lib_models/models.py`
2. The editable install means all dependent services pick up changes immediately
3. Run `uv run ruff check .` before committing

## What I learned building this

Shared library patterns with UV editable installs, Pydantic v2 model design,
and how to avoid duplicating data contracts across microservices.
