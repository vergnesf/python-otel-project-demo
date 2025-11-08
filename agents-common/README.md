# Agents Common Module

This module provides shared models, utilities, and clients for the observability agentic network.

## 📦 Contents

- **models.py** - Shared Pydantic models for agent communication
- **mcp_client.py** - Base MCP (Model Context Protocol) client for Grafana
- **llm_config.py** - LLM configuration and utilities

## 🔧 Usage

This module is imported by all agent services:
- `agent-orchestrator`
- `agent-logs`
- `agent-metrics`
- `agent-traces`
- `agents-ui`

## 📖 Models

### AgentRequest
Request sent to specialized agents from the orchestrator.

```python
AgentRequest(
    query="Why is the order service failing?",
    time_range="1h",
    context={"services": ["order", "ordercheck"]}
)
```

### AgentResponse
Response from specialized agents back to the orchestrator.

```python
AgentResponse(
    agent_name="logs-agent",
    analysis="Found 47 errors in order service...",
    data={"error_count": 47, "error_types": [...]},
    confidence=0.85,
    grafana_links=["http://grafana:3000/..."]
)
```

## 🌐 MCP Client

The `MCPGrafanaClient` provides a unified interface to query Grafana datasources:

```python
from agents_common.mcp_client import MCPGrafanaClient

client = MCPGrafanaClient(base_url="http://grafana-mcp:8000")

# Query logs from Loki
logs = await client.query_logs(
    query='{service_name="order"} |= "error"',
    time_range="1h"
)

# Query metrics from Mimir
metrics = await client.query_metrics(
    query='rate(http_requests_total{service="order"}[5m])',
    time_range="1h"
)

# Query traces from Tempo
traces = await client.query_traces(
    query='service.name="order" && status=error',
    time_range="1h"
)
```

## 🤖 LLM Configuration

Centralized LLM setup for all agents:

```python
from agents_common.llm_config import get_llm

llm = get_llm()  # Returns configured ChatOpenAI instance
```
