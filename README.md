# Python Otel 🐍

## What is this project? 😲

This project is a set of microservices developed by a non-python-developer that allows you to view and understand Python auto-instrumentation with OpenTelemetry.

## How does it work? 🤔

The application is structured as follows:

- **customer**: Kafka producer that acts as the client for ordering wood 🪵
- **supplier**: Kafka producer that acts as the supplier to replenish the wood stock 🪵
- **customercheck**: Kafka consumer that serves as the order reception service 📦
- **suppliercheck**: Kafka consumer that manages stock levels 📊
- **stock**: API for managing stock 🏗️
- **order**: API for managing orders 📝
- **ordermanagement**: A service that updates the order status 😄

The entire application is containerized, and the `docker-compose.yml` file will build all the microservices and deploy the following additional components:

- **Kafka**: A cluster to receive orders and stock updates 📨
- **PostgreSQL**: PostgreSQL database 🗄️
- **Adminer**: Web tool for viewing your database 📂
- **Grafana**: Standard visualization tool 📊
- **Grafana with MCP support**: Enhanced Grafana with Model Context Protocol for AI integration 🤖
- **Loki**: Log database 📝
- **Mimir**: Metrics database 📈
- **Tempo**: Traces database 📍
- **Otel Gateway**: API for receiving observability data 🛠️
- **n8n**: Workflow automation tool 🔄

## Key Features ✨

- **Simulated Error Scenarios**: Built-in error simulation with configurable error rates via `ERROR_RATE` environment variable
- **Comprehensive Observability**: Full OpenTelemetry auto-instrumentation with traces, metrics, and logs
- **Docker-First Architecture**: Complete containerization with optimized build settings
- **Flexible Configuration**: Environment-based configuration for easy deployment across different environments
- **AI Integration Ready**: Includes Grafana with MCP (Model Context Protocol) support for AI-powered observability

## Configuration ⚙️

### Environment Variables
All image versions and registry configuration are managed through environment variables. The project includes:

- `.env.example`: Template with all available configuration options and documentation
- `.env`: Your local configuration (not tracked in git)

Key configuration options include:

```bash
# Docker Registry Configuration
DOCKER_REGISTRY=                    # Leave empty for Docker Hub

# Core Services
IMG_GRAFANA=grafana/grafana:12.0.2      # Standard Grafana
IMG_GRAFANA_MCP=mcp/grafana:latest       # Grafana with MCP support
IMG_LOKI=grafana/loki:3.5.2              # Log aggregation
IMG_TEMPO=grafana/tempo:2.8.1            # Distributed tracing
IMG_MIMIR=grafana/mimir:2.16.1           # Metrics storage

# Additional Tools
IMG_N8N=n8nio/n8n:1.112.0               # Workflow automation
IMG_OTEL=otel/opentelemetry-collector-contrib:0.130.1  # OTEL collector

# Performance Optimizations
COMPOSE_PARALLEL_LIMIT=8                 # Parallel container builds
DOCKER_BUILDKIT=1                        # Enable BuildKit
```

Setup configuration:
```sh
cp .env.example .env
# Edit .env with your specific settings
```

### Error Simulation 🎭
The application includes built-in error simulation for testing observability:

- **Customer Service**: Simulates Kafka/network failures when sending orders
- **Supplier Check Service**: Simulates API/network failures when processing stock updates
- **Configurable Error Rate**: Set `ERROR_RATE` environment variable (default: 0.1 = 10% error rate)

Example configuration:
```bash
# In docker-compose.yml or your environment
ERROR_RATE=0.2  # 20% error rate for testing
```

### Configuration Structure 📁
The project has been reorganized with a cleaner configuration structure:

```
config/
├── grafana/
│   └── datasources/
│       └── default.yaml          # Grafana datasource configuration
├── loki/
│   └── loki-config.yml          # Loki configuration
│   └── mimir-config.yml         # Mimir configuration  
│   └── otel-conf.yml            # OpenTelemetry collector configuration
└── tempo/
    └── tempo.yml                # Tempo configuration
```

## Running the Application 🚀
### With Docker Compose
```sh
# Start all services
docker-compose up -d

# Build and start
docker-compose up --build -d

# Stop all services
docker-compose down

# Clean up (remove volumes and images)
docker-compose down -v --rmi all
```

