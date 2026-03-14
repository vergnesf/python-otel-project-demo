# Story 1-1: Rename Service Directories with ms- and lib- Prefixes

## Status
in-progress

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

- [ ] T1: Create branch `feat/rename-ms-lib-prefix`
  - [ ] T1.1: `git checkout -b feat/rename-ms-lib-prefix`

- [ ] T2: Rename microservice directories (git mv)
  - [ ] T2.1: `git mv customer ms-customer`
  - [ ] T2.2: `git mv supplier ms-supplier`
  - [ ] T2.3: `git mv order ms-order`
  - [ ] T2.4: `git mv stock ms-stock`
  - [ ] T2.5: `git mv ordercheck ms-ordercheck`
  - [ ] T2.6: `git mv suppliercheck ms-suppliercheck`
  - [ ] T2.7: `git mv ordermanagement ms-ordermanagement`

- [ ] T3: Rename shared library directories and internal modules
  - [ ] T3.1: `git mv common-models lib-models`
  - [ ] T3.2: `git mv lib-models/common_models lib-models/lib_models` (rename Python package dir)
  - [ ] T3.3: `git mv common-ai lib-ai`
  - [ ] T3.4: `git mv lib-ai/common_ai lib-ai/lib_ai` (rename Python package dir)
  - [ ] T3.5: Remove stale .egg-info dirs (`lib-models/common_models.egg-info`, `lib-ai/common_ai.egg-info`) if present

- [ ] T4: Update pyproject.toml files
  - [ ] T4.1: `lib-models/pyproject.toml` — set `name = "lib-models"`, update `packages` if any
  - [ ] T4.2: `lib-ai/pyproject.toml` — set `name = "lib-ai"`, update `packages` if any
  - [ ] T4.3: Update all 7 ms-* service pyproject.toml: `"common-models"` → `"lib-models"` in dependencies; `path = "../common-models"` → `path = "../lib-models"`
  - [ ] T4.4: Update all agent-* + benchmark pyproject.toml: `"common-ai"` → `"lib-ai"`; `path = "../common-ai"` → `path = "../lib-ai"`

- [ ] T5: Update Python imports
  - [ ] T5.1: Replace `from common_models` → `from lib_models` in all .py files (ms-* services)
  - [ ] T5.2: Replace `from common_ai` → `from lib_ai` in all .py files (agent-* and benchmark)
  - [ ] T5.3: Update any `import common_models` / `import common_ai` occurrences

- [ ] T6: Update Dockerfiles (12 files — all ms-* + agent-* using shared libs)
  - [ ] T6.1: ms-customer/Dockerfile — COPY paths, WORKDIR
  - [ ] T6.2: ms-supplier/Dockerfile — COPY paths, WORKDIR
  - [ ] T6.3: ms-order/Dockerfile — COPY paths, WORKDIR
  - [ ] T6.4: ms-stock/Dockerfile — COPY paths, WORKDIR
  - [ ] T6.5: ms-ordercheck/Dockerfile — COPY paths, WORKDIR
  - [ ] T6.6: ms-suppliercheck/Dockerfile — COPY paths, WORKDIR
  - [ ] T6.7: ms-ordermanagement/Dockerfile — COPY paths, WORKDIR
  - [ ] T6.8: agent-logs/Dockerfile — `COPY common-ai` → `COPY lib-ai`
  - [ ] T6.9: agent-metrics/Dockerfile — same
  - [ ] T6.10: agent-orchestrator/Dockerfile — same
  - [ ] T6.11: agent-traces/Dockerfile — same
  - [ ] T6.12: agent-traduction/Dockerfile — same

- [ ] T7: Update docker-compose/docker-compose-apps.yml
  - [ ] T7.1: Rename all 7 service keys (`customer:` → `ms-customer:`, etc.)
  - [ ] T7.2: Update `dockerfile:` paths (`customer/Dockerfile` → `ms-customer/Dockerfile`, etc.)
  - [ ] T7.3: Update `container_name:` values
  - [ ] T7.4: Update `OTEL_SERVICE_NAME:` values
  - [ ] T7.5: Update internal URL env vars (`http://order:5000` → `http://ms-order:5000`, `http://stock:5001` → `http://ms-stock:5001`)
  - [ ] T7.6: Update `depends_on:` entries

- [ ] T8: Update config/traefik/dynamic_conf.yml
  - [ ] T8.1: `url: http://order:5000` → `url: http://ms-order:5000`
  - [ ] T8.2: `url: http://stock:5001` → `url: http://ms-stock:5001`

- [ ] T9: Update Taskfile.yml
  - [ ] T9.1: Update PROJECTS var with new ms-* and lib-* names
  - [ ] T9.2: Update KEEPER_SERVICES var (7 ms-* names)
  - [ ] T9.3: Update HEALTHCHECK_SERVICES var (`order stock` → `ms-order ms-stock`)

- [ ] T10: Update CLAUDE.md and README.md
  - [ ] T10.1: CLAUDE.md — service table, KEEPER_SERVICES note, command examples
  - [ ] T10.2: README.md — project structure tree, any service name references

- [ ] T11: Run tests and validate
  - [ ] T11.1: `task test-lint` passes on renamed KEEPER_SERVICES
  - [ ] T11.2: `task test-unit` passes (16 smoke tests across 7 ms-* services)
  - [ ] T11.3: Commit all changes

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
_empty_

## File List
_To be filled during implementation_

## Change Log
_To be filled during implementation_
