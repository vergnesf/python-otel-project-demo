# Agent Logs

Loki specialist agent that analyzes log data via the Grafana MCP server.

## 📊 Features

- Error pattern detection and analysis
- Log aggregation and categorization
- Service correlation and trace linking
- Temporal analysis of error trends
- Context extraction from log messages

## 🔍 Capabilities

### Error Analysis
- Detect error rates per service
- Identify error types and their frequency
- Extract error messages and stack traces
- Correlate errors with trace IDs

### Pattern Recognition
- Find log patterns across services
- Detect anomalies in log volume
- Identify cascading failures

### Time-based Analysis
- Analyze error trends over time
- Identify error spikes
- Correlate with deployment times

## 🚀 API Endpoints

### POST /analyze
Analyze logs based on user query.

**Request:**
```json
{
  "query": "Find errors in order service",
  "time_range": "1h",
  "context": {
    "services": ["order"],
    "focus": "errors"
  }
}
```

**Response:**
```json
{
  "agent_name": "logs",
  "analysis": "Found 47 errors in order service over the last hour...",
  "data": {
    "total_logs": 1250,
    "error_count": 47,
    "error_types": [
      {"type": "Simulated DB insertion error", "count": 42},
      {"type": "Unexpected error", "count": 5}
    ],
    "affected_services": ["order"],
    "sample_logs": ["..."]
  },
  "confidence": 0.95,
  "grafana_links": ["http://grafana:3000/explore?..."],
  "timestamp": "2025-11-08T10:30:00Z"
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "mcp_server": "reachable"
}
```

## 🔧 Configuration

Environment variables:

```bash
# MCP Grafana Server
MCP_GRAFANA_URL=http://grafana-mcp:8000

# LLM configuration
LLM_BASE_URL=http://172.17.0.1:12434/engines/llama.cpp/v1
LLM_API_KEY=dummy-token
LLM_MODEL=qwen3

# Server configuration
HOST=0.0.0.0
PORT=8002
LOG_LEVEL=INFO
```

## 🐳 Docker

Build and run:

```bash
docker build -t agent-logs:latest .
docker run -p 8002:8002 agent-logs:latest
```

## 🧪 Local Development

```bash
# Install dependencies
uv sync

# Run the logs agent
uv run uvicorn agent_logs.main:app --reload --host 0.0.0.0 --port 8002
```

## 📦 Dependencies

- `httpx`: HTTP client for API calls
- `common-ai`: Shared AI utilities (MCP client, LLM config)

## 📊 LogQL Queries

The agent generates LogQL queries for Loki:

### Error Logs
```logql
{service_name="order"} |= "error" | json
```

### Specific Error Types
```logql
{service_name="order"} |~ "Simulated DB.*error"
```

### Count Errors by Service
```logql
sum by (service_name) (count_over_time({service_name=~".+"} |= "error" [1h]))
```

### Trace Correlation
```logql
{service_name="order"} | json | trace_id="abc123"
```

## 🎯 Analysis Examples

### Example 1: Generic Error Query
**Query**: "What errors are happening?"

**Analysis**:
- Queries all services for error-level logs
- Aggregates by error type
- Provides error count and distribution

### Example 2: Service-Specific
**Query**: "Errors in order service last hour"

**Analysis**:
- Filters logs for service_name="order"
- Time range: last 1 hour
- Groups errors by type
- Provides sample error messages

### Example 3: Pattern Detection
**Query**: "DB errors across all services"

**Analysis**:
- Searches for "DB" or "database" in error logs
- Identifies affected services
- Correlates with known issues (ERROR_RATE simulation)
