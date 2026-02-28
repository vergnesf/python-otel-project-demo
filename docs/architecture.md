# Architecture

This project is a **personal learning lab** built in layers, each added as a new topic to explore.

## Two-Layer Design

```
┌─────────────────────────────────────────────────────────┐
│  BUSINESS LAYER (stable)                                │
│                                                         │
│  customer ──┐                  ┌── ordercheck ── order ─┤
│             ├── Kafka ─────────┤                       ├── PostgreSQL
│  supplier ──┘                  └── suppliercheck─ stock─┤
│                   ordermanagement (background worker)   │
└─────────────────────────┬───────────────────────────────┘
                          │ OTLP
                          ▼
┌─────────────────────────────────────────────────────────┐
│  OBSERVABILITY STACK                                    │
│  OTEL Collector → Loki (logs)                          │
│                 → Mimir (metrics)                       │
│                 → Tempo (traces)                        │
│                 → Grafana (UI)                          │
└─────────────────────────┬───────────────────────────────┘
                          │ MCP Protocol
                          ▼
┌─────────────────────────────────────────────────────────┐
│  AGENT LAYER (evolving)                                 │
│                                                         │
│  agent-ui → agent-orchestrator ──┬── agent-logs        │
│                                  ├── agent-metrics      │
│                                  └── agent-traces       │
└─────────────────────────────────────────────────────────┘
```

## Services

### Business Layer (KEEPER)

| Service | Role | Tech |
|---------|------|------|
| `customer` | Generates orders → Kafka | Kafka producer |
| `supplier` | Generates stock updates → Kafka | Kafka producer |
| `ordercheck` | Validates & forwards orders | Kafka consumer → REST |
| `suppliercheck` | Validates & forwards stock updates | Kafka consumer → REST |
| `order` | Order management API | Flask + PostgreSQL |
| `stock` | Stock management API | Flask + PostgreSQL |
| `ordermanagement` | Processes registered orders, updates stock | Background worker |
| `common-models` | Shared business models | Pydantic |
| `common-ai` | Shared AI utilities (LLM config, MCP client) | LangChain |
| `config` | Infrastructure configuration files | YAML |

### Agent Layer (DRAFT — code written, not yet operational)

| Service | Role |
|---------|------|
| `agent-orchestrator` | Routes queries, coordinates agents, synthesizes responses |
| `agent-logs` | Queries Loki for log analysis |
| `agent-metrics` | Queries Mimir for metrics analysis |
| `agent-traces` | Queries Tempo for trace analysis |
| `agent-ui` | Web chat interface |

### Tools (ACTIVE)

| Service | Role |
|---------|------|
| `agent-traduction` | Language detection and translation |
| `benchmark` | LLM performance testing framework |

## Data Flow

```
Business services generate activity autonomously
        │
        ▼ OTLP (traces, metrics, logs)
OTEL Collector
        │
        ├──▶ Loki     (logs)
        ├──▶ Mimir    (metrics)
        └──▶ Tempo    (traces)
                │
                ▼
        Grafana (UI + MCP server)
                │ MCP Protocol
                ▼
        Agent layer reads observability data
        and answers natural language queries
```

## Infrastructure

- **Reverse proxy**: Traefik (port 8081)
- **Message broker**: Kafka
- **Database**: PostgreSQL
- **LLM runtime**: Ollama (local models)
- **Container**: Docker / Podman
- **Package manager**: UV
