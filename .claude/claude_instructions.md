# Claude Instructions - Python OpenTelemetry Observability Project

## Documentation Structure

The project uses a **modular documentation approach**:

- **`README.md`** - Quick start guide for getting the project running (keep it concise!)
- **`docs/`** - Detailed documentation:
  - `architecture.md` - System architecture, components, technology stack
  - `agents.md` - AI agentic network architecture and usage
  - `development.md` - Local development guide, common module, LLM integrations
  - `configuration.md` - Environment variables, Grafana setup, customization
  - `troubleshooting.md` - Common issues and solutions
  - `contributing.md` - Contributing guidelines, code style, PR process

**Important**: When updating documentation, place detailed content in the appropriate `docs/` file and keep the README focused on quick start.

## Project Overview

This is a comprehensive microservices demonstration project showcasing Python auto-instrumentation with OpenTelemetry. It implements an order and stock management system with a complete observability stack and an AI-powered agentic network for intelligent observability analysis.

**Key Characteristics:**
- **Python 3.14+** using **UV** package manager
- Multiple microservices with FastAPI
- OpenTelemetry auto-instrumentation
- MCP (Model Context Protocol) integration for AI agents
- Complete Grafana stack (Loki, Mimir, Tempo)
- Unified `common` module for shared code (business models + agent utilities)

## Architecture

### Microservices (Business Logic)
- **customer** - Kafka producer simulating wood orders
- **supplier** - Kafka producer for stock replenishment
- **ordercheck** - Kafka consumer for order reception
- **suppliercheck** - Kafka consumer for stock management
- **stock** - Stock management REST API
- **order** - Order management REST API
- **ordermanagement** - Order status update service

### AI Agents (Observability Analysis)
- **agent-orchestrator** - Main coordinator that routes queries to specialized agents and synthesizes responses
- **agent-logs** - Specialized in Loki log analysis (LogQL)
- **agent-metrics** - Specialized in Mimir metrics analysis (PromQL)
- **agent-traces** - Specialized in Tempo trace analysis (TraceQL)
- **agents-common** - Shared models, MCP client, and utilities
- **agents-ui** - Web interface for interacting with the agentic network

### Infrastructure Components
- **Kafka** - Message broker for async communication
- **PostgreSQL** - Relational database for orders and stock
- **Grafana** - Observability visualization
- **Loki** - Log aggregation system
- **Mimir** - Metrics storage (Prometheus-compatible)
- **Tempo** - Distributed tracing backend
- **OpenTelemetry Collector** - OTLP gateway for telemetry data
- **Grafana MCP Server** - Model Context Protocol server for AI agents

## Technology Stack

### Python Ecosystem
- **Python 3.14+** - Latest stable version (required minimum)
- **uv** - Fast Python package installer and resolver (`uv sync` to install dependencies)
- **FastAPI** - Web framework for REST APIs and agents
- **Pydantic** - Data validation and settings management
- **SQLAlchemy** - ORM for database interactions
- **Kafka-python** - Kafka client library
- **LangChain** - Framework for LLM applications (agents only)

### Package Management with UV
Each service uses `pyproject.toml` for dependency management:
- **Install dependencies**: `uv sync` or `uv sync --frozen` for exact versions
- **Add dependency**: Edit `dependencies` array in `pyproject.toml`, then run `uv sync`
- **Dev dependencies**: Use `[dependency-groups].dev` section
- **Run commands**: Prefix with `uv run` (e.g., `uv run pytest`, `uv run python -m service.main`)

### Common Module (Unified)

The `common` module is the shared codebase for both microservices and AI agents:

**Location**: `common/common/`

**Business Models** (for microservices):
- `models.py` - WoodType, OrderStatus, Stock, Order, OrderTracking

**Agent Utilities** (for AI agents):
- `agent_models.py` - AgentRequest, AgentResponse, AgentType, OrchestratorResponse
- `mcp_client.py` - MCPGrafanaClient for querying Loki/Mimir/Tempo
- `llm_config.py` - get_llm() helper for LangChain configuration

**Usage**:
```python
# Import business models
from common import WoodType, OrderStatus, Stock, Order

# Import agent utilities
from common import MCPGrafanaClient, get_llm, AgentRequest, AgentResponse
```

**Important**: All agents depend on `common` in their `pyproject.toml`. The old `agents-common` module has been merged into `common`.

### Observability
- **OpenTelemetry** - Auto-instrumentation for traces, metrics, and logs
- **OTLP** - Protocol for sending telemetry data
- **LogQL** - Query language for Loki logs
- **PromQL** - Query language for Mimir metrics
- **TraceQL** - Query language for Tempo traces

### AI/LLM
- **LangChain** - Framework for building LLM applications
- **MCP (Model Context Protocol)** - Protocol for AI context enrichment
- **OpenAI-compatible APIs** - Used via Docker Model Runner locally

## Development Guidelines

### Code Structure

