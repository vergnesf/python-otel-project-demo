# Common Models

> **Status:** `KEEPER` — Stable library. Expected to stay functional and tested.

Shared Pydantic v2 business models used across all KEEPER services.

## Why I built this

To learn shared library patterns with UV editable installs, Pydantic v2 model design,
and how to avoid duplicating data contracts across Python microservices.

## Contents

| Model | Type | Fields |
|-------|------|--------|
| `WoodType` | Enum | OAK, MAPLE, BIRCH, ELM, PINE |
| `OrderStatus` | Enum | READY, SHIPPED, BLOCKED, CLOSED, UNKNOWN, REGISTERED |
| `Stock` | Pydantic model | `wood_type: WoodType`, `quantity: int` |
| `Order` | Pydantic model | `wood_type: WoodType`, `quantity: int` |
| `OrderTracking` | Pydantic model | `id`, `order_status`, `wood_type`, `quantity`, `date` |

All models include a `to_json()` method for Kafka serialization.

## Installation in other services

```toml
# pyproject.toml
dependencies = ["common-models"]

[tool.uv.sources]
common-models = { path = "../common-models", editable = true }
```

Then run `uv sync` to activate the editable install.

## Development

```bash
cd common-models/ && uv sync
uv run ruff check .
```

> No tests exist yet — smoke tests tracked in issue #17.
