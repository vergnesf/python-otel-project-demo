# Agent UI

FastAPI-based web interface for interacting with the observability agentic network.

## 📊 Features

- Chat interface for natural language queries
- Real-time streaming of agent responses
- Rich response formatting with code blocks
- Multi-agent response visualization
- Grafana integration with direct links
- Response history and session management

## 🏗️ Architecture

The UI communicates with the **Orchestrator Agent** which coordinates the specialized agents:

```
User → FastAPI UI → Orchestrator → [Logs, Metrics, Traces] Agents → MCP → Grafana Stack
```

## 🚀 Running the UI

### Development Mode

```bash
# Install dependencies
uv sync

# Run development server
uv run start-dev

# Or directly
uv run uvicorn agent_ui.main:app --reload

# Access at http://localhost:8000
```

### Production Mode

```bash
# Run production server
uv run start

# Or directly
uv run uvicorn agent_ui.main:app --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run all tests
uv run test

# Or directly
pytest tests/ -v
```

## 🐳 Development with Podman

### Quick Start

```bash
# Build the image
make podman-build-ui

# Rebuild and restart (forces fresh build)
make podman-rebuild-ui

# Start all services
make podman-up

# Stop all services
make podman-down

# Full rebuild and restart (clean slate)
make podman-rebuild
```

### Manual Commands

```bash
# Build the Docker image
cd agent-ui
podman build -t agent-ui:latest .
cd ..

# Force rebuild with podman-compose
podman-compose build --no-cache agent-ui

# Restart the service
podman-compose restart agent-ui

# View logs
podman-compose logs -f agent-ui
```

### Ensuring Fresh Builds

To ensure you always have the latest code:

```bash
# 1. Stop the service
podman-compose down agent-ui

# 2. Remove old containers
podman rm -f agent-ui

# 3. Remove old images
podman rmi agent-ui:latest

# 4. Rebuild
cd agent-ui
podman build -t agent-ui:latest .
cd ..

# 5. Restart
podman-compose up -d agent-ui
```

### Quick Rebuild Script

For the easiest way to ensure you have the latest code, use the provided rebuild script:

```bash
# Make sure the script is executable
chmod +x agent-ui/rebuild.sh

# Run the rebuild script
./agent-ui/rebuild.sh
```

This script will:
1. Stop the running service
2. Remove old containers and images
3. Rebuild with fresh code (no cache)
4. Restart the service
5. Show build information

### Debugging

```bash
# Check running containers
podman ps

# Inspect container
podman inspect agent-ui

# Enter container shell
podman exec -it agent-ui /bin/bash

# Check service logs
podman-compose logs agent-ui

# Check port mapping
podman port agent-ui

# Check build info
podman exec agent-ui cat /app/BUILD_INFO.txt
```

### Pro Tips

1. **Always use `--no-cache`** when building to ensure fresh code:
   ```bash
   podman build --no-cache -t agent-ui:latest .
   ```

2. **Use build arguments** to force rebuilds:
   ```bash
   podman build --no-cache -t agent-ui:latest --build-arg BUILD_TIMESTAMP=$(date +%s) .
   ```

3. **Check the build info** to verify your code is up to date:
   ```bash
   podman exec agent-ui cat /app/BUILD_INFO.txt
   ```

4. **Use `make` commands** for common operations (see root Makefile)

## 📦 Dependencies

- `fastapi`: Web framework for Python
- `uvicorn`: ASGI server
- `jinja2`: Templating engine
- `httpx`: HTTP client
- `pydantic`: Data validation

## 🐳 Docker

The UI is containerized and runs as part of the docker-compose stack:

```bash
docker-compose up agent-ui
```

Access at: **http://localhost:8000**

## 🔧 Configuration

Environment variables:

```bash
# Orchestrator endpoint
ORCHESTRATOR_URL=http://agent-orchestrator:8001

# UI server configuration
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
```

## 💬 Example Queries

### General Observability
- "What's happening in the system?"
- "Show me recent errors"
- "Analyze performance issues"

### Service-Specific
- "Why is the order service failing?"
- "Check order service performance"
- "Show me order service logs"

### Time-Based
- "Errors in the last hour"
- "Performance trends over 24 hours"
- "What changed in the last 30 minutes?"

### Multi-Service
- "Analyze the customer to order flow"
- "Show dependencies between services"
- "Where are errors happening?"

## 🎨 UI Components

### Chat Message
Each message shows:
- **User Query**: What you asked
- **Agent Analysis**: Combined response from all agents
- **Grafana Links**: Quick access to dashboards
- **Timestamp**: When the analysis was performed

### Response Sections
Responses are organized by agent:
- **📜 Logs Analysis**: Error patterns from Loki
- **📊 Metrics Analysis**: Performance data from Mimir
- **🛤️ Traces Analysis**: Request flows from Tempo
- **💡 Recommendations**: Actionable next steps

## 🔄 State Management

FastAPI handles state management with:
- `ChatState`: Manages conversation history
- `chats`: List of QA pairs
- `processing`: Shows loading indicator
- `send_message()`: Sends query to orchestrator

## 📱 Responsive Design

The UI is fully responsive:
- **Desktop**: Full-width chat with sidebar
- **Tablet**: Optimized layout
- **Mobile**: Stack layout for small screens

## 🎯 User Flow

1. User types question in chat input
2. UI sends request to Orchestrator
3. Loading indicator shows while agents work
4. Response streams back with analysis
5. User can click Grafana links for details
6. History preserved for context

## 🛠️ Development

### File Structure

```
agent-ui/
├── agent_ui/
│   ├── __init__.py
│   ├── main.py          # Main FastAPI app
│   ├── state.py          # State management
│   └── templates/       # Jinja2 templates
│       ├── base.html
│       └── index.html
├── pyproject.toml
└── Dockerfile
```

### Adding Features

To extend the UI:

1. Add new templates in `templates/`
2. Update state in `state.py`
3. Add new routes in `main.py`
4. Style with Tailwind CSS

## 🎨 Styling

The UI uses:
- **Jinja2 Templates**: HTML templates with Python
- **Tailwind CSS**: Utility-first styling
- **Custom Theme**: Observability-focused colors
- **Dark Mode**: Eye-friendly for monitoring

## 📊 Example Response

**Query**: "Why is order service failing?"

**Response**:
```
📜 Logs Analysis
Found 47 error logs in the last hour.
Primary error: 'Simulated DB insertion error' (42 occurrences).

📊 Metrics Analysis
Order service shows 10.2% HTTP 500 error rate.
Request latency p95: 245ms (above baseline).

🛤️ Traces Analysis
Analyzed 150 traces. Found 15 failed traces (10%).
Bottleneck: order.POST /orders (312ms average).

💡 Recommendations
1. Check ERROR_RATE environment variable
2. Review database connection pool settings
3. Investigate DB query performance

[View Logs in Grafana] [View Metrics] [View Traces]
```

## 🔗 Integration

The UI integrates with:
- **Orchestrator**: Main analysis coordinator
- **Grafana**: Deep-dive into data
- **MCP**: Indirect via orchestrator and agents

## 🐳 Podman Compose (rebuild a service)

To force the rebuild of a service without restarting the entire stack:

```bash
podman compose up -d --build --force-recreate --no-deps <service>
```

To ensure a rebuild without cache:

```bash
podman compose build --no-cache <service>
podman compose up -d --force-recreate --no-deps <service>
```
