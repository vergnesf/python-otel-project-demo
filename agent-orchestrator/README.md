# Agent Orchestrator

The **Orchestrator Agent** is the main coordinator of the observability agentic network. It receives user queries, routes them to specialized agents (Logs, Metrics, Traces), and synthesizes their responses into a coherent analysis.

## 🎯 Role

- **Request Analysis**: Parse and understand user queries
- **Intelligent Routing**: Determine which specialized agents to invoke
- **Parallel Execution**: Query multiple agents simultaneously
- **Response Synthesis**: Combine agent analyses into actionable insights
- **Recommendation Generation**: Provide next steps based on findings

## 🏗️ Architecture

```
User Query
    ↓
Orchestrator
    ├─→ Logs Agent (parallel)
    ├─→ Metrics Agent (parallel)
    └─→ Traces Agent (parallel)
    ↓
Synthesis & Response
```

## 🚀 API Endpoints

### POST /analyze
Analyze observability issues based on user query.

**Request:**
```json
{
  "query": "Why is the order service failing?",
  "time_range": "1h"
}
```

**Response:**
```json
{
  "query": "Why is the order service failing?",
  "summary": "The order service has a 10% error rate...",
  "agent_responses": {
    "logs": {...},
    "metrics": {...},
    "traces": {...}
  },
  "recommendations": [
    "Check ERROR_RATE environment variable",
    "Review database connection pool"
  ],
  "timestamp": "2025-11-08T10:30:00Z"
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "agents": {
    "logs": "reachable",
    "metrics": "reachable",
    "traces": "reachable"
  }
}
```

## 🔧 Configuration

Environment variables:

```bash
# Agent endpoints
AGENT_LOGS_URL=http://agent-logs:8002
AGENT_METRICS_URL=http://agent-metrics:8003
AGENT_TRACES_URL=http://agent-traces:8004

# LLM configuration
LLM_BASE_URL=http://172.17.0.1:12434/engines/llama.cpp/v1
LLM_API_KEY=dummy-token
LLM_MODEL=qwen3

# Server configuration
HOST=0.0.0.0
PORT=8001
LOG_LEVEL=INFO
```

## 🐳 Docker

Build and run:

```bash
docker build -t agent-orchestrator:latest .
docker run -p 8001:8001 agent-orchestrator:latest
```

## 🧪 Local Development

```bash
# Install dependencies
uv sync

# Run the orchestrator
uv run uvicorn agent_orchestrator.main:app --reload --host 0.0.0.0 --port 8001
```

## 📊 Decision Logic

The orchestrator uses LLM-based reasoning to:

1. **Parse Intent**: Understand what the user is asking
2. **Select Agents**: Determine which agents are needed
   - Logs: Error patterns, log analysis
   - Metrics: Performance issues, resource usage
   - Traces: Latency, service dependencies
3. **Execute in Parallel**: Query all selected agents simultaneously
4. **Synthesize**: Combine findings with context awareness
5. **Recommend**: Provide actionable next steps

## 🔄 Example Flow

**User Query**: "Analyze problems with the order service in the last hour"

**Orchestrator Actions**:
1. Detects services: `["order"]`
2. Routes to all 3 agents (logs, metrics, traces)
3. Receives responses:
   - Logs: 47 errors found
   - Metrics: 10% error rate, high latency
   - Traces: 15 failed spans in order flow
4. Synthesizes: "Order service experiencing DB errors..."
5. Recommends: Check ERROR_RATE config, review DB connections
