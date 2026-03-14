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

### Discussion notes — choices made and why

**Pourquoi l'orchestrateur comme point d'entrée ?**
Intuition de a-team : l'orchestrateur est le cerveau, il doit exister pour que tout ait du sens.
Nuance Winston : ne pas le construire seul — le coupler dès le départ à au moins un agent feuille opérationnel pour pouvoir tester end-to-end. `agent-logs` suggéré comme premier agent feuille (Loki = plus simple, MCPGrafanaClient.query_logs déjà implémenté).

**Pourquoi LLM call pour le routing et pas des règles keyword ?**
L'utilisateur cible est une équipe support — les questions sont en langage naturel métier ("les commandes passent plus depuis ce matin"), pas des requêtes techniques. Les règles keyword ne suffisent pas pour capturer l'intent métier. Le LLM comprend le contexte et choisit les bons signaux.

**Pourquoi la contrainte de portabilité ?**
a-team veut pouvoir déployer ce système ailleurs — donner une doc applicative et que ça marche sans toucher au code. Ça interdit de hardcoder les noms de services, la topologie, les labels OTEL. Tout ça doit venir d'un fichier `app-context` externe.

**Pourquoi le pattern Reflexion (évaluation + retry) ?**
Les LLMs locaux (Ollama) peuvent retourner des réponses vides ou insuffisantes, surtout sur des requêtes DSL complexes. Plutôt que de présenter une mauvaise réponse au support, l'orchestrateur juge la qualité et reformule. Max 2-3 retries pour éviter les boucles infinies.

**Pourquoi stateless ?**
Learning lab, pas de prod. Pas de base de données agent, pas de session distribuée. Chaque requête est indépendante. Simplifie énormément le déploiement et la maintenance.

**Sortie orientée action, pas données brutes**
Le support peut déjà voir les logs bruts dans Grafana. La valeur ajoutée du système c'est la synthèse : problème identifié / impact / cause probable / recommandation. Sans ça, ce n'est qu'un wrapper Grafana.

---

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

