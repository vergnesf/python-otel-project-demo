# Agent Traces (Tempo Specialist)

The **Traces Agent** is specialized in analyzing distributed traces from **Tempo** via the Grafana MCP server. It identifies slow spans, analyzes service dependencies, and provides insights about request flows and bottlenecks.

## 🛤️ Role

- **Distributed Tracing**: Analyze request flows across microservices
- **Bottleneck Detection**: Identify slow spans and performance issues
- **Service Dependency Mapping**: Understand service call patterns
- **Error Propagation**: Track how errors cascade through services
- **Latency Analysis**: Deep-dive into request timing

## 🔍 Capabilities

### Trace Analysis
- Find slow or failed traces
- Analyze span durations
- Identify critical path in requests
- Detect timeout issues

### Service Dependencies
- Map service-to-service calls
- Identify upstream/downstream dependencies
- Detect circular dependencies
- Analyze call frequency

### Performance Insights
- Identify slowest operations
- Find network latency issues
- Detect database query bottlenecks
- Analyze queue wait times

### Error Analysis
- Track error propagation
- Identify error sources
- Correlate errors with spans
- Link to logs via trace ID

## 🚀 API Endpoints

### POST /analyze
Analyze traces based on user query.

**Request:**
```json
{
  "query": "Why is order service slow?",
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
  "agent_name": "traces",
  "analysis": "Analyzed 150 traces containing order service...",
  "data": {
    "total_traces": 150,
    "slow_traces": 23,
    "failed_traces": 15,
    "avg_duration_ms": 285,
    "bottlenecks": [
      {
        "service": "order",
        "operation": "POST /orders",
        "avg_duration_ms": 312
      }
    ],
    "service_dependencies": ["customer", "ordercheck", "order", "postgres"]
  },
  "confidence": 0.88,
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
PORT=8004
LOG_LEVEL=INFO
```

## 🐳 Docker

Build and run:

```bash
docker build -t agent-traces:latest .
docker run -p 8004:8004 agent-traces:latest
```

## 🧪 Local Development

```bash
# Install dependencies
uv sync

# Run the traces agent
uv run uvicorn agent_traces.main:app --reload --host 0.0.0.0 --port 8004
```

## 📊 TraceQL Queries

The agent generates TraceQL queries for Tempo:

### Failed Traces
```traceql
{service.name="order" && status=error}
```

### Slow Traces
```traceql
{service.name="order" && duration > 500ms}
```

### Specific Operation
```traceql
{service.name="order" && name="POST /orders"}
```

### Service Path
```traceql
{service.name="customer"} >> {service.name="order"}
```

### Error with Specific Message
```traceql
{service.name="order" && status=error && span.error.message=~"DB.*"}
```

## 🎯 Analysis Examples

### Example 1: Slow Requests
**Query**: "Why are order requests slow?"

**Analysis**:
- Queries traces for order service
- Identifies spans > 200ms
- Finds slowest operation: DB queries
- Provides breakdown of time spent

### Example 2: Failed Requests
**Query**: "Analyze failed orders"

**Analysis**:
- Filters traces with status=error
- Identifies failure points in request flow
- Maps error propagation: customer → ordercheck → order
- Correlates with log errors

### Example 3: Service Dependencies
**Query**: "Show order service dependencies"

**Analysis**:
- Extracts service call graph
- Identifies: customer → ordercheck → order → postgres
- Calculates call frequency
- Detects potential circular dependencies

## 🔄 Request Flow Analysis

The agent can reconstruct complete request flows:

```
customer → ordercheck → order → stock → postgres
  85ms       120ms      312ms    78ms     145ms
                                  ↓
                           (Bottleneck: DB insertion)
```

## 🎯 Bottleneck Detection

Identifies bottlenecks by:
- **Span Duration**: Longest spans in traces
- **Frequency**: Most called operations
- **Error Rate**: Operations that fail frequently
- **Downstream Impact**: Slow upstream services affecting downstream

## 📈 Insights Provided

- **Critical Path**: Which services add the most latency
- **Error Sources**: Where errors originate
- **Dependency Chain**: Complete service call graph
- **Optimization Targets**: Services/operations to optimize first
