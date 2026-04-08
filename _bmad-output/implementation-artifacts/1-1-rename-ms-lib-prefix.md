# Story 1-1: Rename Service Directories with ms- and lib- Prefixes

## Status
obsolete

> **Note (2026-04-08):** Story exécutée et mergée (commit `cdd2d16`, 2026-03-14). Obsolète car la refonte brewery-phase-1 a remplacé tous les services sawmill (`ms-customer`, `ms-order`, `ms-stock`, etc.) par le domaine brasserie (`ms-brewery`, `ms-cellar`, `ms-beerstock`, etc.). Les ACs ne correspondent plus à l'état réel du repo.

## Story
**As a** developer navigating the repository,
**I want** all microservice directories prefixed with `ms-` and shared libraries prefixed with `lib-`,
**so that** the repository structure immediately communicates the nature of each component (consistent with the existing `agent-` prefix convention).

## Acceptance Criteria
- [ ] AC1: All 7 KEEPER microservice directories renamed to `ms-<name>` (`ms-customer`, `ms-supplier`, `ms-order`, `ms-stock`, `ms-ordercheck`, `ms-suppliercheck`, `ms-ordermanagement`)
- [ ] AC2: Shared library directories renamed to `lib-models` and `lib-ai`; their internal Python module directories renamed to `lib_models` and `lib_ai`
- [ ] AC3: All Python imports updated (`from common_models` → `from lib_models`, `from common_ai` → `from lib_ai`)
- [ ] AC4: All Dockerfiles updated (COPY source paths, WORKDIR paths)
- [ ] AC5: `docker-compose/docker-compose-apps.yml` fully updated (service names, build paths, container names, OTEL_SERVICE_NAME, internal URLs, depends_on)
- [ ] AC6: `config/traefik/dynamic_conf.yml` internal service URLs updated (`http://order` → `http://ms-order`, `http://stock` → `http://ms-stock`)
- [ ] AC7: `Taskfile.yml` variables updated (PROJECTS, KEEPER_SERVICES, HEALTHCHECK_SERVICES)
- [ ] AC8: `CLAUDE.md` and `README.md` updated to reflect new directory names
- [ ] AC9: All pyproject.toml files updated (package names `common-models`→`lib-models`, `common-ai`→`lib-ai`, dependency paths)
- [ ] AC10: `task test` passes (test-lint + test-unit) with zero regressions

## Tasks / Subtasks

- [x] T1: Create branch `feat/rename-ms-lib-prefix`
  - [x] T1.1: `git checkout -b feat/rename-ms-lib-prefix`

- [x] T2: Rename microservice directories (git mv)
  - [x] T2.1: `git mv customer ms-customer`
  - [x] T2.2: `git mv supplier ms-supplier`
  - [x] T2.3: `git mv order ms-order`
  - [x] T2.4: `git mv stock ms-stock`
  - [x] T2.5: `git mv ordercheck ms-ordercheck`
  - [x] T2.6: `git mv suppliercheck ms-suppliercheck`
  - [x] T2.7: `git mv ordermanagement ms-ordermanagement`

- [x] T3: Rename shared library directories and internal modules
  - [x] T3.1: `git mv common-models lib-models`
  - [x] T3.2: `git mv lib-models/common_models lib-models/lib_models`
  - [x] T3.3: `git mv common-ai lib-ai`
  - [x] T3.4: `git mv lib-ai/common_ai lib-ai/lib_ai`
  - [x] T3.5: Removed stale .egg-info dirs

- [x] T4: Update pyproject.toml files
  - [x] T4.1: `lib-models/pyproject.toml` — `name = "lib-models"`
  - [x] T4.2: `lib-ai/pyproject.toml` — `name = "lib-ai"`
  - [x] T4.3: All 7 ms-* service pyproject.toml updated (deps + `[tool.uv.sources]` key)
  - [x] T4.4: All agent-* + benchmark pyproject.toml updated; uv.lock regenerated

- [x] T5: Update Python imports
  - [x] T5.1: `from common_models` → `from lib_models` (ms-* services)
  - [x] T5.2: `from common_ai` → `from lib_ai` (agent-* + benchmark)
  - [x] T5.3: No bare `import common_*` occurrences found

- [x] T6: Update Dockerfiles (12 files)
  - [x] T6.1–T6.7: ms-* Dockerfiles — COPY paths + WORKDIR updated
  - [x] T6.8–T6.12: agent-* Dockerfiles — `COPY lib-ai` updated

- [x] T7: Update docker-compose/docker-compose-apps.yml
  - [x] T7.1–T7.6: All service names, dockerfile paths, container_name, OTEL_SERVICE_NAME, internal URLs, depends_on updated

- [x] T8: Update config/traefik/dynamic_conf.yml
  - [x] T8.1: `http://ms-order:5000`
  - [x] T8.2: `http://ms-stock:5001`

