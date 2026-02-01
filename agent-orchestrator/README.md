# Agent Orchestrator

Main coordinator of the observability agentic network.

## 📊 Features

- User query processing and routing
- Language detection and translation
- Intelligent agent selection (logs, metrics, traces)
- Response synthesis and validation
- Multi-agent coordination and parallel execution

## 🏗️ Architecture

```
User Query (FR/EN)
    ↓
┌─────────────────────────────────────────┐
│         ORCHESTRATOR                    │
│                                         │
│  1. Detect Language & Translate         │
│  2. Route to Agents                     │
│  3. Call Agents (parallel)              │
│  4. Validate Responses                  │
└─────────────────────────────────────────┘
    ├─→ Logs Agent (parallel)
    ├─→ Metrics Agent (parallel)
    └─→ Traces Agent (parallel)
    ↓
Validated Response with Summary
```
> **Note**: External access via Traefik at `http://localhost:8010/agents/orchestrator/`. Internal services communicate directly via Docker network.
## 🚀 API Endpoints

### POST /analyze
Analyze observability issues based on user query.

**Request:**
```json
{
  "query": "Show me recent errors",
  "time_range": "1h"
}
```

**Response:**
```json
{
  "query": "Show me recent errors",
  "translated_query": "Show me recent errors",
  "language": "english",
  "routing": {
    "agents": ["logs"],
    "reason": "Error query routed to logs agent"
  },
  "agent_responses": {
    "logs": {
      "analysis": "Found 5 errors in customer service...",
      "recommendations": ["Check database connection"],
      "data": {"error_count": 5}
    }
  },
  "validation": {
    "validated": true,
    "issues": [],
    "suggestion": "Response is complete"
  },
  "summary": "...",
  "recommendations": [...],
  "timestamp": "2025-11-17T..."
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

# Agent call timeout (seconds)
AGENT_CALL_TIMEOUT=60

# LLM configuration
LLM_BASE_URL=http://172.17.0.1:12434/engines/llama.cpp/v1
LLM_API_KEY=dummy-token
LLM_MODEL=qwen3
LLM_EPHEMERAL_PER_CALL=false  # Set to true for fresh LLM instance per call

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

### Installation

```bash
# Install dependencies
cd agent-orchestrator
uv sync --dev
```

### Running the Service

```bash
# Run with auto-reload (development)
uv run uvicorn agent_orchestrator.main:app --reload --host 0.0.0.0 --port 8001

# Or with environment variables
PORT=8001 LOG_LEVEL=DEBUG uv run uvicorn agent_orchestrator.main:app --reload
```

## 📦 Dependencies

- `httpx`: HTTP client for API calls
- `langchain`: LLM framework
- `common-ai`: Shared AI utilities (MCP client, LLM config, agent models)

### Testing the Service

```bash
# Quick health check
# Via Traefik (external access)
curl http://localhost:8080/agents/orchestrator/health

# Or direct internal access (from containers)
curl http://agent-orchestrator:8001/health

# Test with an English query (via Traefik)
curl -X POST http://localhost:8080/agents/orchestrator/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me recent errors", "time_range": "1h"}'

# Test with a French query (via Traefik)
curl -X POST http://localhost:8080/agents/orchestrator/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Montre-moi les erreurs récentes", "time_range": "1h"}'
```

## 🧪 Tests

The orchestrator has comprehensive test coverage for all 3 functionalities.

### Unit Tests (Recommended for Development)

**22 unit tests** covering all core functionalities with mocks (fast, ~1-2 seconds):

```bash
# Run all unit tests
uv run pytest

# Or with pytest directly (if in venv)
pytest

# Run specific test classes
uv run pytest tests/test_orchestrator_core.py::TestLanguageDetectionAndTranslation  # Translation tests
uv run pytest tests/test_orchestrator_core.py::TestAgentRouting                    # Routing tests
uv run pytest tests/test_orchestrator_core.py::TestResponseValidation              # Validation tests

# Run a single test
uv run pytest tests/test_orchestrator_core.py::TestLanguageDetectionAndTranslation::test_detect_english_query -v
```

**Test breakdown:**
- ✅ Language detection & translation: 5 tests
- ✅ Agent routing: 9 tests
- ✅ Response validation: 5 tests
- ✅ End-to-end flow: 3 tests

### Integration Tests

**4 integration tests** with real HTTP calls:

**REQUIREMENTS:**
- ✅ Orchestrator must be running (accessible at `http://localhost:8080/agents/orchestrator/` or internally at `http://agent-orchestrator:8001`)
- ✅ **LLM must be running at `http://172.17.0.1:12434/v1`** (docker-compose default)

All integration tests **require a working LLM**. The tests use the hardcoded LLM URL from docker-compose.

**Running integration tests:**

