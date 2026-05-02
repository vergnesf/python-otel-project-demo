# Unified AI Instructions for python-otel-project-demo

This document consolidates all AI-specific instructions from Claude, Copilot, and other AI tools into a single reference.

---

## 🎯 Project Overview

**Personal learning lab** for Python, OpenTelemetry, and infrastructure concepts. Simplicity over engineering.

- **Architecture:** Two-layer (KEEPER business layer + Agent layer with MCP)
- **Language:** Python 3.14+ (UV package manager)
- **Container Orchestration:** Docker Compose (7 split configs via Taskfile)
- **Observability:** Full OTEL stack (Loki, Mimir, Tempo → Grafana)

## 📦 Key Services

### KEEPER Services (12 business services)
- **Producers:** ms-brewer, ms-supplier, ms-retailer
- **Consumers:** ms-brewcheck, ms-ingredientcheck, ms-quality-control, ms-dispatch
- **Workers:** ms-brewmaster, ms-fermentation
- **APIs:** ms-brewery, ms-cellar, ms-beerstock (Flask + SQLAlchemy)

### Agent Services (FastAPI, async)
- agent-orchestrator, agent-logs, agent-metrics, agent-traces, agent-traduction, agent-ui

### Shared Libraries
- **lib-models:** Pydantic v2 models (all KEEPER services)
- **lib-ai:** LangChain, MCP Grafana client

---

## ⚙️ Framework Conventions

| Aspect | Standard |
|--------|----------|
| **HTTP/KEEPER** | Flask + SQLAlchemy (no FastAPI migration planned) |
| **Agents** | FastAPI (async, LLM-friendly) |
| **Package Mgr** | UV only — `uv run <cmd>`, never `python`/`pip` directly |
| **Linting** | Ruff (line-length=200, rules: E, F, W, I) |
| **Type Checking** | Pyright on all KEEPER services |
| **Testing** | Pytest (no pytest-async) |

## 🚀 Essential Tasks

```bash
# Stack Management
task compose-up       # Start full stack (idempotent — preserves running containers)
task compose-down     # Stop all services gracefully
task compose-reset    # Hard reset (remove volumes + built images)

# Python Tooling
task lint             # Ruff check all projects
task tools-format     # Ruff format all projects
task typecheck        # Pyright on KEEPER_SERVICES
task test             # test-lint → test-unit → test-integration
task test --continue  # Run all phases even if one fails

# AI Models
task models-init      # Pull Ollama models (qwen3, mistral, llama, etc.)

# Inspection
task --list           # Show all available tasks
```

## 📋 Variable Scopes (Taskfile.yml)

- **PROJECTS:** All services + agents + libs (used by `task lint`)
- **KEEPER_SERVICES:** 12 business services only (used by `task test-lint`, `task test-unit`)
- **HEALTHCHECK_SERVICES:** Flask APIs + all KEEPER services (used by `task test-integration`)

---

## 🔧 Configuration

### Environment Setup
1. Copy `.env.example` → `.env` (contains secrets + local overrides)
2. Secrets: `GRAFANA_SERVICE_ACCOUNT_TOKEN`, `POSTGRES_PASSWORD`
3. Image versions in `versions.env` (committed — override in `.env` if needed)

### Infrastructure Access (local)

**Note:** All KEEPER services and Agents are behind **Traefik reverse proxy** (port 8081) for unified ingress routing.

| Service | Direct Access | Via Traefik |
|---------|---|---|
| Grafana | http://localhost:3000 | — |
| Brewery API | http://localhost:5000 | — |
| Cellar API | http://localhost:5001 | — |
| Kafka UI (AKHQ) | — | http://localhost:8081/akhq/ |
| Traefik Dashboard | — | http://localhost:8082 |

**Traefik role:** Routes external HTTP traffic to backend services. Direct access is faster for local dev; Traefik is used for unified ingress in production deployments.

---

## 📝 Code Standards

### Python Conventions
See `.github/instructions/python.instructions.md`
- Type hints mandatory
- Follow PEP 8 (79 char max lines)
- `snake_case` for functions/vars, `CamelCase` for classes
- Break functions at ~50 lines (modularize)
- Use specific exceptions, fail fast with meaningful messages
- No global variables

