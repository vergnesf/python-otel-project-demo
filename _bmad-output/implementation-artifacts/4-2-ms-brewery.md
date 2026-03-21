# Story: ms-order → ms-brewery (Issue #103)

**Status:** done
**Branch:** refactor/ms-brewery
**Milestone:** brewery-phase-1

## Summary

Rename and migrate `ms-order` Flask REST API to `ms-brewery` using the brewery domain models from `lib-models`.

## Acceptance Criteria

- [x] Directory renamed `ms-order` → `ms-brewery` (git mv, history preserved)
- [x] Python package renamed `order` → `brewery`
- [x] SQLAlchemy model: `Order` → `BrewModel`, table `orders` → `brews`
- [x] Fields: `wood_type`/`WoodType` → `ingredient_type`/`IngredientType`, `order_status`/`OrderStatus` → `brew_status`/`BrewStatus`, new `brew_style`/`BrewStyle`
- [x] Schemas: `OrderCreate` → `BrewCreate` (adds `brew_style`)
- [x] CRUD: all functions renamed to brew variants
- [x] Routes: `/orders` → `/brews`, `order_status` → `brew_status` field, Blueprint `orders_bp` → `brews_bp`
- [x] Health endpoint returns `"service": "brewery"`
- [x] `pyproject.toml`: `name = "brewery"`, entry `brewery/main.py`
- [x] Dockerfile: updated COPY paths and CMD
- [x] CLAUDE.md: fully updated
- [x] Tests: 12/12 passing with brewery domain data
- [x] Ruff: all checks passed

## Review Notes

No code review issues — straightforward domain rename with full test coverage.
