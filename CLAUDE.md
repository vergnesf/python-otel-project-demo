# CLAUDE.md — python-otel-project-demo

## Project Nature

Personal **learning lab**, not a production app. Simplicity over engineering.
Each service exists to learn a specific Python/OTEL/infra concept.

## Architecture

Two-layer model:
- **Business layer (KEEPER)** — generates activity and OTEL telemetry → Grafana
- **Agent layer** — reads observability data via MCP Grafana (future / in progress)

## KEEPER Services

| Service | Type | Framework |
|---------|------|-----------|
| `ms-brewer` | Kafka producer | none |
| `ms-supplier` | Kafka producer | none |
| `ms-retailer` | Kafka producer | none |
| `ms-brewcheck` | Kafka consumer | none |
| `ms-ingredientcheck` | Kafka consumer | none |
| `ms-quality-control` | Kafka consumer | none |
| `ms-dispatch` | Kafka consumer | none |
| `ms-brewmaster` | Background worker | none |
| `ms-fermentation` | Background worker | none |
| `ms-brewery` | REST API + DB | Flask + SQLAlchemy |
| `ms-cellar` | REST API + DB | Flask + SQLAlchemy |
| `ms-beerstock` | REST API + DB | Flask + SQLAlchemy |
| `lib-models` | Shared library | Pydantic v2 |
| `lib-ai` | Shared AI library | LangChain + MCP |
| `config` | Infra config files | YAML |

## Active Services

- `benchmark` — ACTIVE: test suite for AI agent APIs (latency, throughput, multi-model comparison)
- `agent-traduction` — ACTIVE: translation agent (FastAPI)

## Framework Convention

- **Flask** for KEEPER HTTP services (`ms-brewery`, `ms-cellar`, `ms-beerstock`) — synchronous, SQLAlchemy-based. No migration to FastAPI planned.
- **FastAPI** for all agent services — async, LLM-friendly.

## Tools

- **Python 3.14+** and **UV** — see `.github/instructions/python.instructions.md` for full conventions.
  Critical rule: always `uv run <cmd>`, never call `python`/`pip`/`pytest` directly.
- **Docker Compose** — 7 split files orchestrated via `Taskfile.yml` (go-task >= 3.28, install: `mise use task@latest` or `brew install go-task`)
- **Ruff** — linting and formatting, line-length=200, rules: E, F, W, I (configured in root `pyproject.toml`)
- **Pyright** — type checking

## Key Task Targets

```bash
task compose-up       # Start full stack (observability → db → kafka → ai-tools → ai → apps → traefik) — idempotent: running containers are preserved; use compose-down first to apply config/image changes
task compose-down     # Stop all services: traefik first (ingress), then apps → ai → ai-tools → kafka → db → observability
task compose-reset    # Full reset: down (remove volumes + built images) then up — use after image changes or DB schema changes
task lint             # Ruff check across all projects (PROJECTS var — includes agents)
task tools-format     # Ruff format across all projects (runs from repo root, applies root pyproject.toml config)
task models-init      # Pull Ollama AI models (mistral, llama, qwen, etc.)
task test             # test-lint → test-unit → test-integration (sequential, stops on first failure)
task --continue test  # Run all test phases even if one fails
task test-lint        # Ruff check scoped to KEEPER_SERVICES only (subset of lint)
task test-unit        # Pytest smoke tests — KEEPER_SERVICES only (11 dirs), no Docker required
task test-integration # Container health checks (ms-brewery, ms-cellar only) — skips if stack not running or runtime absent; unhealthy containers report failure
task --list           # Show all available tasks with descriptions
```

> **Taskfile variable scopes:** `PROJECTS` = all services (see `Taskfile.yml` for the full list), used by `task lint`.
> `KEEPER_SERVICES` (12 dirs) = business services with runnable processes, used by `task test-lint` and `task test-unit`.
> `HEALTHCHECK_SERVICES` (12 dirs) = `ms-brewery`, `ms-cellar`, `ms-beerstock` (Flask/HTTP healthcheck), all other KEEPER services (process healthcheck via `/proc`) — used by the `test-integration` health loop.
> Agent services (`agent-*`) and shared libs (`lib-*`) are in `PROJECTS` but not `KEEPER_SERVICES`.

## Environment Setup

Copy `.env.example` to `.env` before starting — it contains secrets and local overrides
(`GRAFANA_SERVICE_ACCOUNT_TOKEN`, `POSTGRES_PASSWORD`).
Docker image versions live in `versions.env` (committed — no copy needed, override in `.env` if required).

## Git Workflow (mandatory)

- **Always branch + PR** — never commit directly to `main`
- **Conventional Commits** format — see `.github/instructions/commit-message.instructions.md`
- PRs reviewed by a BMAD persona before merging (BMAD is the AI-assisted workflow framework used in this project — see `_bmad/`)

## Pre-PR Checklist (mandatory on every PR)

Before opening a PR, run both commands and verify they pass:
- `task test` — test-lint (ruff) → test-unit (pytest)
- `task typecheck` — pyright on all KEEPER services

If you modify a service's public function signatures, update its tests accordingly.

Also verify:
- `CLAUDE.md` (root) KEEPER Services table matches the actual services in `Taskfile.yml` `KEEPER_SERVICES`
- `docs/architecture.md` services table is up to date
- `README.md` Project Structure section reflects any added/removed services
- New services have a `README.md` in their directory
- No links in any doc point to files that don't exist

A PR template at `.github/pull_request_template.md` provides the checklist.

## OpenTelemetry Pattern

All KEEPER services are auto-instrumented via the `opentelemetry-instrument` wrapper in their Dockerfile `CMD`.
Key env vars: `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_TRACES/METRICS/LOGS_EXPORTER`.
Telemetry flows: logs → Loki, metrics → Mimir, traces → Tempo, UI → Grafana (port 3000).