### Commit Message Format
See `.github/instructions/commit-message.instructions.md`
- Use **Conventional Commits** format
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`
- Example: `feat(agent-orchestrator): add synthesis LLM step`
- Include `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>` footer

### Pull Request Workflow
1. Always branch + PR (never commit to `main`)
2. Run `task test` + `task typecheck` locally before pushing
3. Run pre-PR checklist (see PR template `.github/pull_request_template.md`)
4. PRs reviewed by BMAD personas before merge

---

## 🔍 Pre-PR Checklist

**Mandatory before opening PR:**
```bash
task test             # Must pass: test-lint → test-unit → test-integration
task typecheck        # Must pass: pyright on all KEEPER_SERVICES
```

**Documentation verification:**
- [ ] CLAUDE.md KEEPER Services table matches Taskfile.yml `KEEPER_SERVICES`
- [ ] docs/architecture.md services table is current
- [ ] README.md Project Structure reflects added/removed services
- [ ] New services have their own README.md
- [ ] No broken doc links

---

## 📡 OpenTelemetry Pattern

All KEEPER services auto-instrumented via `opentelemetry-instrument` wrapper in Dockerfile `CMD`.

**Key env vars:**
- `OTEL_SERVICE_NAME` — service identifier
- `OTEL_EXPORTER_OTLP_ENDPOINT` — collector endpoint
- `OTEL_TRACES/METRICS/LOGS_EXPORTER` — signal routing

**Telemetry flow:** logs → Loki, metrics → Mimir, traces → Tempo, UI → Grafana

---

## 🎲 Error Injection

`ERROR_RATE` env var (0.0–1.0, default 0.1) injects random failures in:
- Kafka producers/consumers
- Background workers (brewmaster)

**Flask REST APIs** (ms-brewery, ms-cellar) do NOT use `ERROR_RATE`. Intentional — generates realistic, noisy telemetry for learning OTEL.

---

## 📚 Related Instructions

For detailed guidance, see:
- `.github/instructions/python.instructions.md` — Python 3.14 + UV conventions
- `.github/instructions/python-mcp-server.instructions.md` — Building MCP servers
- `.github/instructions/langchain-python.instructions.md` — LangChain patterns
- `.github/instructions/commit-message.instructions.md` — Conventional Commits
- `_bmad/` — BMAD (Business Model AI Development) framework docs

---

## 🏗️ BMAD Workflow

This project uses **BMAD**, an AI-assisted development framework with:
- **Agents:** PM (product manager), architect, developer, QA, tech writer, etc.
- **Phases:** 1-analysis → 2-planning → 3-solutioning → 4-implementation
- **Artifacts:** Planning, implementation, brainstorming sessions in `_bmad-output/`
- **Skill commands:** `bmad-create-prd`, `bmad-create-architecture`, `bmad-dev-story`, etc.

---

## 🚨 Anti-Patterns

- ❌ Use `python` / `pip` / `pytest` directly — use `uv run` instead
- ❌ Commit secrets to source code
- ❌ Global variables
- ❌ Silent error handling (`try/except: pass`)
- ❌ Mock data fallbacks in production code paths
- ❌ Commit directly to `main` — always use branches + PR

---

## ✅ Quick Wins for Contributors

1. Pick an **open issue** from GitHub (sort by "Ready" label if available)
2. Create a branch: `git checkout -b fix/issue-name`
3. Follow code standards above
4. Run `task test` + `task typecheck`
5. Submit PR with Conventional Commits message
6. Update docs if needed
7. Wait for BMAD persona review

---

## 📚 Token Optimization Reference

> **RTK (Rust Token Killer)** — Token-optimized command filtering. Use `rtk` prefix on any CLI command to reduce output verbosity by 60-90% (saves context tokens in Claude/Copilot sessions).
>
> Examples: `rtk git log`, `rtk cargo build`, `rtk pytest`, `rtk docker ps` — see `rtk --help` for full reference.

---

**Last Updated:** 2026-04-25  
**Project Root:** `/home/fvergnes/workpace/git/vergnesf/python-otel-project-demo`

---

## 🤖 AI-Specific Instructions

### RTK — Token-Optimized CLI

**rtk** is a CLI proxy that filters and compresses command outputs, saving 60-90% tokens.

## Rule

Always prefix shell commands with `rtk`:

```bash
# Instead of:              Use:
git status                 rtk git status
git log -10                rtk git log -10
cargo test                 rtk cargo test
docker ps                  rtk docker ps
kubectl get pods           rtk kubectl pods
```

## Meta commands (use directly)

```bash
rtk gain              # Token savings dashboard
rtk gain --history    # Per-command savings history
rtk discover          # Find missed rtk opportunities
rtk proxy <cmd>       # Run raw (no filtering) but track usage
```

---

### Python 3.14 Coding Conventions and UV Workflow

## ⚠️ CRITICAL: Always Use UV for All Python Operations

**IMPORTANT:** GitHub Copilot MUST use `uv` for ALL Python-related operations in this project. Never use `python`, `pip`, `pytest`, or other tools directly without prefixing with `uv run`.

### UV Command Pattern

All Python operations follow this pattern:
```bash
uv run <command>
```

Examples:
```bash
uv run python script.py              # Run Python scripts
uv run pytest                        # Run tests
uv run pytest tests/                 # Run specific test directory
uv run pytest tests/test_file.py     # Run specific test file
uv run mypy src/                     # Type checking
uv run ruff check src/               # Linting
uv run black src/                    # Code formatting
uv run python -m pip list            # List packages
uv sync                              # Install dependencies from lock file
```

**Never use these directly:**
- ❌ `python script.py` → ✅ `uv run python script.py`
- ❌ `pytest` → ✅ `uv run pytest`
- ❌ `pip install` → ✅ `uv add`
- ❌ `mypy` → ✅ `uv run mypy`
- ❌ `black` → ✅ `uv run black`
- ❌ `ruff` → ✅ `uv run ruff`

---

### GitHub Copilot Commit Message Instructions

## Overview
Generate commit messages following the Conventional Commits 1.0.0 specification to create explicit, machine-readable commit history.

## Commit Message Structure

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## Required Elements

### Type (REQUIRED)
Must be one of the following:

- **feat**: A new feature (correlates with MINOR in SemVer)
- **fix**: A bug fix (correlates with PATCH in SemVer)
- **docs**: Documentation only changes
- **style**: Changes that don't affect code meaning (white-space, formatting, etc.)
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes that affect the build system or external dependencies
- **ci**: Changes to CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files
- **revert**: Reverts a previous commit

### Description (REQUIRED)
- Must immediately follow the colon and space after the type/scope prefix
- Short summary of code changes
- Use imperative, present tense: "change" not "changed" nor "changes"
- Don't capitalize first letter
- No period (.) at the end

## Optional Elements

### Scope (OPTIONAL)
- Noun describing a section of the codebase
- Enclosed in parentheses
- Examples: `feat(parser):`, `fix(api):`, `docs(readme):`

### Body (OPTIONAL)
- Must begin one blank line after the description
- Free-form, can consist of multiple paragraphs
- Provides additional contextual information about code changes
- Use imperative, present tense

### Footer(s) (OPTIONAL)
- Must be provided one blank line after the body
- Format: `<token>: <value>` or `<token> #<value>`
- Use hyphens in tokens: `Reviewed-by:`, `Refs:`
- Common footers: `Reviewed-by:`, `Refs:`, `Fixes:`, `Co-authored-by:`