### Useful URLs 🌐

- [Grafana (Standard)](http://localhost:3000/) 📊 - Main observability dashboard
- [AKHQ](http://localhost:8080/) 🛠️ - Kafka management UI
- [Adminer](http://localhost:8081/) 🗃️ - Database administration
- [n8n](http://localhost:5678/) 🔄 - Workflow automation

## GPU Support with NVIDIA Container Toolkit 🚀

For AI/LLM features (like the n8n AI models), you need GPU support in Docker. This requires the NVIDIA Container Toolkit.

### Prerequisites 📋

First, check if your GPU is detected:
```bash
nvidia-smi
```

You should see your GPU information. If this command fails, install NVIDIA drivers first.

### Install NVIDIA Container Toolkit

#### For Fedora/RHEL/CentOS:
```bash
# Configure the production repository
curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | \
  sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo

# Install the toolkit
sudo dnf install -y nvidia-container-toolkit
```

### Configure Docker

After installation, configure Docker to use the NVIDIA runtime:

```bash
# Configure the container runtime
sudo nvidia-ctk runtime configure --runtime=docker

# Restart Docker daemon
sudo systemctl restart docker
```

### Test GPU Support

Test that Docker can access your GPU:
```bash
# Test with a simple CUDA container
docker run --rm --gpus all nvidia/cuda:11.0.3-base-ubuntu20.04 nvidia-smi
```

If successful, you should see your GPU information displayed within the container.

### Common Issues 🔧


For more details, see the [official NVIDIA Container Toolkit documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

## Docker AI Model Runner 🤖

Docker Model Runner (DMR) lets you run and manage AI models locally using Docker. This is particularly useful for the AI/LLM features in this project.

### Installation 📦

#### For Docker Engine (Fedora/RPM):
```bash
# Install Docker Model Runner plugin
sudo dnf install docker-model-plugin

# Test the installation
docker model version
```

### Update DMR 🔄

To update Docker Model Runner in Docker Engine:

```bash
# Uninstall current version and reinstall (preserves local models)
docker model uninstall-runner --images && docker model install-runner
```

### Integration with n8n 🔗

To configure AI features in n8n using Docker Model Runner:

1. In n8n, create an **OpenAI** credential type
2. Use a dummy token (e.g., `dummy-token`)
3. Set the base URL to: `http://172.17.0.1:12434/engines/llama.cpp/v1`

This allows n8n to connect to your local Docker Model Runner instance for AI/LLM capabilities.

### MCP (Model Context Protocol) in n8n 🛰️

If you want to enable Grafana MCP integration inside n8n (for context enrichment / model context), configure a separate credential or webhook using the Server Sent Events transport with the following URL:

- Transport: Server Sent Events (SSE)
- URL: `http://grafana-mcp:8000/sse`

Example notes:

- Use the SSE transport when configuring the MCP server/transport in n8n so Grafana MCP can stream context updates.
- The hostname `grafana-mcp` matches the internal Docker Compose service name used in this project; when running n8n inside the same Compose network, this resolves to the MCP service.

#### Pre-step: create Grafana service account 🔐

Before using the MCP server from n8n, create a Grafana service account and copy its token into your `.env` file:

- In Grafana, go to Configuration → Service accounts → Create service account
- Create a token for the account and copy the token value
- Add the token to your `.env` as:

```bash
GRAFANA_SERVICE_ACCOUNT_TOKEN=eyJ...your-token...
```

After setting the token, restart the MCP service so Grafana picks up the new credentials:

```bash
docker compose restart grafana-mcp
```


## Running Locally 🐛

Each microservice is set up with **uv**, so you can launch the different services using `uv run`.

Locally, you'll need to modify `PYTHONPATH` to include the project and access the "common" part, which simplifies things for me.

To run a microservice with auto-instrumentation:

```sh
uv run opentelemetry-instrument \
    --traces_exporter otlp \
    --metrics_exporter otlp \
    --service_name customer2 \
    --exporter_otlp_endpoint http://localhost:4318 \
    --log_level debug \
    python -m order.main
```
