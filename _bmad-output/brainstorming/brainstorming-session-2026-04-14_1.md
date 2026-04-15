---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'Agentic network architecture — incident investigation assistant via observability'
session_goals: 'Define each agent role, their interfaces, required tests and code to reach a functional MVP'
selected_approach: 'ai-recommended'
techniques_used: ['Question Storming', 'SCAMPER', 'Decision Tree Mapping']
ideas_generated: [9]
context_file: ''
session_active: false
workflow_completed: true
---

# Brainstorming Session Results

**Facilitator:** a-team  
**Date:** 2026-04-14

---

## Session Overview

**Topic:** Architecture of the agentic network — incident investigation assistant  
**Objective:** Define each agent's role, their interfaces, tests, and code to reach a functional MVP

### Target Scenario

> Support receives an incident → pastes the text into a chat → the agentic network queries logs/metrics/traces and synthesizes probable root causes

### Existing Agents

| Agent | Status | Role |
|-------|--------|------|
| `agent-ui` | DRAFT | Chat interface |
| `agent-orchestrator` | DRAFT | Interprets the incident, coordinates specialists |
| `agent-traduction` | ACTIVE | Language normalization |
| `agent-logs` | DRAFT | Queries Loki |
| `agent-metrics` | DRAFT | Queries Mimir |
| `agent-traces` | DRAFT | Queries Tempo |

### Constraints

- Personal learning project — simplicity > sophistication
- Local infrastructure (Ollama, Grafana MCP, Docker Compose)
- Beginner in agentic systems

---

## Architectural Decisions

### Decision 1 — Response Format: Correlated Analysis + Hypothesis (Version B)

**Decision:** Each specialist returns a structured summary of its domain (logs, metrics, traces). The orchestrator synthesizes the 3 summaries and formulates a root cause hypothesis.

**Rationale:** Avoids pure data aggregation. The LLM produces a real observability conclusion, not a list of raw data.

**Impact:** Orchestrator needs a `_synthesize_and_hypothesize()` step → the `synthesize_analysis.md` prompt already exists but is not wired up.

---

### Decision 2 — agent-traduction stays a separate service

**Decision:** `agent-traduction` is an independent FastAPI service, not a module embedded in the orchestrator.

**Rationale:** Separation of concerns — the orchestrator already handles dispatch and synthesis; adding language detection internally would overload it. A dedicated service can use a specialized small model (qwen3:0.6b) independently from the orchestrator's model.

**Impact:** The orchestrator calls `agent-traduction` via HTTP like any other specialist.

---

### Decision 3 — Selective dispatch by LLM orchestrator

**Decision:** The orchestrator decides which specialists to call (logs / metrics / traces) based on incident content. Not always the 3 agents.

**Rationale:** Reduces unnecessary latency. "Cannot connect to the database" → logs + metrics. "Slow response" → traces. A generic question → all 3.

**Impact:** `_route_to_agents()` with LLM routing already exists. Keyword fallback already implemented. ✓

---

### Decision 4 — agent-ui out of MVP

**Decision:** The chat interface (`agent-ui`) is excluded from the MVP. MVP = orchestrator + 3 specialists + traduction agent.

**Rationale:** agent-ui adds frontend complexity (stream, UX) that distracts from the core: observability correlation.

**Impact:** MVP validation via `curl` or the benchmark suite.

---

### Decision 5 — Specialist agents = separate FastAPI services

**Decision:** agent-logs, agent-metrics, agent-traces each have their own FastAPI process.

**Rationale:** Real-world separation of responsibilities. Each specialist can be developed, tested, and deployed independently.

**Impact:** All 5 services exist in docker-compose-ai.yml. ✓

---

### Decision 6 — Distributed analysis (each specialist runs LLM), centralized synthesis (orchestrator)

**Decision:** Each specialist agent (logs, metrics, traces) runs its own LLM call to produce a domain-specific structured analysis. The orchestrator only synthesizes the 3 results.

**Rationale:** Separates domain expertise (how to interpret a LogQL result) from correlation (what does it all mean together). Small models can be specialized per agent.

