# Agentic Architecture Strategy with Grafana MCP

## Overview

This architecture combines the best of both worlds:
- **Specialized agents**: Domain expertise (logs, metrics, traces)
- **Centralized MCP server**: Unified access to Grafana data
- **Intelligent orchestration**: Routing and synthesis of analyses

## Current architecture

```
┌───────────────────────────────────────────────────────┐
│                  ORCHESTRATION LAYER                  │
│                                                        │
│  ┌──────────────────────────────────────────────┐   │
│  │         agent-orchestrator                    │   │
│  │  • Routes requests to the right agents       │   │
│  │  • Synthesizes multi-agent results           │   │
│  │  • Manages context and conversation          │   │
│  └────┬─────────────┬────────────┬───────────────┘   │
│       │             │            │                    │
└───────┼─────────────┼────────────┼────────────────────┘
    │             │            │
┌───────┼─────────────┼────────────┼────────────────────┐
│       │   SPECIALIZED AGENTS LAYER│                   │
│       ↓             ↓            ↓                    │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐            │
│  │ agent-  │  │ agent-   │  │ agent-   │            │
│  │  logs   │  │ metrics  │  │ traces   │            │
│  │         │  │          │  │          │            │
│  │ Expert: │  │ Expert:  │  │ Expert:  │            │
│  │ • LogQL │  │ • PromQL │  │ • TraceQL│            │
│  │ • Error │  │ • SLIs   │  │ • Latency│            │
│  │ patterns│  │ • Alerts │  │ • Deps   │            │
│  └────┬────┘  └─────┬────┘  └─────┬────┘            │
│       │             │             │                  │
└───────┼─────────────┼─────────────┼──────────────────┘
    │             │             │
┌───────┴─────────────┴─────────────┴──────────────────┐
│              DATA ACCESS LAYER                        │
│                                                        │
│  All agents use:                                     │
│  ┌──────────────────────────────────────────┐        │
│  │      MCPGrafanaClient (Python)           │        │
│  │  • MCP abstraction in Python             │        │
│  │  • Session management                     │        │
│  │  • Datasource UID caching                │        │
│  └──────────────┬───────────────────────────┘        │
│                 │                                     │
│                 ↓                                     │
│  ┌──────────────────────────────────────────┐        │
│  │      MCP Grafana Server (mcp/grafana)   │        │
│  │  • SSE endpoint: :8000/sse               │        │
│  │  • 49+ MCP tools available               │        │
│  └──────────────┬───────────────────────────┘        │
│                 │                                     │
└─────────────────┼─────────────────────────────────────┘
          │
     ┌────────┴────────┐
     ↓                 ↓
    ┌─────────┐      ┌──────────────┐
    │ Grafana │ ───→ │ Datasources  │
    │  :3000  │      │ Loki, Mimir, │
    └─────────┘      │ Tempo, etc.  │
             └──────────────┘
```

## Why this approach is excellent

### ✅ 1. Separation of concerns

Each agent has a **clear domain of expertise**:

| Agent             | Expertise                    | MCP tools used                                                         |
| ----------------- | ---------------------------- | ---------------------------------------------------------------------- |
| **agent-logs**    | Log analysis, error patterns | `query_loki_logs`, `list_loki_label_names`, `query_loki_stats`         |
| **agent-metrics** | Metrics, SLIs, performance   | `query_prometheus`, `list_prometheus_metric_names`, `list_alert_rules` |
| **agent-traces**  | Distributed traces, latency  | Tempo (via proxied tools), Pyroscope profiling                         |

### ✅ 2. Specialized and optimized prompts

Each agent can have tailored **system prompts**:

```python
# agent-logs/prompts/system.md
"""
You are an expert in system and application log analysis.

Main skills:
- Mastery of LogQL (Loki Query Language)
- Identifying error patterns (stack traces, exceptions)
- Temporal correlation of events
- Analysis of structured and unstructured logs

When analyzing logs:
1. Identify errors and their frequency
2. Look for recurring patterns
3. Correlate with timestamps
4. Recommend concrete actions
"""
```

### ✅ 3. Scalability and parallelization

The orchestrator can **query multiple agents in parallel**:

```python
# agent-orchestrator/orchestrator.py

async def analyze_service_issue(self, service: str, user_query: str):
    """
    Full analysis of a service issue
    Queries multiple agents in parallel
    """
    # Launch parallel analyses
    results = await asyncio.gather(
    self.agent_logs.analyze(
        query=f"Errors on {service}",
        time_range="1h"
    ),
    self.agent_metrics.analyze(
        query=f"Performance of {service}",
        time_range="1h"
    ),
    self.agent_traces.analyze(
        query=f"Slow traces of {service}",
        time_range="1h"
    ),
    return_exceptions=True  # Continue even if an agent fails
    )

    # Intelligent synthesis with LLM
    synthesis = await self.synthesize_results(results, user_query)
    return synthesis
```

### ✅ 4. Context-driven intelligent orchestration

The orchestrator **dynamically decides** which agents to call:

