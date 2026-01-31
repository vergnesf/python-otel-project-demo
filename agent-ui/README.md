# Agent UI

Reflex-based web interface for interacting with the observability agentic network.

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
User → Reflex UI → Orchestrator → [Logs, Metrics, Traces] Agents → MCP → Grafana Stack
```

## 🚀 Running the UI

### Development Mode

```bash
# Install dependencies
uv sync

# Run development server
uv run reflex run

# Access at http://localhost:3002
```

### Production Mode

```bash
# Build for production
uv run reflex export

# Run production server
uv run reflex run --env prod
```

## 📦 Dependencies

- `reflex`: Web framework for Python
- `common-ai`: Shared AI utilities (agent models)

## 🐳 Docker

The UI is containerized and runs as part of the docker-compose stack:

```bash
docker-compose up agent-ui
```

Access at: **http://localhost:3002**

## 🔧 Configuration

Environment variables:

```bash
# Orchestrator endpoint
ORCHESTRATOR_URL=http://agent-orchestrator:8001

# UI server configuration
REFLEX_HOST=0.0.0.0
REFLEX_PORT=3002
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

Reflex handles state management with:
- `ChatState`: Manages conversation history
- `messages`: List of chat messages
- `is_loading`: Shows loading indicator
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
│   ├── agent_ui.py      # Main Reflex app
│   ├── state.py          # State management
│   └── components/       # UI components
│       ├── chat.py
│       ├── message.py
│       └── sidebar.py
├── assets/               # Static assets
├── pyproject.toml
└── rxconfig.py          # Reflex configuration
```

### Adding Features

To extend the UI:

1. Add new components in `components/`
2. Update state in `state.py`
3. Modify layout in `agent_ui.py`
4. Style with Tailwind classes

## 🎨 Styling

The UI uses:
- **Reflex Components**: Pre-built React components
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
