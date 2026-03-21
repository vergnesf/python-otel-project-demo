# Story: ms-stock → ms-cellar (Issue #104)

**Status:** done
**Branch:** refactor/ms-cellar
**Milestone:** brewery-phase-1

## Summary

Rename and migrate `ms-stock` Flask REST API to `ms-cellar` using the brewery domain models from `lib-models`.

## Acceptance Criteria

- [x] Directory renamed `ms-stock` → `ms-cellar` (git mv, history preserved)
- [x] Python package renamed `stock` → `cellar`
- [x] SQLAlchemy model: `Stock` → `IngredientStockModel`, table `stocks` → `ingredient_stocks`
- [x] Fields: `wood_type`/`WoodType` → `ingredient_type`/`IngredientType` (PK preserved)
- [x] Schemas: `StockCreate/StockDecrease` → `IngredientCreate/IngredientDecrease`
- [x] CRUD: typed `IngredientNotFoundError` / `InsufficientIngredientError` replace generic `ValueError`
- [x] Routes: `/stocks` → `/ingredients`, Blueprint `stocks_bp` → `cellar_bp`, invalid type → 400
- [x] Health endpoint returns `"service": "cellar"`
- [x] `pyproject.toml`: `name = "cellar"`, entry `cellar/main.py`
- [x] Dockerfile: updated COPY paths and CMD
- [x] CLAUDE.md + README: fully updated
- [x] Tests: 14/14 passing with brewery domain data
- [x] Ruff: all checks passed

## Review Notes

Pending adversarial code review.
