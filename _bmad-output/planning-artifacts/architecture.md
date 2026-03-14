---
stepsCompleted: [1]
inputDocuments:
  - docs/architecture.md
  - _bmad-output/brainstorming/brainstorming-session-2026-02-28.md
workflowType: architecture
project_name: python-otel-project-demo
user_name: a-team
date: '2026-03-14'
scope: agent-layer — observability AI assistant for support teams
---

# Architecture Decision Document

_Agent Layer — Observability AI Assistant for Support Teams_

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

---

## Session State

**Last updated:** 2026-03-14
**Workflow step:** Step 2 — Context Analysis (in progress, not yet saved)
**Next action:** Resume CA workflow — run Party Mode [P] on context analysis, then [C] to save and move to step-03

### Vision captured so far

- **Target user:** support teams debugging production issues via natural language
- **Entry point:** `agent-orchestrator` — receives prompt, routes, evaluates, synthesizes
- **Pattern:** Reflexion — orchestrator evaluates agent response quality, retries if insufficient (max 2-3)
- **Routing:** LLM call (not keyword rules) to decide which signals to query (logs/metrics/traces/all)
- **Key constraint — Portability:** system must be app-agnostic. Application topology injected via an `app-context` file (YAML/MD), not hardcoded. Goal: deploy elsewhere by swapping the context file, not the code.

### Transport layer clarification

Agents do NOT send DSL queries directly to Loki/Mimir/Tempo.
They use `MCPGrafanaClient` (from `lib-ai`) which calls MCP Grafana server tools:
- `query_loki_logs` → takes `logql` param
- `query_prometheus` → takes `expr` (PromQL) param
- `tempo_traceql-search` → takes `query` (TraceQL) param

NL → DSL translation still happens, but **inside MCP tool call parameters** (not raw HTTP).

### Functional Requirements (draft)

| ID | Requirement |
|----|-------------|
| FR1 | Intelligent routing by signal — LLM classifies intent (logs/metrics/traces/all) |
| FR2 | NL → MCP tool parameters translation (including DSL queries) |
| FR3 | Response quality evaluation + retry — Reflexion pattern |
| FR4 | Multi-source synthesis → actionable output (problem / impact / cause / recommendation) |
| FR5 | Dynamic app context injection — portability constraint |
| FR6 | Support-oriented output format |

### Non-Functional Requirements (draft)

| NFR | Requirement | Implication |
|-----|-------------|-------------|
| Portability | Zero app coupling | Context injected, not hardcoded |
| Local-first | Ollama, no cloud LLM | Simple retry strategy |
| Simplicity | Learning lab | Stateless, no distributed state |
| Confidence | Say when unsure | `confidence` score on every response |
| Resilience | Auto-retry on bad response | Reflexion loop max 2-3 iterations |

---