```python
async def route_query(self, user_query: str):
    """
    Analyze the query and route to the appropriate agents
    """
    # Use an LLM to classify the query
    classification = await self.llm.invoke(f"""
    Analyze this query and identify the concerned domains:
    - logs (if mentions errors, issues, messages)
    - metrics (if mentions performance, latency, CPU, memory)
    - traces (if mentions spans, slow requests, dependencies)

    Query: {user_query}

    Return a JSON list: ["logs", "metrics"] for example
    """)

    agents_to_call = parse_classification(classification)

    # Selective agent calls
    results = []
    if "logs" in agents_to_call:
    results.append(await self.agent_logs.analyze(user_query))
    if "metrics" in agents_to_call:
    results.append(await self.agent_metrics.analyze(user_query))
    # ...
```

### ✅ 5. Reusability of agents

Each agent can be **used independently**:

```python
# Via the orchestrator
GET http://agent-orchestrator:8001/analyze
{"query": "Issue on service order"}

# Directly to the logs agent
GET http://agent-logs:8002/analyze
{"query": "Order errors", "time_range": "24h"}

# Directly to the metrics agent
GET http://agent-metrics:8002/analyze
{"query": "Order latency"}
```

## Progressive enrichment plan

### Phase 1: Consolidation (✅ Done)

Each agent already uses:
- ✅ `query_loki_logs` (agent-logs)
- ✅ `query_prometheus` (agent-metrics)
- ✅ `list_datasources` (all)

### Phase 2: Enrich existing capabilities (Recommended priority)

#### 2.1 agent-logs: Add advanced Loki tools

```python
# common-ai/common_ai/mcp_client.py

async def list_loki_labels(self) -> list[str]:
    """List all labels available in Loki"""
    session = await self._ensure_session()
    result = await session.call_tool(
    "list_loki_label_names",
    arguments={"datasourceUid": self.loki_uid}
    )
    # Parse and return labels

async def get_loki_label_values(self, label: str) -> list[str]:
    """Retrieve possible values for a label"""
    session = await self._ensure_session()
    result = await session.call_tool(
    "list_loki_label_values",
    arguments={
        "datasourceUid": self.loki_uid,
        "labelName": label
    }
    )
    # Parse and return values

async def query_loki_stats(
    self,
    query: str,
    time_range: str = "1h"
) -> dict:
    """Statistics on logs (volumes, rates)"""
    start, end = self._parse_time_range(time_range)
    session = await self._ensure_session()
    result = await session.call_tool(
    "query_loki_stats",
    arguments={
        "datasourceUid": self.loki_uid,
        "logql": query,
        "startRfc3339": start,
        "endRfc3339": end
    }
    )
    return self._parse_result(result)
```

Impact: agent-logs will be able to:
- Automatically discover available services
- Analyze log volumes
- Build smarter queries

#### 2.2 agent-metrics: Add advanced Prometheus tools

```python
async def list_prometheus_metrics(self) -> list[str]:
    """List all available metrics"""
    session = await self._ensure_session()
    result = await session.call_tool(
    "list_prometheus_metric_names",
    arguments={"datasourceUid": self.prometheus_uid}
    )
    return self._parse_result(result)

async def get_metric_metadata(self, metric_name: str) -> dict:
    """Metadata for a metric (type, help, unit)"""
    session = await self._ensure_session()
    result = await session.call_tool(
    "list_prometheus_metric_metadata",
    arguments={
        "datasourceUid": self.prometheus_uid,
        "metric": metric_name
    }
    )
    return self._parse_result(result)

async def list_alert_rules(self) -> list[dict]:
    """List configured alert rules"""
    session = await self._ensure_session()
    result = await session.call_tool(
    "list_alert_rules",
    arguments={}
    )
    return self._parse_result(result)
```

Impact: agent-metrics will be able to:
- Automatically discover available metrics
- Understand metric type and unit
- Check existing alert rules

#### 2.3 All agents: Contextual annotations

```python
async def create_annotation(
    self,
    text: str,
    tags: list[str],
    time: str | None = None
) -> dict:
    """Create an annotation in Grafana"""
    session = await self._ensure_session()
    result = await session.call_tool(
    "create_annotation",
    arguments={
        "text": text,
        "tags": tags,
        "time": time or int(datetime.now().timestamp() * 1000)
    }
    )
    return self._parse_result(result)

async def get_annotations(
    self,
    time_range: str = "1h",
    tags: list[str] | None = None
) -> list[dict]:
    """Retrieve annotations"""
    start, end = self._parse_time_range(time_range)
    session = await self._ensure_session()
    result = await session.call_tool(
    "get_annotations",
    arguments={
        "from": start,
        "to": end,
        "tags": tags or []
    }
    )
    return self._parse_result(result)
```

Impact: Agents will be able to:
- Create annotations when anomalies are detected
- Correlate events with metrics/logs
- Enrich temporal context

### Phase 3: Cross-cutting new capabilities

#### 3.1 Integration with incidents

```python
# New agent or orchestrator capability
async def create_incident_if_critical(
    self,
    analysis_results: dict
) -> dict | None:
    """
    Automatically create an incident if the analysis
    reveals a critical problem
    """
    if analysis_results.get("severity") == "critical":
    session = await self._ensure_session()
    result = await session.call_tool(
        "create_incident",
        arguments={
        "title": f"Detected incident: {analysis_results['summary']}",
        "severity": "critical",
        "status": "open"
        }
    )
    return self._parse_result(result)
    return None
```

