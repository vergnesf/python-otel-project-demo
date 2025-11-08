# Contributing Guide

## Code Style

- **Type Hints**: Always use type annotations for better IDE support
- **Async/Await**: Prefer async code for I/O operations
- **Error Handling**: Implement proper exception handling with logging
- **Documentation**: Add docstrings to public functions and classes
- **Testing**: Write tests for new functionality

## Commit Message Convention

Follow **Conventional Commits 1.0.0** specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: New feature (MINOR in SemVer)
- `fix`: Bug fix (PATCH in SemVer)
- `docs`: Documentation changes
- `refactor`: Code restructuring (no feature/fix)
- `perf`: Performance improvements
- `test`: Test additions/corrections
- `chore`: Other changes

### Examples

```bash
feat(agent-logs): add error pattern detection
fix(customer): prevent race condition in Kafka producer
docs: update MCP server setup instructions
refactor(common): extract MCP client to shared module
```

## Adding a New Microservice

1. **Create directory structure**:
   ```
   my-service/
   ├── pyproject.toml
   ├── Dockerfile
   ├── my_service/
   │   ├── __init__.py
   │   └── main.py
   └── tests/
       └── __init__.py
   ```

2. **Setup pyproject.toml**:
   ```toml
   [project]
   name = "my-service"
   version = "0.1.0"
   requires-python = ">=3.14"
   dependencies = [
       "fastapi>=0.115.0",
       "uvicorn>=0.32.0",
       "common",  # If you need business models
   ]
   ```

3. **Implement with OpenTelemetry**:
   ```python
   from fastapi import FastAPI
   from common import WoodType, Order

   app = FastAPI()

   @app.get("/")
   def read_root():
       return {"service": "my-service"}
   ```