### Microservice Structure
```
service-name/
├── pyproject.toml          # Dependencies and metadata (Python 3.14+)
├── README.md               # Service-specific documentation
├── Dockerfile              # Container build (python:3.14-slim)
├── service_name/           # Main package directory
│   ├── __init__.py
│   ├── main.py            # Entry point (FastAPI app)
│   └── ...                # Service logic
└── tests/                 # Test suite
    └── __init__.py
```

### Agent Structure
```
agent-{name}/
├── pyproject.toml          # Dependencies (includes common)
├── README.md               # Agent-specific documentation
├── Dockerfile              # Container build (python:3.14-slim)
├── agent_{name}/           # Main package directory
│   ├── __init__.py
│   ├── main.py            # FastAPI app with /analyze and /health
│   └── {name}_analyzer.py # Analysis logic using MCPGrafanaClient
└── tests/                 # Test suite
    └── __init__.py
```

### Common Module Structure
```
common/
├── pyproject.toml          # Shared dependencies
├── common/
│   ├── __init__.py        # Exports all public symbols
│   ├── models.py          # Business models (microservices)
│   ├── agent_models.py    # Agent communication models
│   ├── mcp_client.py      # MCP Grafana client
│   └── llm_config.py      # LLM configuration helper
└── tests/
    └── __init__.py
```

### Python Conventions
1. **Type Hints**: Always use type annotations for better IDE support and type checking
2. **Pydantic Models**: Use for data validation and API schemas
3. **Async/Await**: Prefer async code for I/O operations (FastAPI, database, HTTP calls)
4. **Error Handling**: Implement proper exception handling with OpenTelemetry tracing
5. **Logging**: Use structured logging compatible with OpenTelemetry
6. **Docstrings**: Document public functions and classes with clear descriptions

### Commit Message Conventions

Follow **Conventional Commits 1.0.0** specification for explicit, machine-readable commit history.

**Structure:**
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types** (REQUIRED):
- `feat`: New feature (MINOR in SemVer)
- `fix`: Bug fix (PATCH in SemVer)
- `docs`: Documentation changes
- `style`: Code formatting (no logic change)
- `refactor`: Code restructuring (no feature/fix)
- `perf`: Performance improvements
- `test`: Test additions/corrections
- `build`: Build system changes
- `ci`: CI/CD configuration changes
- `chore`: Other changes (no src/test modification)

**Description** (REQUIRED):
- Imperative, present tense: "add" not "added"
- Lowercase, no period at end
- Concise (50 chars or less ideal)

**Breaking Changes**:
Use `!` before colon or `BREAKING CHANGE:` footer
```
feat!: remove support for Python 3.11
feat(api)!: change response format
```

**Examples:**
```
feat(agent-logs): add error pattern detection
fix(customer): prevent race condition in Kafka producer
docs: update MCP server setup instructions
refactor(common): extract MCP client to shared module
```

### OpenTelemetry Integration
All services are auto-instrumented. Key environment variables:
- `OTEL_EXPORTER_OTLP_ENDPOINT` - Collector endpoint
- `OTEL_SERVICE_NAME` - Service identifier
- `ERROR_RATE` - Simulated error rate for testing (0.0-1.0)

### Agent Development Patterns

#### MCP Client Usage
Agents use the MCP client from `agents-common` to query Grafana datasources:
```python
from agents_common.mcp_client import MCPClient

# Query Loki for logs
logs = await mcp_client.query_loki(query="LogQL query here")

# Query Mimir for metrics
metrics = await mcp_client.query_mimir(query="PromQL query here")

# Query Tempo for traces
traces = await mcp_client.query_tempo(query="TraceQL query here")
```

#### Agent Specialization
- **Logs Agent**: Focus on error patterns, log aggregation, temporal analysis
- **Metrics Agent**: Analyze performance, detect anomalies, threshold alerts
- **Traces Agent**: Identify bottlenecks, service dependencies, error propagation
- **Orchestrator**: Route requests, coordinate parallel queries, synthesize results

### Common Development Tasks

#### Running Services Locally
```bash
# With auto-instrumentation
uv run opentelemetry-instrument \
    --traces_exporter otlp \
    --metrics_exporter otlp \
    --service_name <service-name> \
    --exporter_otlp_endpoint http://localhost:4318 \
    python -m <service_name>.main
```

#### Docker Development
```bash
# Start all services
docker-compose up -d

# Rebuild specific service
docker-compose up --build <service-name>

# View logs
docker-compose logs -f <service-name>

# Restart MCP server after token update
docker-compose restart grafana-mcp
```

#### Testing
Each service should have tests. Run with:
```bash
cd <service-directory>
uv run pytest
```

## Configuration Management

### Environment Variables
All configuration is managed via `.env` file (copy from `.env.example`). Key variables:
- `DOCKER_REGISTRY` - Docker registry prefix (empty for Docker Hub)
- `IMG_*` - Image versions for all services
- `ERROR_RATE` - Simulated error rate (default: 0.1)
- `GRAFANA_SERVICE_ACCOUNT_TOKEN` - Token for MCP server authentication

### Service Configuration
- Loki: `config/loki/loki-config.yml`
- Mimir: `config/mimir/mimir-config.yml`
- Tempo: `config/tempo/tempo.yml`
- OTEL Collector: `config/otel/otel-conf.yml`
- Grafana Datasources: `config/grafana/datasources/default.yaml`