#### 3.2 Sift analysis for pattern detection

```python
async def find_error_patterns(
    self,
    service: str,
    time_range: str = "1h"
) -> dict:
    """
    Use Sift to automatically detect error patterns
    """
    session = await self._ensure_session()
    result = await session.call_tool(
    "find_error_pattern_logs",
    arguments={
        "query": f'{{service_name="{service}"}}',
        "timeRange": time_range
    }
    )
    return self._parse_result(result)
```

#### 3.3 Dynamic dashboards

```python
async def search_relevant_dashboards(
    self,
    service: str
) -> list[dict]:
    """
    Find dashboards relevant to a service
    """
    session = await self._ensure_session()
    result = await session.call_tool(
    "search_dashboards",
    arguments={
        "query": service,
        "type": "dash-db"
    }
    )
    return self._parse_result(result)

async def generate_dashboard_link(
    self,
    dashboard_uid: str,
    time_range: str = "1h"
) -> str:
    """
    Generate a deeplink to a dashboard
    """
    session = await self._ensure_session()
    result = await session.call_tool(
    "generate_deeplink",
    arguments={
        "resourceType": "dashboard",
        "resourceUid": dashboard_uid,
        "timeRange": time_range
    }
    )
    return self._parse_result(result)
```

### Phase 4: Advanced profiling and traces

#### 4.1 agent-traces: Pyroscope for profiling

```python
async def fetch_cpu_profile(
    self,
    service: str,
    time_range: str = "1h"
) -> dict:
    """
    Retrieve CPU profiling data
    """
    session = await self._ensure_session()
    result = await session.call_tool(
    "fetch_pyroscope_profile",
    arguments={
        "datasourceUid": self.pyroscope_uid,
        "profileType": "cpu",
        "labelSelector": f'{{service_name="{service}"}}',
        "startRfc3339": start,
        "endRfc3339": end
    }
    )
    return self._parse_result(result)
```

## Examples of enriched scenarios

### Scenario 1: Automatic investigation

```python
# User request
"Service order has issues, analyze it"

# Orchestrator:
1. Route to the 3 agents in parallel
2. agent-logs:
   - Query error logs
   - Use find_error_pattern_logs (Sift)
   - Create an annotation "Investigation started"
3. agent-metrics:
   - Query performance metrics
   - Check active alert_rules
   - Compare with normal values
4. agent-traces:
   - Query slow traces
   - Identify bottlenecks
5. Orchestrator synthesizes
6. If critical → create_incident automatically
7. Return links to relevant dashboards
```

### Scenario 2: Guided exploration

```python
# User request
"What services can I monitor?"

# agent-logs :
1. list_loki_label_values("service_name")
   → ["order", "stock", "customer", ...]
2. For each service, query_loki_stats
   → Log volume per service
3. search_relevant_dashboards for each service
4. Present an interactive table with links
```

## Benefits of this strategy

| Aspect              | Benefit                                                            |
| ------------------- | ------------------------------------------------------------------ |
| **Maintainability** | Code organized by domain, easy to debug                            |
| **Performance**     | Native parallelization, each agent optimized                       |
| **Scalability**     | Add new agents without impact (agent-profiling, agent-security...) |
| **Testability**     | Each agent independently testable                                  |
| **Expertise**       | Prompts and logic specialized per domain                           |
| **Resilience**      | If one agent fails, others continue                                |
| **Flexibility**     | Use directly or via the orchestrator                               |

## Comparison with a single LLM agent

| Criterion             | Multi-agents (your approach)  | Single LLM agent       |
| --------------------- | ----------------------------- | ---------------------- |
| **Prompt complexity** | ✅ Simple, specialized prompts | ❌ Huge, complex prompt |
| **Context window**    | ✅ Small context per agent     | ❌ Risk of overflow     |
| **Parallelization**   | ✅ Native                      | ❌ Sequential           |
| **Maintenance**       | ✅ Isolated changes            | ❌ Global impact        |
| **LLM cost**          | ✅ Optimized (small prompts)   | ❌ High tokens          |
| **Expertise**         | ✅ Domain-specialized          | ⚠️ Generalist           |
| **Debugging**         | ✅ Easy (per agent)            | ❌ Hard                 |

## Final recommendation

Keep your multi-agent architecture!

Enrich it progressively with MCP tools:

1. ✅ Phase 2.1-2.2 (High priority): Labels, stats, metadata
2. ✅ Phase 2.3 (Medium priority): Annotations
3. ⏳ Phase 3 (When needed): Incidents, Sift, Dashboards
4. ⏳ Phase 4 (Advanced): Profiling

This approach gives you:
- ✅ Maximum flexibility
- ✅ Optimal performance
- ✅ Long-term maintainability
- ✅ Possibility to integrate external agents (n8n) later
- ✅ An architecture that scales horizontally

Would you like me to start by enriching the MCP client with the Phase 2.1-2.2 tools?