---

### Python MCP Server Development

## ⚠️ CRITICAL: Always Use UV for All Operations

**IMPORTANT:** GitHub Copilot MUST use `uv` for ALL Python-related operations. Never use `python`, `pip`, or other tools directly.

### UV Command Pattern

All commands follow this pattern:
```bash
uv run <command>
```

Examples:
```bash
uv run python server.py              # Run Python scripts
uv run pytest                        # Run tests
uv run mcp dev server.py             # Test MCP server with Inspector
uv run mcp install server.py         # Install for Claude Desktop
```

**Never use these directly:**
- ❌ `python server.py` → ✅ `uv run python server.py`
- ❌ `pip install` → ✅ `uv add`
- ❌ `pytest` → ✅ `uv run pytest`
- ❌ `mcp dev` → ✅ `uv run mcp dev`

---

### LangChain Python Instructions

## ⚠️ CRITICAL: Always Use UV for Python Operations

**IMPORTANT:** GitHub Copilot MUST use `uv` for ALL Python-related operations. Never use `python` or `pip` directly.

### UV Command Pattern
```bash
uv run python script.py
uv run pytest
uv run mypy src/
```

**Never use these directly:**
- ❌ `python script.py` → ✅ `uv run python script.py`
- ❌ `pip install` → ✅ `uv add`

---

### Advanced Elicitation (BMAD)

**Goal:** Push the LLM to reconsider, refine, and improve its recent output.

## CRITICAL LLM INSTRUCTIONS

- **MANDATORY:** Execute ALL steps in the flow section IN EXACT ORDER
- DO NOT skip steps or change the sequence
- HALT immediately when halt-conditions are met
- Each action within a step is a REQUIRED action to complete that step
- Sections outside flow (validation, output, critical-context) provide essential context - review and apply throughout execution
- **YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the `communication_language`**

---

## INTEGRATION (When Invoked Indirectly)

When invoked from another prompt or process:

1. Receive or review the current section content that was just generated
2. Apply elicitation methods iteratively to enhance that specific content
3. Return the enhanced version back when user selects 'x' to proceed and return back
4. The enhanced content replaces the original section content in the output document

---

## FLOW

### Step 1: Method Registry Loading