## Error Injection

`ERROR_RATE` env var (0.0–1.0, default 0.1) injects random failures in Kafka producers, consumers,
and the brewmaster worker. The Flask REST APIs (`ms-brewery`, `ms-cellar`) do not use `ERROR_RATE`.
This is intentional — generates realistic, noisy telemetry for learning OTEL.

## Shared Libraries

- `lib-models` — Pydantic models shared across KEEPER services (editable install)
- `lib-ai` — LLM config, MCP Grafana client, agent Pydantic models (for agent services only)

## Infrastructure Access (local dev)

All services are behind **Traefik** (port 8081). Direct access:
- Grafana: `http://localhost:3000`
- Brewery API: `http://localhost:5000`
- Cellar API: `http://localhost:5001`

Via Traefik (`http://localhost:8081`):
- Kafka UI (AKHQ): `http://localhost:8081/akhq/`
- Traefik dashboard: `http://localhost:8082`

<!-- rtk-instructions v2 -->
# RTK (Rust Token Killer) - Token-Optimized Commands

## Golden Rule

**Always prefix commands with `rtk`**. If RTK has a dedicated filter, it uses it. If not, it passes through unchanged. This means RTK is always safe to use.

**Important**: Even in command chains with `&&`, use `rtk`:
```bash
# ❌ Wrong
git add . && git commit -m "msg" && git push

# ✅ Correct
rtk git add . && rtk git commit -m "msg" && rtk git push
```

## RTK Commands by Workflow

### Build & Compile (80-90% savings)
```bash
rtk cargo build         # Cargo build output
rtk cargo check         # Cargo check output
rtk cargo clippy        # Clippy warnings grouped by file (80%)
rtk tsc                 # TypeScript errors grouped by file/code (83%)
rtk lint                # ESLint/Biome violations grouped (84%)
rtk prettier --check    # Files needing format only (70%)
rtk next build          # Next.js build with route metrics (87%)
```

### Test (90-99% savings)
```bash
rtk cargo test          # Cargo test failures only (90%)
rtk vitest run          # Vitest failures only (99.5%)
rtk playwright test     # Playwright failures only (94%)
rtk test <cmd>          # Generic test wrapper - failures only
```

### Git (59-80% savings)
```bash
rtk git status          # Compact status
rtk git log             # Compact log (works with all git flags)
rtk git diff            # Compact diff (80%)
rtk git show            # Compact show (80%)
rtk git add             # Ultra-compact confirmations (59%)
rtk git commit          # Ultra-compact confirmations (59%)
rtk git push            # Ultra-compact confirmations
rtk git pull            # Ultra-compact confirmations
rtk git branch          # Compact branch list
rtk git fetch           # Compact fetch
rtk git stash           # Compact stash
rtk git worktree        # Compact worktree
```

Note: Git passthrough works for ALL subcommands, even those not explicitly listed.

### GitHub (26-87% savings)
```bash
rtk gh pr view <num>    # Compact PR view (87%)
rtk gh pr checks        # Compact PR checks (79%)
rtk gh run list         # Compact workflow runs (82%)
rtk gh issue list       # Compact issue list (80%)
rtk gh api              # Compact API responses (26%)
```

### JavaScript/TypeScript Tooling (70-90% savings)
```bash
rtk pnpm list           # Compact dependency tree (70%)
rtk pnpm outdated       # Compact outdated packages (80%)
rtk pnpm install        # Compact install output (90%)
rtk npm run <script>    # Compact npm script output
rtk npx <cmd>           # Compact npx command output
rtk prisma              # Prisma without ASCII art (88%)
```

### Files & Search (60-75% savings)
```bash
rtk ls <path>           # Tree format, compact (65%)
rtk read <file>         # Code reading with filtering (60%)
rtk grep <pattern>      # Search grouped by file (75%)
rtk find <pattern>      # Find grouped by directory (70%)
```

### Analysis & Debug (70-90% savings)
```bash
rtk err <cmd>           # Filter errors only from any command
rtk log <file>          # Deduplicated logs with counts
rtk json <file>         # JSON structure without values
rtk deps                # Dependency overview
rtk env                 # Environment variables compact
rtk summary <cmd>       # Smart summary of command output
rtk diff                # Ultra-compact diffs
```

### Infrastructure (85% savings)
```bash
rtk docker ps           # Compact container list
rtk docker images       # Compact image list
rtk docker logs <c>     # Deduplicated logs
rtk kubectl get         # Compact resource list
rtk kubectl logs        # Deduplicated pod logs
```

### Network (65-70% savings)
```bash
rtk curl <url>          # Compact HTTP responses (70%)
rtk wget <url>          # Compact download output (65%)
```

### Meta Commands
```bash
rtk gain                # View token savings statistics
rtk gain --history      # View command history with savings
rtk discover            # Analyze Claude Code sessions for missed RTK usage
rtk proxy <cmd>         # Run command without filtering (for debugging)
rtk init                # Add RTK instructions to CLAUDE.md
rtk init --global       # Add RTK to ~/.claude/CLAUDE.md
```

## Token Savings Overview

| Category | Commands | Typical Savings |
|----------|----------|-----------------|
| Tests | vitest, playwright, cargo test | 90-99% |
| Build | next, tsc, lint, prettier | 70-87% |
| Git | status, log, diff, add, commit | 59-80% |
| GitHub | gh pr, gh run, gh issue | 26-87% |
| Package Managers | pnpm, npm, npx | 70-90% |
| Files | ls, read, grep, find | 60-75% |
| Infrastructure | docker, kubectl | 85% |
| Network | curl, wget | 65-70% |

Overall average: **60-90% token reduction** on common development operations.
<!-- /rtk-instructions -->