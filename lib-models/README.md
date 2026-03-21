# Common Models

> **Status:** `KEEPER` — Stable library. Expected to stay functional and tested.

Shared Pydantic v2 business models used across all KEEPER services.

## Why I built this

To learn shared library patterns with UV editable installs, Pydantic v2 model design,
and how to avoid duplicating data contracts across Python microservices.

## Contents

| Model | Type | Fields |
|-------|------|--------|
| `IngredientType` | Enum | MALT, HOPS, YEAST, WHEAT, BARLEY |
| `BrewStatus` | Enum | REGISTERED, BREWING, READY, SHIPPED, BLOCKED, CLOSED, UNKNOWN |
| `BrewStyle` | Enum | LAGER, IPA, STOUT, WHEAT_BEER |
| `IngredientStock` | Pydantic model | `ingredient_type: IngredientType`, `quantity: int` |
| `BrewOrder` | Pydantic model | `ingredient_type: IngredientType`, `quantity: int`, `brew_style: BrewStyle` |
| `BrewTracking` | Pydantic model | `id`, `brew_status`, `ingredient_type`, `quantity`, `brew_style`, `date` |

Serialization uses Pydantic's `model_dump()` and `model_dump_json()` directly.

## Installation in other services

```toml
# pyproject.toml
dependencies = ["lib-models"]

[tool.uv.sources]
lib-models = { path = "../lib-models", editable = true }
```

Then run `uv sync` to activate the editable install.

## Development

```bash
cd lib-models/ && uv sync
uv run ruff check .
uv run pytest
```