4. **Create Dockerfile**:
   ```dockerfile
   ARG DOCKER_REGISTRY=""
   ARG IMG_PYTHON="python:3.14-slim"
   FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

   WORKDIR /app

   COPY my-service/pyproject.toml /app/
   COPY my-service/my_service /app/my_service
   COPY common/common/ /app/common/common

   RUN pip install uv && uv add pip

   EXPOSE 8000

   CMD ["uv", "run", "uvicorn", "my_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

5. **Add to docker-compose.yml**:
   ```yaml
   my-service:
     build:
       context: .
       dockerfile: my-service/Dockerfile
       args:
         DOCKER_REGISTRY: ${DOCKER_REGISTRY}
         IMG_PYTHON: ${IMG_PYTHON:-python:3.14-slim}
     container_name: my-service
     ports:
       - "8005:8000"
     environment:
       - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-gateway:4318
       - OTEL_SERVICE_NAME=my-service
     networks:
       - otel-network
     depends_on:
       - otel-gateway
   ```

6. **Add tests**:
   ```python
   # tests/test_main.py
   from fastapi.testclient import TestClient
   from my_service.main import app

   client = TestClient(app)

   def test_read_root():
       response = client.get("/")
       assert response.status_code == 200
       assert response.json() == {"service": "my-service"}
   ```

7. **Update documentation**:
   - Add service description to `docs/architecture.md`
   - Update architecture diagrams if needed

## Adding a New Agent

1. **Create agent directory**:
   ```
   agent-myagent/
   ├── pyproject.toml
   ├── Dockerfile
   ├── agent_myagent/
   │   ├── __init__.py
   │   ├── main.py
   │   └── myagent_analyzer.py
   └── tests/
       └── __init__.py
   ```

2. **Setup pyproject.toml**:
   ```toml
   [project]
   name = "agent-myagent"
   version = "0.1.0"
   requires-python = ">=3.14"
   dependencies = [
       "fastapi>=0.115.0",
       "uvicorn>=0.32.0",
       "common",  # Includes MCPGrafanaClient, get_llm, models
   ]
   ```

3. **Create analyzer using MCPGrafanaClient**:
   ```python
   # agent_myagent/myagent_analyzer.py
   import logging
   import os
   from typing import Any
   from common import MCPGrafanaClient

   logger = logging.getLogger(__name__)

   class MyAgentAnalyzer:
       def __init__(self):
           mcp_url = os.getenv("MCP_GRAFANA_URL", "http://grafana-mcp:8000")
           self.mcp_client = MCPGrafanaClient(base_url=mcp_url)

       async def close(self):
           await self.mcp_client.close()

       async def analyze(self, query: str, time_range: str = "1h", context: dict = None) -> dict[str, Any]:
           # Your analysis logic here
           # Use self.mcp_client.query_logs(), query_metrics(), or query_traces()
           return {
               "agent_name": "myagent",
               "analysis": "Analysis result...",
               "data": {},
               "confidence": 0.8,
           }
   ```

4. **Create FastAPI app**:
   ```python
   # agent_myagent/main.py
   from fastapi import FastAPI
   from pydantic import BaseModel
   from .myagent_analyzer import MyAgentAnalyzer

   app = FastAPI(title="MyAgent API")
   analyzer = MyAgentAnalyzer()

   class AnalyzeRequest(BaseModel):
       query: str
       time_range: str = "1h"
       context: dict = {}

   @app.post("/analyze")
   async def analyze(request: AnalyzeRequest):
       return await analyzer.analyze(request.query, request.time_range, request.context)

   @app.get("/health")
   async def health():
       mcp_status = await analyzer.mcp_client.health_check()
       return {"status": "healthy" if mcp_status else "unhealthy"}
   ```

5. **Create Dockerfile** (same pattern as other agents)

6. **Add to docker-compose.yml**

7. **Update orchestrator**:
   ```python
   # agent-orchestrator/agent_orchestrator/orchestrator.py
   self.myagent_url = os.getenv("AGENT_MYAGENT_URL", "http://agent-myagent:8006")

   # Add to parallel query in analyze() method
   ```

8. **Add tests and documentation**

## Code Review Guidelines

Before submitting a pull request:

1. **Code Quality**:
   - Run `uv run ruff format .`
   - Run `uv run ruff check .`
   - Fix any linting errors

2. **Tests**:
   - Add tests for new functionality
   - Ensure existing tests pass: `uv run pytest`
   - Aim for >80% code coverage

3. **Type Checking**:
   - Add type hints to all functions
   - Run `uv run mypy .` if configured

4. **Documentation**:
   - Update README or docs/ if needed
   - Add docstrings to public functions
   - Update architecture diagrams if structure changes

5. **Commits**:
   - Follow Conventional Commits specification
   - Keep commits atomic and focused
   - Write clear commit messages

## Pull Request Process

1. **Fork and Branch**:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make Changes**:
   - Implement your feature
   - Add tests
   - Update documentation

3. **Test Locally**:
   ```bash
   # Run tests
   uv run pytest

   # Test with Docker
   docker-compose up --build my-service

   # Verify no breaking changes
   docker-compose up -d
   ```

4. **Commit**:
   ```bash
   git add .
   git commit -m "feat(my-service): add new capability"
   ```

5. **Push and Create PR**:
   ```bash
   git push origin feature/my-new-feature
   ```

   Then create a pull request on GitHub with:
   - Clear description of changes
   - Reference to related issues
   - Screenshots if UI changes
   - Test results

6. **Address Review Comments**:
   - Make requested changes
   - Push new commits to the same branch
   - PR will update automatically

## Development Workflow

### Local Development Cycle

```bash
# Make changes
vim agent-logs/agent_logs/logs_analyzer.py

# Test locally
cd agent-logs/
uv run pytest

# Test with Docker
docker-compose up --build agent-logs

# Check logs
docker-compose logs -f agent-logs
```

### Testing Changes

```bash
# Unit tests
uv run pytest

# Integration tests (with Docker)
docker-compose up -d
# Run integration tests or manual tests
docker-compose down

# Full stack test
docker-compose up --build -d
# Test all functionality
docker-compose logs -f
```

## Releasing

Maintainers use semantic versioning:

- `feat:` commits → MINOR version bump (0.X.0)
- `fix:` commits → PATCH version bump (0.0.X)
- `feat!:` or `BREAKING CHANGE:` → MAJOR version bump (X.0.0)

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Check existing documentation in `docs/`
