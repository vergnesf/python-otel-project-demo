# Agent Metrics

> **Status:** `DRAFT` — Code written but not yet operational. No maintenance required.

Mimir specialist agent that analyzes performance metrics via the Grafana MCP server.

## 📊 Features

- Performance analysis (CPU, memory, latency)
- Anomaly detection and pattern recognition
- Trend analysis over time
- Resource utilization monitoring
- SLI/SLO tracking and alerting

## 🔍 Capabilities

### Performance Metrics
- HTTP request rates and error rates
- Response latency (p50, p95, p99)
- Throughput and request volume
- Status code distribution (2xx, 4xx, 5xx)

### Resource Metrics
- CPU utilization per service
- Memory usage and trends
- Database connection pool usage
- Network I/O

### Anomaly Detection
- Detect sudden spikes in error rates
- Identify latency degradation
- Find resource exhaustion patterns
- Correlate metrics across services

## 🚀 API Endpoints

### POST /analyze
Analyze metrics based on user query.

**Request:**
```json
{
  "query": "Check performance of order service",
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
  "agent_name": "metrics",
  "analysis": "Order service shows 10.2% HTTP 500 error rate...",
  "data": {
    "error_rate": 0.102,
    "request_rate": 125.5,
    "latency_p95": 245,
    "anomalies": [
      {"metric": "http_errors_total", "severity": "high"}
    ]
  },
  "confidence": 0.92,
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
PORT=8003
LOG_LEVEL=INFO
```

## 🐳 Docker

Build and run:

```bash
docker build -t agent-metrics:latest .
docker run -p 8003:8003 agent-metrics:latest
```

## 🧪 Local Development

```bash
# Install dependencies
uv sync

# Run the metrics agent
uv run uvicorn agent_metrics.main:app --reload --host 0.0.0.0 --port 8003
```

## 📦 Dependencies

- `httpx`: HTTP client for API calls
- `common-ai`: Shared AI utilities (MCP client, LLM config)

## 📊 PromQL Queries

The agent generates PromQL queries for Mimir:

### Error Rate
```promql
rate(http_requests_total{status=~"5..", service="order"}[5m])
```

### Request Rate
```promql
sum(rate(http_requests_total{service="order"}[5m]))
```

### Latency Percentiles
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service="order"}[5m]))
```

### CPU Usage
```promql
avg(rate(process_cpu_seconds_total{service="order"}[5m])) * 100
```

### Memory Usage
```promql
process_resident_memory_bytes{service="order"} / 1024 / 1024
```

## 🎯 Analysis Examples

### Example 1: Error Rate Analysis
**Query**: "High error rate in order service"

**Analysis**:
- Queries HTTP 5xx error rates
- Compares to baseline/SLO
- Identifies spike timing
- Correlates with deployment events

### Example 2: Performance Degradation
**Query**: "Order service is slow"

**Analysis**:
- Queries latency percentiles (p50, p95, p99)
- Identifies latency increase
- Checks resource utilization
- Suggests bottlenecks

### Example 3: Resource Exhaustion
**Query**: "Is order service running out of memory?"

**Analysis**:
- Queries memory usage trends
- Checks for memory leaks
- Analyzes GC patterns
- Provides capacity recommendations

## 📈 Anomaly Detection

The agent detects:
- **Spikes**: Sudden increases (>50% from baseline)
- **Degradation**: Gradual performance decline
- **Outliers**: Metrics outside normal ranges
- **Correlations**: Related metric changes across services

## 🐳 Podman Compose

### Redeploy Command

Use the generic `redeploy` command from the root Makefile to rebuild any service:

```bash
# Redeploy any service (agent-metrics, agent-logs, etc.)
make redeploy agent-metrics
```

This command will:
1. Stop the specified service
2. Rebuild with `--no-cache` to ensure fresh code
3. Restart the service

**Note:** If no service is specified, the command will show an error with usage instructions.