```bash
# Step 1: Make sure docker-compose services are running
docker compose up -d

# Step 2: Verify orchestrator is accessible
curl http://localhost:8080/agents/orchestrator/health

# Step 2: Start orchestrator (Terminal 1)
uv run uvicorn agent_orchestrator.main:app --port 8001

# Step 3: Run integration tests (Terminal 2)
uv run python tests/test_orchestrator_integration.py
```

**Coverage:**
1. Language detection and translation (3 test cases)
2. Agent routing (4 test cases)
3. Response validation (2 test cases)
4. Complete workflow (1 test case)

### Useful Pytest Options

```bash
# Stop at first failure
uv run pytest -x

# Extra verbose
uv run pytest -vv

# Quick mode (less verbose)
uv run pytest -q

# Show available tests without running
uv run pytest --collect-only

# Run only unit tests (with marker)
uv run pytest -m unit

# Run with coverage report
uv run pytest --cov=agent_orchestrator --cov-report=html
```

### Expected Test Results

```
======================== 22 passed in 1.21s ========================
```

## 🐛 Debugging

### Enable Debug Logging

```bash
# Set log level to DEBUG
LOG_LEVEL=DEBUG uv run uvicorn agent_orchestrator.main:app --reload --port 8001
```

### Check Agent Connectivity

```bash
# Health endpoint shows agent status
curl http://localhost:8001/health

# Expected response:
{
  "status": "healthy",
  "agents": {
    "logs": "reachable",
    "metrics": "reachable",
    "traces": "reachable"
  }
}
```

### Common Issues

**Issue: Tests fail with "LLM not available"**
- Unit tests use mocks, so this shouldn't happen
- For integration tests, check your LLM configuration

**Issue: "Connection refused" in integration tests**
- Make sure the orchestrator is running: `uv run uvicorn agent_orchestrator.main:app --port 8001`

**Issue: Slow tests**
- Use unit tests for rapid development: `uv run pytest tests/test_orchestrator_core.py`
- Integration tests make real HTTP calls and can be slower

**Issue: Import errors**
- Install dependencies: `uv sync --dev`

### Viewing Logs

```bash
# Follow logs in real-time
LOG_LEVEL=INFO uv run uvicorn agent_orchestrator.main:app --reload | tee orchestrator.log

# Check for specific errors
grep ERROR orchestrator.log
```

## 📊 Prompts for Small Language Models

All prompts are optimized for SLMs with these characteristics:

✅ **Short and direct** - No unnecessary context
✅ **Strict format** - JSON responses only
✅ **Clear instructions** - One task per prompt
✅ **Examples included** - Response format shown
✅ **No explanations** - Only requested output

**Prompts location**: `agent_orchestrator/prompts/`

1. `detect_language.md` - Detects if text is in English
2. `translate_to_english.md` - Translates to English
3. `route_agents.md` - Decides which agents to call
4. `validate_response.md` - Validates response quality

## 🔄 Example Workflows

### French Query Workflow

```
Input: "Montre-moi les erreurs récentes"
  ↓
1. Language Detection → "non-english"
  ↓
2. Translation → "Show me recent errors"
  ↓
3. Routing → agents: ["logs"]
  ↓
4. Logs Agent Call → {"analysis": "Found 5 errors..."}
  ↓
5. Validation → {"validated": true}
  ↓
Output: Complete response with validation
```

### Multi-Agent Query

```
Input: "Show errors and CPU usage"
  ↓
1. Language Detection → "english"
  ↓
2. Routing → agents: ["logs", "metrics"]
  ↓
3. Parallel Calls:
   - Logs Agent → Error analysis
   - Metrics Agent → CPU metrics
  ↓
4. Validation → Check responses
  ↓
Output: Combined analysis
```

## 📈 Performance

- **Unit tests**: ~1.2 seconds for 22 tests
- **Integration tests**: ~30-60 seconds (depends on LLM)
- **Agent routing**: Uses only necessary agents (not all 3)
- **Parallel execution**: All selected agents called simultaneously

## 📚 Documentation

- See `/docs/orchestrator-simplified.md` for detailed architecture
- See `/docs/ai-prompts-architecture.md` for prompt design principles
- See project root `/docs/` for overall system documentation

## 🔜 Future Improvements

- [ ] Add caching for frequent translations
- [ ] Add performance metrics for each step
- [ ] Optimize prompts to reduce token usage
- [ ] Add support for more languages
- [ ] Implement response streaming

## 🐳 Podman Compose

### Redeploy Command

Use the generic `redeploy` command from the root Makefile to rebuild any service:

```bash
# Redeploy any service (agent-orchestrator, agent-logs, etc.)
make redeploy agent-orchestrator
```

This command will:
1. Stop the specified service
2. Rebuild with `--no-cache` to ensure fresh code
3. Restart the service

**Note:** If no service is specified, the command will show an error with usage instructions.