**Impact:** All 3 specialist analyzers already have LLM analysis (`_analyze_*_with_llm()`). The orchestrator synthesis step is missing — only string concatenation today.

---

### Decision 7 — Parallel HTTP calls to specialists

**Decision:** The orchestrator calls the 3 selected specialists concurrently via `asyncio.gather()`.

**Rationale:** Ollama serializes LLM inference but Grafana MCP data fetching is genuinely parallel. Network latency is amortized.

**Impact:** `_call_agents()` already uses `asyncio.gather()`. ✓

---

### Decision 8 — Orchestrator = LLM with tools pattern

**Decision:** The orchestrator embeds an LLM that reasons about the query and uses specialist agents as "tools" (HTTP calls). It decides which agents to call and how to synthesize their output.

**Rationale:** Classic LLM-with-tools pattern. Simpler than a multi-agent framework. Fits the "beginner in agentic systems" constraint.

**Impact:** Current implementation uses LLM for routing (`_route_to_agents`) and intent classification (`_classify_intent`). The synthesis step needs to be wired up.

---

### Decision 9 — agent-traduction = optional tool (not always called)

**Decision:** Translation is not systematic. The orchestrator calls agent-traduction only when the query language is not English.

**Rationale:** Small LLMs perform better in English. Translation adds latency on every call — better to detect first and translate only when needed.

**Impact:** **Gap identified**: the current orchestrator always calls `_detect_and_translate()` as the first step regardless of language. Needs to be made conditional.

---

## Technical Review of Existing Code (2026-04-14)

### What's working

| Component | Status |
|-----------|--------|
| All 5 agents have consistent FastAPI structure (main.py + analyzer.py) | ✓ |
| All expose `GET /health` and `POST /analyze` | ✓ |
| Parallel agent calls via `asyncio.gather()` | ✓ |
| LLM-powered routing with keyword fallback | ✓ |
| LLM-powered analysis in agent-logs, agent-metrics, agent-traces | ✓ |
| `synthesize_analysis.md` prompt exists in agent-orchestrator | ✓ |
| agent-traduction has tests | ✓ |
| agent-orchestrator has tests | ✓ |
| docker-compose-ai.yml has all 5 agents + agent-ui | ✓ |

### Gaps vs decisions

| Gap | Decision violated | Severity |
|-----|------------------|----------|
| Synthesis step not wired: `synthesize_analysis.md` exists but `_synthesize_and_hypothesize()` not called | Decision 1, 6 | High — no hypothesis produced |
| Translation is always called, not selective | Decision 9 | Medium — extra latency on every call |
| No smoke tests for agent-logs, agent-metrics, agent-traces | — | Medium — regressions undetected |
| Mock data fallback in `agent-metrics._query_mimir()` silently returns fake data | — | Medium — silent bad data |
| Orchestrator default ports: logs:8002, metrics:8003, traces:8004 — docker-compose overrides all to :8002 | — | Low — misleading defaults |
| No shared Pydantic response contract between specialist agents | Decision 6 | Low — runtime `KeyError` risk |

---

## Action Plan (MVP order)

**Phase 1 — Contract & quality**
1. Define specialist response contract (Pydantic model in lib-models)
2. Add smoke tests for agent-logs, agent-metrics, agent-traces
3. Fix default port values in orchestrator.py
4. Remove silent mock fallback in agent-metrics

**Phase 2 — Core agentic behavior**
5. Wire synthesis step in orchestrator: call `synthesize_analysis.md` → add `hypothesis` to response
6. Make translation conditional: skip agent-traduction if language is already English

**Phase 3 — Validation**
7. End-to-end test: paste real incident text → verify hypothesis is produced
8. Benchmark across models (qwen3:0.6b / mistral:7b) on the synthesis quality

---

## Development Order

Recommended: logs → metrics → traces → orchestrator synthesis → conditional translation

**Reason:** agent-logs is the most complete (LLM LogQL generation + LLM analysis). Use it as the reference pattern for metrics and traces. Wire the orchestrator synthesis last, once the specialist contracts are stable.
