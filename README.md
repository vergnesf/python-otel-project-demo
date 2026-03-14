# Python OpenTelemetry Demo 🐍

> A comprehensive microservices platform showcasing Python auto-instrumentation with OpenTelemetry and AI-powered observability analysis

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-enabled-blueviolet)](https://opentelemetry.io/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)](https://www.docker.com/)

## 🚀 Quick Start

For a complete getting started guide including Docker, Podman, and GPU setup, see [GETTING_STARTED.md](GETTING_STARTED.md).

Note: the compose configuration is split across multiple files. Use the provided Taskfile helpers to bring the full stack up and down in the correct order (requires [go-task](https://taskfile.dev), install: `mise use task@latest` or `brew install go-task`):

- `task compose-up` — starts observability → db → kafka → ai-tools → ai → apps → traefik
- `task compose-down` — stops services in reverse order and removes orphans

## 📚 Documentation

📚 **Detailed documentation available in the [`docs/`](docs/) directory:**

- **[Architecture](docs/architecture.md)** - System architecture, components, and data flow
- **[Agents](docs/agents.md)** - AI agentic network architecture and usage
- **[Prompts](docs/prompts.md)** - Prompt engineering and AI query patterns
- **[Docker Security](docs/docker-security.md)** - Security best practices
- **[Handbook](docs/handbook/)** - Quick reference guides:
  - [Development](docs/handbook/development.md) - Local development workflow
  - [Configuration](docs/handbook/configuration.md) - Environment setup
  - [Troubleshooting](docs/handbook/troubleshooting.md) - Common issues

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Business Application (Order & Stock Management)            │
│  customer → kafka → ordercheck → order → postgres          │
│  supplier → kafka → suppliercheck → stock → postgres       │
└─────────────────────────────────────────────────────────────┘
                          ↓ OTLP
┌─────────────────────────────────────────────────────────────┐
│  Observability Stack (Grafana, Loki, Mimir, Tempo)         │
└─────────────────────────────────────────────────────────────┘
                          ↑ MCP Protocol
┌─────────────────────────────────────────────────────────────┐
│  AI Agentic Network (Orchestrator + Specialized Agents)     │
│  User → Orchestrator → Logs/Metrics/Traces Agents          │
└─────────────────────────────────────────────────────────────┘
```

See [Architecture Documentation](docs/architecture.md) for detailed diagrams.

## 🎯 Features

✨ **Complete Observability Stack** - Grafana, Loki, Mimir, Tempo with OpenTelemetry auto-instrumentation
🤖 **AI-Powered Analysis** - Intelligent agents for natural language observability queries
🏗️ **Production-Ready** - Docker-first, Python 3.14, UV package manager, FastAPI
🎭 **Error Simulation** - Built-in configurable error injection for testing

## 🔧 Technology Stack

- **Python 3.14** - Latest stable Python
- **UV** - Fast Python package manager
- **FastAPI** - Modern web framework
- **OpenTelemetry** - Observability instrumentation
- **Grafana Stack** - Loki (logs), Mimir (metrics), Tempo (traces)
- **LangChain** - LLM framework for AI agents
- **Kafka** - Message streaming
- **PostgreSQL** - Relational database

## 🗂️ Project Structure

```
├── lib-models/          # Shared business models (WoodType, Order, Stock)
├── lib-ai/              # Shared AI utilities (MCP client, LLM config, agent models)
├── ms-customer/         # Microservice: Customer orders (Kafka producer)
├── ms-order/            # Microservice: Order management API
├── ms-stock/            # Microservice: Stock management API
├── ms-supplier/         # Microservice: Supplier (Kafka producer)
├── ms-ordercheck/       # Microservice: Order processing (Kafka consumer)
├── ms-suppliercheck/    # Microservice: Stock updates (Kafka consumer)
├── ms-ordermanagement/  # Microservice: Order status updates
├── agent-orchestrator/  # AI Agent: Main coordinator
├── agent-logs/          # AI Agent: Loki log analysis
├── agent-metrics/       # AI Agent: Mimir metrics analysis
├── agent-traces/        # AI Agent: Tempo traces analysis
├── agent-ui/           # Web UI for agents
├── config/              # Configuration files (Grafana, Loki, Mimir, Tempo)
├── docs/                # Documentation
└── docker-compose.yml   # Complete stack orchestration
```

## 🎯 Access Points

**All services are accessible via Traefik reverse proxy on port 8081**

| Service             | URL                                | Description                      |
| ------------------- | ---------------------------------- | -------------------------------- |
| **Reverse Proxy**   |                                    |                                  |
| Traefik Dashboard   | http://localhost:8082              | Traefik management dashboard     |
| **Observability**   |                                    |                                  |
| Grafana             | http://localhost:8081/grafana/     | Main observability dashboard     |
| **Agentic Network** |                                    |                                  |
| Agents Web UI       | http://localhost:8081/agents/ui/   | AI-powered observability queries |
| Orchestrator API    | http://localhost:8081/agents/orchestrator/ | Main agent coordinator |
| Logs Agent          | http://localhost:8081/agents/logs/ | Loki log analysis                |
| Metrics Agent       | http://localhost:8081/agents/metrics/ | Mimir metrics analysis        |
| Traces Agent        | http://localhost:8081/agents/traces/ | Tempo traces analysis          |
| Translation Agent   | http://localhost:8081/agents/traduction/ | Language detection & translation |
| **Applications**    |                                    |                                  |
| Order Service       | http://localhost:8081/apps/order/  | Order management API             |
| Stock Service       | http://localhost:8081/apps/stock/  | Stock management API             |
| **Tools**           |                                    |                                  |
| AKHQ (Kafka UI)     | http://localhost:8081/akhq/        | Kafka management                 |
| Adminer (Database)  | http://localhost:8081/adminer/     | PostgreSQL administration        |

**Default Grafana credentials**: `admin` / `admin`

> **Note**: All services communicate internally via Docker network. Only Traefik exposes services externally.

## 🤖 Using the AI Agents

### Quick Example

Open http://localhost:8081/agents/ui/ and ask questions in natural language:

- "Show me errors in the order service"
- "What's the CPU usage of customer service?"
- "Analyze slow traces in the last hour"
- "Why is the order service failing?"

### Setup MCP Authentication

For agents to work, create a Grafana service account:

```bash
# 1. Open Grafana: http://localhost:8081/grafana/
# 2. Go to Configuration → Service accounts → Create service account
# 3. Generate token and copy it
# 4. Add to environment:
echo 'GRAFANA_SERVICE_ACCOUNT_TOKEN=eyJ...your-token...' >> .env

# 5. Restart MCP service
docker-compose restart grafana-mcp
```

See [Configuration Guide](docs/handbook/configuration.md) for detailed setup.

## 🔧 Common Commands

```bash
# Start the full stack (preferred)
task compose-up

# Stop all services
task compose-down

# Rebuild a single service (example)
podman compose up -d --build --no-deps agent-logs || \
  docker compose up -d --build --no-deps agent-logs

# View logs for specific service
podman-compose logs -f order || docker-compose logs -f order

# Restart a service (no task target — use compose directly)
podman compose up -d --force-recreate --no-deps agent-logs || \
  docker compose up -d --force-recreate --no-deps agent-logs

# Complete cleanup (removes all data)
task compose-down
podman-compose down -v || docker-compose down -v
```

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


## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](docs/contributing.md) for:

- Code style and conventions
- Commit message format (Conventional Commits)
- Pull request process
- Adding new services or agents

---