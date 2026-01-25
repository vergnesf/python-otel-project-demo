# Configuration Guide

> NOTE: A condensed configuration handbook is available at `docs/handbook/configuration.md`.
> Use the handbook for quick setup steps. This file keeps the full reference.

## Environment Variables

All image versions and registry configuration are managed through environment variables. The project includes:

- **`.env.example`** - Template with all available configuration options and documentation
- **`.env`** - Your local configuration (not tracked in git)

### Core Configuration

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
IMG_OTEL=otel/opentelemetry-collector-contrib:0.130.1  # OTEL collector

# Performance Optimizations
COMPOSE_PARALLEL_LIMIT=8                 # Parallel container builds
DOCKER_BUILDKIT=1                        # Enable BuildKit
```

### Agentic Network Configuration

```bash
# LLM Configuration
## Default local endpoint uses Ollama (`http://localhost:11434/api`).
LLM_BASE_URL=http://localhost:11434/api  # Local LLM endpoint (Ollama)
LLM_API_KEY=not-needed                   # API key (not required for local LLM)
LLM_MODEL=ai/qwen3:0.6B-Q4_0             # Model name (project metadata may require mapping)

# MCP Server Authentication
GRAFANA_SERVICE_ACCOUNT_TOKEN=<token>    # Required for MCP agents (see setup below)
```

### Business Application Configuration

```bash
# Error Simulation
ERROR_RATE=0.1                           # 10% error rate for testing observability

# Service-specific settings
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-gateway:4318  # OpenTelemetry endpoint
```

## Configuration Structure

The project uses a modular configuration structure:

```
config/
├── grafana/
│   └── datasources/
│       └── default.yaml          # Grafana datasources (Loki, Mimir, Tempo)
├── loki/
│   └── loki-config.yml          # Loki configuration
├── mimir/
│   └── mimir-config.yml         # Mimir configuration
├── otel/
│   └── otel-conf.yml            # OpenTelemetry Collector configuration
└── tempo/
    └── tempo.yml                # Tempo configuration
```

## Setting Up Grafana Service Account

For MCP agents to work, you need to create a Grafana service account:

### Step 1: Access Grafana

1. Start the stack: `docker-compose up -d`
2. Open http://localhost:3000
3. Login with default credentials: `admin` / `admin`

### Step 2: Create Service Account

1. Navigate to **Configuration** → **Service accounts**
2. Click **Add service account**
3. Fill in details:
   - **Display name**: MCP Agent Access
   - **Role**: Editor (or Viewer if read-only access is sufficient)
4. Click **Create**

### Step 3: Generate Token

1. In the service account page, click **Add service account token**
2. Set an expiration date (or leave blank for no expiration)
3. Click **Generate token**
4. **Copy the token** (you won't be able to see it again!)

### Step 4: Configure Environment

1. Open or create `.env` file:
   ```bash
   cp .env.example .env
   ```

2. Add the token:
   ```bash
   GRAFANA_SERVICE_ACCOUNT_TOKEN=eyJ...your-copied-token...
   ```

3. Restart the MCP service:
   ```bash
   docker-compose restart grafana-mcp
   ```

### Step 5: Verify

Check that the MCP server can connect:

```bash
# Check MCP server logs
docker-compose logs grafana-mcp

# Test agent health
curl http://localhost:8002/health  # Logs agent
curl http://localhost:8003/health  # Metrics agent
curl http://localhost:8004/health  # Traces agent
```

## Customizing Datasources

Edit `config/grafana/datasources/default.yaml` to modify Grafana datasource configuration:

```yaml
apiVersion: 1

datasources:
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    isDefault: false
    editable: true

  - name: Mimir
    type: prometheus
    access: proxy
    url: http://mimir:9009/prometheus
    isDefault: true
    editable: true

  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    isDefault: false
    editable: true
```

## Customizing OpenTelemetry

Edit `config/otel/otel-conf.yml` to modify how telemetry data is collected and exported:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:

exporters:
  loki:
    endpoint: http://loki:3100/loki/api/v1/push
  otlp/tempo:
    endpoint: tempo:4317
    tls:
      insecure: true
  prometheusremotewrite:
    endpoint: http://mimir:9009/api/v1/push

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/tempo]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheusremotewrite]
    logs:
      receivers: [otlp]
      processors: [batch]
      exporters: [loki]
```

## Docker Compose Override

For local customizations without modifying `docker-compose.yml`, create a `docker-compose.override.yml`:

```yaml
version: '3.8'

services:
  order:
    environment:
      - ERROR_RATE=0.5  # Override error rate for testing
      - LOG_LEVEL=debug

  agent-orchestrator:
    environment:
      - LLM_MODEL=ai/llama-3.2:1B  # Use a different model
```

This file is automatically merged with `docker-compose.yml` and is git-ignored by default.
