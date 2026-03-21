# Story 4-1: Replace Sawmill Domain with Brewery Domain Models in lib-models

## Status
done

## Story
**As a** developer working on the brewery-phase-1 refonte,
**I want** `lib-models` to expose brewery-domain Pydantic models (`IngredientType`, `BrewStatus`, `BrewStyle`, `BrewOrder`, `IngredientStock`, `BrewTracking`) replacing the sawmill domain (`WoodType`, `OrderStatus`, `Stock`, `Order`, `OrderTracking`),
**so that** all downstream KEEPER services (#98–#104) can depend on correct, brewery-named contracts.

## Acceptance Criteria
- [x] AC1: All old class names (`WoodType`, `OrderStatus`, `Stock`, `Order`, `OrderTracking`, `InsufficientStockError`, `StockNotFoundError`) removed from `lib_models/models.py`
- [x] AC2: New classes (`IngredientType`, `BrewStatus`, `BrewStyle`, `IngredientStock`, `BrewOrder`, `BrewTracking`, `InsufficientIngredientError`, `IngredientNotFoundError`) added and correctly exported via `__init__.py`
- [x] AC3: `lib-models/tests/test_models.py` fully rewritten — all tests pass with new model names and fields
- [x] AC4: No references to `wood_type`, `order_status`, `WoodType`, `OrderStatus` remain in `lib-models/`
- [x] AC5: `uv run pytest` passes in `lib-models/`

## Tasks / Subtasks

- [x] T1: Create branch `refactor/lib-models-brewery`
  - [x] T1.1: `git checkout main && git pull`
  - [x] T1.2: `git checkout -b refactor/lib-models-brewery`

- [x] T2: Rewrite `lib_models/models.py` with brewery domain
  - [x] T2.1: Replace `WoodType` → `IngredientType` (MALT, HOPS, YEAST, WHEAT, BARLEY)
  - [x] T2.2: Replace `OrderStatus` → `BrewStatus` (REGISTERED, BREWING, READY, SHIPPED, BLOCKED, CLOSED, UNKNOWN)
  - [x] T2.3: Add `BrewStyle` (LAGER, IPA, STOUT, WHEAT_BEER)
  - [x] T2.4: Replace `Stock` → `IngredientStock` (ingredient_type, quantity)
  - [x] T2.5: Replace `Order` → `BrewOrder` (ingredient_type, quantity, brew_style)
  - [x] T2.6: Replace `OrderTracking` → `BrewTracking` (id, brew_status, ingredient_type, quantity, brew_style, date)
  - [x] T2.7: Replace `InsufficientStockError` → `InsufficientIngredientError`
  - [x] T2.8: Replace `StockNotFoundError` → `IngredientNotFoundError`

- [x] T3: Update `lib_models/__init__.py` exports
  - [x] T3.1: Remove all old class exports
  - [x] T3.2: Export all new classes

- [x] T4: Rewrite `lib-models/tests/test_models.py`
  - [x] T4.1: Remove all sawmill tests (WoodType, OrderStatus, Stock, Order, OrderTracking)
  - [x] T4.2: Write tests for `IngredientType` (all 5 values, invalid raises)
  - [x] T4.3: Write tests for `BrewStatus` (all 7 values including BREWING, invalid raises)
  - [x] T4.4: Write tests for `BrewStyle` (all 4 values, invalid raises)
  - [x] T4.5: Write tests for `IngredientStock` (instantiation, validation, JSON round-trip)
  - [x] T4.6: Write tests for `BrewOrder` (instantiation, brew_style field, validation, JSON round-trip)
  - [x] T4.7: Write tests for `BrewTracking` (instantiation, all fields, JSON round-trip)
  - [x] T4.8: Write tests for `InsufficientIngredientError` and `IngredientNotFoundError`

- [x] T5: Run tests and validate
  - [x] T5.1: `uv run pytest` in `lib-models/` — 35/35 passed
  - [x] T5.2: `uv run ruff check` in lib-models/ — clean

## Dev Notes

**This is a pure domain rename — no behavior change, no new business logic.**

- `BrewTracking` gains one new field vs `OrderTracking`: `brew_style: BrewStyle`
- `BrewOrder` gains one new field vs `Order`: `brew_style: BrewStyle`
- `BrewStatus` gains one new value vs `OrderStatus`: `BREWING`
- Downstream services will break at import time until they are updated (#98–#104) — that's expected and fine
- Run `uv run pytest` from inside `lib-models/` directory (uses local venv)
- Tests use pattern: `from lib_models.models import ...`
- CLAUDE.md for lib-models will need update in #111 (done there, not here)

## Dev Agent Record

### Implementation Plan
T1 (branch) → T2 (rewrite models.py) → T3 (update __init__.py) → T4 (rewrite tests) → T5 (validate).

### Debug Log
_empty_

### Completion Notes
- Pure domain rename — no behavior change, no new business logic
- `BrewOrder` and `BrewTracking` gain one new field each vs old models: `brew_style: BrewStyle`
- `BrewStatus` gains new `BREWING` intermediate status vs old `OrderStatus`
- 35 tests written (29 model tests + 6 existing log_formatter tests) — all passing
- Ruff clean

## File List
- `lib-models/lib_models/models.py`
- `lib-models/lib_models/__init__.py`
- `lib-models/tests/test_models.py`
- `lib-models/CLAUDE.md`
- `lib-models/README.md`
- `_bmad-output/implementation-artifacts/4-1-lib-models-brewery.md`

## Change Log
- 2026-03-21: Replace sawmill domain with brewery domain in lib-models. New models: IngredientType, BrewStatus, BrewStyle, IngredientStock, BrewOrder, BrewTracking, InsufficientIngredientError, IngredientNotFoundError. 35 tests passing.