## MCP (Model Context Protocol) Integration

### Architecture
The MCP server (`grafana-mcp`) acts as a unified gateway for AI agents to query Grafana datasources:
- **URL**: `http://grafana-mcp:8000/sse` (SSE transport)
- **Authentication**: Uses `GRAFANA_SERVICE_ACCOUNT_TOKEN`
- **Supported Datasources**: Loki, Mimir, Tempo

### Creating Grafana Service Account
1. Navigate to Grafana UI (http://localhost:3000)
2. Configuration → Service accounts → Create service account
3. Generate token and copy it
4. Add to `.env`: `GRAFANA_SERVICE_ACCOUNT_TOKEN=eyJ...`
5. Restart MCP service: `docker-compose restart grafana-mcp`

## Debugging and Troubleshooting

### Common Issues

#### Services Not Sending Telemetry
1. Check OTEL Collector is running: `docker-compose ps otel-gateway`
2. Verify endpoint configuration in service environment
3. Check collector logs: `docker-compose logs -f otel-gateway`

#### MCP Server Connection Errors
1. Verify `GRAFANA_SERVICE_ACCOUNT_TOKEN` is set in `.env`
2. Check token has proper permissions in Grafana
3. Ensure MCP service is running: `docker-compose ps grafana-mcp`
4. Review MCP logs: `docker-compose logs -f grafana-mcp`

#### Agent Query Failures
1. Verify Grafana datasources are configured correctly
2. Check if data exists in Loki/Mimir/Tempo
3. Test queries directly in Grafana Explore UI
4. Review agent logs for detailed error messages

## Code Quality Standards

### Before Committing
1. **Type Checking**: Ensure code passes type checks
2. **Formatting**: Code should be well-formatted (consider using ruff or black)
3. **Testing**: Add/update tests for new functionality
4. **Documentation**: Update README and docstrings
5. **OpenTelemetry**: Verify auto-instrumentation works correctly

### Pull Request Guidelines
1. Provide clear description of changes
2. Reference related issues
3. Include test results
4. Document any new environment variables
5. Update architecture documentation if needed

## Useful Resources

### Access Points
- Grafana: http://localhost:3000 (admin/admin)
- AKHQ (Kafka UI): http://localhost:8080
- Adminer (DB): http://localhost:8081

### Documentation
- OpenTelemetry Python: https://opentelemetry.io/docs/languages/python/
- FastAPI: https://fastapi.tiangolo.com/
- LangChain: https://python.langchain.com/
- Grafana Loki LogQL: https://grafana.com/docs/loki/latest/query/
- Prometheus PromQL: https://prometheus.io/docs/prometheus/latest/querying/basics/
- Tempo TraceQL: https://grafana.com/docs/tempo/latest/traceql/

## Project-Specific Patterns

### Error Simulation
Services support controlled error injection via `ERROR_RATE`:
- Used in `customer` and `suppliercheck` services
- Helps test observability stack under failure conditions
- Simulates DB errors, network failures, etc.

### Parallel Agent Execution
The orchestrator executes specialized agents in parallel:
- Improves response time for complex queries
- Each agent returns independent analysis
- Results are synthesized into coherent answer

### Service Communication
- **Sync**: REST APIs (order, stock) using FastAPI
- **Async**: Kafka messages for event-driven flows
- **Agents**: HTTP requests to orchestrator, MCP for datasource queries

## When Making Changes

### Adding New Microservice
1. Create directory with pyproject.toml
2. Implement with OpenTelemetry auto-instrumentation
3. Add Dockerfile (follow existing patterns)
4. Update docker-compose.yml
5. Document in README.md
6. Add to architecture diagrams

### Adding New Agent
1. Create `agent-{name}` directory with standard structure
2. Add `common` as dependency in `pyproject.toml`
3. Create analyzer class using `MCPGrafanaClient` from common
4. Implement FastAPI app with `/analyze` and `/health` endpoints
5. Create Dockerfile (copy pattern from existing agents)
6. Add service to `docker-compose.yml`
7. Update `agent-orchestrator` to include new agent
8. Add tests for agent logic
9. Update architecture documentation in README.md

**Example pyproject.toml for new agent**:
```toml
[project]
name = "agent-{name}"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.32.0",
    "common",  # Includes MCPGrafanaClient, get_llm, agent models
]
```

### Modifying Configuration
1. Update `.env.example` with new variables
2. Document in README.md
3. Update relevant config files in `config/`
4. Test with `docker-compose up --build`

## Security Considerations

1. **Never commit** `.env` files with secrets
2. **Service accounts** should have minimal required permissions
3. **API tokens** should be rotated regularly
4. **Network isolation** - use Docker networks appropriately
5. **Input validation** - always validate data with Pydantic

## Performance Notes

- Use `COMPOSE_PARALLEL_LIMIT` to control Docker build parallelism
- Enable `DOCKER_BUILDKIT=1` for faster builds
- Monitor resource usage in docker-compose.yml limits
- Consider volume mounts for development hot-reload
