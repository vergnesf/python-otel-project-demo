# Python OpenTelemetry Demo 🐍

> A comprehensive microservices platform showcasing Python auto-instrumentation with OpenTelemetry and AI-powered observability analysis

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-enabled-blueviolet)](https://opentelemetry.io/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)](https://www.docker.com/)

## Features

✨ **Complete Observability Stack** - Grafana, Loki, Mimir, Tempo with OpenTelemetry auto-instrumentation
🤖 **AI-Powered Analysis** - Intelligent agents for natural language observability queries
🏗️ **Production-Ready** - Docker-first, Python 3.14, UV package manager, FastAPI
🎭 **Error Simulation** - Built-in configurable error injection for testing

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd python-otel-project-demo

# Copy environment template
cp .env.example .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

That's it! The complete stack is now running.

## Utiliser Ollama avec Podman et GPU NVIDIA

Lorsque vous lancez la stack avec Podman (ou Docker) et que vous souhaitez que `ollama` utilise la GPU, il faut s'assurer que le conteneur voit bien les périphériques et les bibliothèques NVIDIA. Dans ce dépôt, `docker-compose.yml` a été mis à jour pour exposer les devices et variables nécessaires (voir la section `ollama` dans `docker-compose.yml`).

- Ce que nous ajoutons dans `docker-compose.yml` :
    - Variables d'environnement : `NVIDIA_VISIBLE_DEVICES`, `NVIDIA_DRIVER_CAPABILITIES`, `LD_LIBRARY_PATH`.
    - Mappings de devices : `/dev/nvidia*` montés dans le conteneur.
    - Bind-mounts des bibliothèques drivers hôtes (ex. `/usr/lib/nvidia` → `/usr/local/nvidia/lib`).
    - Note SELinux : les mounts de volumes utilisent `:Z` là où c'est nécessaire.

- Vérifications rapides après `podman compose up -d` :

```bash
podman compose down
podman compose up -d
podman logs --tail 200 ollama
podman exec -it ollama ls -l /dev/nvidia* || true
podman exec -it ollama ls -l /usr/local/nvidia || true
podman exec -it ollama nvidia-smi || true
```

- Si le conteneur n'affiche toujours pas de VRAM (ex. `total vram = 0 B`), installez l'outil d'intégration NVIDIA pour conteneurs afin que Podman injecte correctement devices et bibliothèques :

```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-container-toolkit/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-container-toolkit/$distribution/nvidia-container-toolkit.list | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart podman
```

Après installation, redémarrez la stack (`podman compose down && podman compose up -d`) et vérifiez à nouveau les logs et `nvidia-smi` à l'intérieur du conteneur.

Si vous préférez ne pas installer l'outil NVIDIA, la méthode alternative est de continuer à monter explicitement `/dev/nvidia*` et les bibliothèques host dans le conteneur (comme fait ici), mais l'intégration via `nvidia-container-toolkit` est plus robuste et évite les manipulations manuelles sur chaque machine.

Note SELinux (Podman on SELinux-enabled hosts)

Sur des hôtes SELinux (par ex. distributions atomiques), Podman peut bloquer l'accès aux devices même si le runtime et les devices sont correctement configurés. Si vous rencontrez des erreurs d'accès aux périphériques, activez la boolean SELinux recommandée pour permettre aux conteneurs d'utiliser les devices :

```bash
sudo setsebool -P container_use_devices true
```

Cette commande autorise les conteneurs à utiliser des périphériques (/dev/*). Après l'avoir exécutée, redémarrez la stack et vérifiez `nvidia-smi` dans le conteneur.


## Access Points

| Service             | URL                   | Description                      |
| ------------------- | --------------------- | -------------------------------- |
| **Observability**   |                       |                                  |
| Grafana             | http://localhost:3000 | Main observability dashboard     |
| **Agentic Network** |                       |                                  |
| Agents Web UI       | http://localhost:3002 | AI-powered observability queries |
| Orchestrator API    | http://localhost:8001 | Main agent coordinator           |
| Logs Agent          | http://localhost:8002 | Loki log analysis                |
| Metrics Agent       | http://localhost:8003 | Mimir metrics analysis           |
| Traces Agent        | http://localhost:8004 | Tempo traces analysis            |
| **Tools**           |                       |                                  |
| AKHQ (Kafka UI)     | http://localhost:8080 | Kafka management                 |
| Adminer (Database)  | http://localhost:8081 | PostgreSQL administration        |

**Default Grafana credentials**: `admin` / `admin`

## Using the AI Agents

### Quick Example

Open http://localhost:3002 and ask questions in natural language:

- "Show me errors in the order service"
- "What's the CPU usage of customer service?"
- "Analyze slow traces in the last hour"
- "Why is the order service failing?"

### Setup MCP Authentication

For agents to work, create a Grafana service account:

```bash
# 1. Open Grafana: http://localhost:3000
# 2. Go to Configuration → Service accounts → Create service account
# 3. Generate token and copy it
# 4. Add to .env:
echo 'GRAFANA_SERVICE_ACCOUNT_TOKEN=eyJ...your-token...' >> .env

# 5. Restart MCP service
docker-compose restart grafana-mcp
```

See [Configuration Guide](docs/configuration.md) for detailed setup.

## Common Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Rebuild and start
docker-compose up --build -d

# View logs for specific service
docker-compose logs -f order

# Restart a service
docker-compose restart agent-logs

# Complete cleanup (removes all data)
docker-compose down -v
```

## Documentation

📚 **Detailed documentation available in the [`docs/`](docs/) directory:**

- **[Architecture](docs/architecture.md)** - System architecture, components, and data flow
- **[Agents](docs/agents.md)** - AI agentic network architecture and usage
- **[Development](docs/development.md)** - Local development guide and best practices
- **[Configuration](docs/configuration.md)** - Environment variables and customization
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions
- **[Docker Security](docs/DOCKER_SECURITY.md)** - Security best practices and non-root execution
- **[Contributing](docs/contributing.md)** - Contribution guidelines and code style

## Architecture Overview

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

## Technology Stack

- **Python 3.14** - Latest stable Python
- **UV** - Fast Python package manager
- **FastAPI** - Modern web framework
- **OpenTelemetry** - Observability instrumentation
- **Grafana Stack** - Loki (logs), Mimir (metrics), Tempo (traces)
- **LangChain** - LLM framework for AI agents
- **Kafka** - Message streaming
- **PostgreSQL** - Relational database

## Project Structure

```
├── common-models/       # Shared business models (WoodType, Order, Stock)
├── common-ai/           # Shared AI utilities (MCP client, LLM config, agent models)
├── customer/            # Microservice: Customer orders (Kafka producer)
├── order/               # Microservice: Order management API
├── stock/               # Microservice: Stock management API
├── supplier/            # Microservice: Supplier (Kafka producer)
├── ordercheck/          # Microservice: Order processing (Kafka consumer)
├── suppliercheck/       # Microservice: Stock updates (Kafka consumer)
├── ordermanagement/     # Microservice: Order status updates
├── agent-orchestrator/  # AI Agent: Main coordinator
├── agent-logs/          # AI Agent: Loki log analysis
├── agent-metrics/       # AI Agent: Mimir metrics analysis
├── agent-traces/        # AI Agent: Tempo traces analysis
├── agent-ui/           # Web UI for agents
├── config/              # Configuration files (Grafana, Loki, Mimir, Tempo)
├── docs/                # Documentation
└── docker-compose.yml   # Complete stack orchestration
```

## Local Development

For local development without Docker:

```bash
# Navigate to a service
cd order/

# Install dependencies with UV
uv sync

# Run with OpenTelemetry instrumentation
uv run opentelemetry-instrument \
    --traces_exporter otlp \
    --metrics_exporter otlp \
    --service_name order \
    --exporter_otlp_endpoint http://localhost:4318 \
    python -m order.main
```

See [Development Guide](docs/development.md) for detailed instructions.

## Contributing

Contributions are welcome! Please read our [Contributing Guide](docs/contributing.md) for:

- Code style and conventions
- Commit message format (Conventional Commits)
- Pull request process
- Adding new services or agents

---

Built with ❤️ using Python 3.14, OpenTelemetry, and Grafana Stack