**Action:** Load `./methods.csv` for elicitation methods. If party-mode may participate, resolve the agent roster via:

```bash
python3 {project-root}/_bmad/scripts/resolve_config.py --project-root {project-root} --key agents
```

The resolver merges four layers in order: `_bmad/config.toml` (installer base, team-scoped), `_bmad/config.user.toml` (installer base, user-scoped), `_bmad/custom/config.toml` (team overrides), and `_bmad/custom/config.user.toml` (personal overrides). Each entry under `agents` is keyed by the agent's `code` and carries `name`, `title`, `icon`, `description`, `module`, and `team`.

#### CSV Structure

- **category:** Method grouping (core, structural, risk, etc.)
- **method_name:** Display name for the method
- **description:** Rich explanation of what the method does, when to use it, and why it's valuable
- **output_pattern:** Flexible flow guide using arrows (e.g., "analysis -> insights -> action")

#### Context Analysis

- Use conversation history
- Analyze: content type, complexity, stakeholder needs, risk level, and creative potential

#### Smart Selection

1. Analyze context: Content type, complexity, stakeholder needs, risk level, creative potential
2. Parse descriptions: Understand each method's purpose from the rich descriptions in CSV
3. Select 5 methods: Choose methods that best match the context based on their descriptions
4. Balance approach: Include mix of foundational and specialized techniques as appropriate

---

### Step 2: Present Options and Handle Responses

#### Display Format

```
**Advanced Elicitation Options**
_If party mode is active, agents will join in._
Choose a number (1-5), [r] to Reshuffle, [a] List All, or [x] to Proceed:

1. [Method Name]
2. [Method Name]
3. [Method Name]
4. [Method Name]
5. [Method Name]
r. Reshuffle the list with 5 new options
a. List all methods with descriptions
x. Proceed / No Further Actions
```

#### Response Handling

**Case 1-5 (User selects a numbered method):**

- Execute the selected method using its description from the CSV
- Adapt the method's complexity and output format based on the current context
- Apply the method creatively to the current section content being enhanced
- Display the enhanced version showing what the method revealed or improved
- **CRITICAL:** Ask the user if they would like to apply the changes to the doc (y/n/other) and HALT to await response.
- **CRITICAL:** ONLY if Yes, apply the changes. IF No, discard your memory of the proposed changes. If any other reply, try best to follow the instructions given by the user.
- **CRITICAL:** Re-present the same 1-5,r,x prompt to allow additional elicitations

**Case r (Reshuffle):**

- Select 5 random methods from methods.csv, present new list with same prompt format
- When selecting, try to think and pick a diverse set of methods covering different categories and approaches, with 1 and 2 being potentially the most useful for the document or section being discovered

**Case x (Proceed):**

- Complete elicitation and proceed
- Return the fully enhanced content back to the invoking skill
- The enhanced content becomes the final version for that section
- Signal completion back to the invoking skill to continue with next section

**Case a (List All):**

- List all methods with their descriptions from the CSV in a compact table
- Allow user to select any method by name or number from the full list
- After selection, execute the method as described in the Case 1-5 above

**Case: Direct Feedback:**

- Apply changes to current section content and re-present choices

**Case: Multiple Numbers:**

- Execute methods in sequence on the content, then re-offer choices

---

### Step 3: Execution Guidelines

- **Method execution:** Use the description from CSV to understand and apply each method
- **Output pattern:** Use the pattern as a flexible guide (e.g., "paths -> evaluation -> selection")
- **Dynamic adaptation:** Adjust complexity based on content needs (simple to sophisticated)
- **Creative application:** Interpret methods flexibly based on context while maintaining pattern consistency
- Focus on actionable insights
- **Stay relevant:** Tie elicitation to specific content being analyzed (the current section from the document being created unless user indicates otherwise)
- **Identify personas:** For single or multi-persona methods, clearly identify viewpoints, and use party members if available in memory already
- **Critical loop behavior:** Always re-offer the 1-5,r,a,x choices after each method execution
- Continue until user selects 'x' to proceed with enhanced content, confirm or ask the user what should be accepted from the session
- Each method application builds upon previous enhancements
- **Content preservation:** Track all enhancements made during elicitation
- **Iterative enhancement:** Each selected method (1-5) should:
  1. Apply to the current enhanced version of the content
  2. Show the improvements made
  3. Return to the prompt for additional elicitations or completion

---

## 📚 Additional Resources

- [Python 3.14 Documentation](https://docs.python.org/3.14/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [MCP Protocol Documentation](https://docs.anthropic.com/claude/docs/model-context-protocol)
- [BMAD Framework Documentation](_bmad/README.md)

---

**Maintained by:** AI Agents  
**Last Updated:** 2026-04-25