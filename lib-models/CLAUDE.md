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
├── BrewStatus (Enum)            — REGISTERED, BREWING, READY, APPROVED, REJECTED, SHIPPED, BLOCKED, CLOSED, UNKNOWN
├── BrewStyle (Enum)             — LAGER, IPA, STOUT, WHEAT_BEER
├── IngredientStock              — ingredient_type: IngredientType, quantity: PositiveInt (gt=0)
├── BrewOrder                    — ingredient_type: IngredientType, quantity: PositiveInt (gt=0), brew_style: BrewStyle
├── BrewTracking                 — id, brew_status, ingredient_type, quantity: PositiveInt (gt=0), brew_style, date
├── BeerStock                    — brew_style: BrewStyle, quantity: int
├── BeerOrder                    — brew_style: BrewStyle, quantity: PositiveInt (gt=0), retailer_name: str
├── InsufficientIngredientError  — raised when stock is too low; carries ingredient_type, requested, available
├── IngredientNotFoundError      — raised when ingredient entry does not exist; carries ingredient_type
└── InsufficientBeerStockError   — raised when beer stock is too low or missing; carries brew_style, requested, available
```

> **Note Phase 2:** `BrewTracking` sert à la fois de modèle de réponse API Flask et de modèle de lecture dans `ms-brewmaster`.
> Si Phase 2 ajoute des champs riches (`fermentation_start`, `quality_result`…), envisager de séparer en `BrewReadModel` vs `BrewSummary`.

Serialization uses Pydantic's `model_dump()` and `model_dump_json()` directly — no custom `to_json()` method.

## Adding new models

1. Edit `lib_models/models.py`
2. The editable install means all dependent services pick up changes immediately
3. Run `uv run ruff check .` before committing

## What I learned building this

Shared library patterns with UV editable installs, Pydantic v2 model design,
and how to avoid duplicating data contracts across microservices.