- [x] T9: Update Taskfile.yml
  - [x] T9.1–T9.3: PROJECTS, KEEPER_SERVICES, HEALTHCHECK_SERVICES updated

- [x] T10: Update CLAUDE.md and README.md
  - [x] T10.1: CLAUDE.md fully updated
  - [x] T10.2: README.md project structure tree updated

- [x] T11: Run tests and validate
  - [x] T11.1: `task test-lint` ✓ (ruff clean, 2 import-sort auto-fixed)
  - [x] T11.2: `task test-unit` ✓ (16/16 smoke tests passed)
  - [x] T11.3: Committed — `cdd2d16`

## Dev Notes

**This is a pure refactoring story — no behavior changes.**

- No new business logic → no new unit tests to write (red-green-refactor doesn't apply to rename)
- Existing smoke tests (16 tests, 7 services) are the regression guard — they must pass 100%
- `task test-integration` will be skipped (requires running stack) — that's expected
- Python module names inside shared libs MUST be renamed: `common_models/` → `lib_models/`, `common_ai/` → `lib_ai/`. Without this, imports break.
- The inner Python package (e.g., `customer/customer/`) keeps its name — only the top-level dir gets the `ms-` prefix
- Dockerfiles use `context: ..` (project root), so COPY source paths are relative to project root
- uv editable installs use path source: `path = "../common-models"` — these must match the renamed dirs
- ordercheck Dockerfile uses `./common-models/` (relative, same as `/app/common-models/`) — treat consistently

## Dev Agent Record

### Implementation Plan
Implement tasks sequentially T1→T11. After T3 (renames), run a quick import check. After T5 (imports), run `uvx ruff check` to catch broken references. Full `task test` at T11.

### Debug Log
_empty_

### Completion Notes
- Pure refactoring — no behavior change, no new logic
- Stumbling block: `[tool.uv.sources]` key must match the dependency name (not the path); fixed after first lock failure
- Stale `.venv` dirs required manual cleanup after pyproject.toml renames
- Ruff auto-fixed 2 I001 import-sort issues in ms-customer and ms-supplier after lib_models became first-party

## File List
- `ms-customer/` (renamed from `customer/`) — Dockerfile, pyproject.toml, uv.lock, customer/*.py, tests/
- `ms-supplier/` (renamed from `supplier/`) — Dockerfile, pyproject.toml, uv.lock, supplier/*.py, tests/
- `ms-order/` (renamed from `order/`) — Dockerfile, pyproject.toml, uv.lock, order/*.py, tests/
- `ms-stock/` (renamed from `stock/`) — Dockerfile, pyproject.toml, uv.lock, stock/*.py, tests/
- `ms-ordercheck/` (renamed from `ordercheck/`) — Dockerfile, pyproject.toml, uv.lock, ordercheck/*.py, tests/
- `ms-suppliercheck/` (renamed from `suppliercheck/`) — Dockerfile, pyproject.toml, uv.lock
- `ms-ordermanagement/` (renamed from `ordermanagement/`) — Dockerfile, pyproject.toml, uv.lock, ordermanagement/*.py, tests/
- `lib-models/` (renamed from `common-models/`) — pyproject.toml; `lib_models/` (renamed from `common_models/`)
- `lib-ai/` (renamed from `common-ai/`) — pyproject.toml; `lib_ai/` (renamed from `common_ai/`)
- `agent-logs/Dockerfile`, `agent-logs/pyproject.toml`, `agent-logs/agent_logs/logs_analyzer.py`
- `agent-metrics/Dockerfile`, `agent-metrics/pyproject.toml`, `agent-metrics/agent_metrics/metrics_analyzer.py`
- `agent-orchestrator/Dockerfile`, `agent-orchestrator/pyproject.toml`, `agent-orchestrator/agent_orchestrator/orchestrator.py`, `agent-orchestrator/tests/test_benchmark_models.py`
- `agent-traces/Dockerfile`, `agent-traces/pyproject.toml`, `agent-traces/agent_traces/traces_analyzer.py`
- `agent-traduction/Dockerfile`, `agent-traduction/pyproject.toml`, `agent-traduction/agent_traduction/translation_service.py`
- `benchmark/pyproject.toml`, `benchmark/benchmark/main.py`
- `docker-compose/docker-compose-apps.yml`
- `config/traefik/dynamic_conf.yml`
- `Taskfile.yml`
- `CLAUDE.md`
- `README.md`

## Change Log
- 2026-03-14: Rename all KEEPER microservice dirs to ms-*, shared libs to lib-*, Python modules to lib_models/lib_ai. All imports, Dockerfiles, compose, Traefik, pyproject.toml, uv.lock, Taskfile, docs updated. 16 smoke tests passing.
