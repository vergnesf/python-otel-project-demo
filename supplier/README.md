# Supplier Service

Kafka producer that simulates supplier stock updates being sent to the system.

## 📋 Overview

- **Type**: Kafka Producer
- **Topic**: `stocks`
- **Frequency**: Configurable interval (default: 60 seconds)
- **Error Simulation**: Configurable error rate (default: 10%)
- **Dependencies**: Kafka broker, common-models

## 🚀 Running the Service

### With Docker

```bash
docker-compose up supplier
```

### Local Development

```bash
# Navigate to service directory
cd supplier/

# Install dependencies
uv sync

# Run the producer
uv run python -m supplier.supplier_producer
```

## 🔧 Configuration

Environment variables:

```bash
# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS=broker:29092

# Service behavior
INTERVAL_SECONDS=60          # How often to send stock updates (seconds)
ERROR_RATE=0.1               # Percentage of updates that will fail (0.0 to 1.0)
LOG_LEVEL=INFO               # Logging level (DEBUG, INFO, WARNING, ERROR)

# OpenTelemetry
OTEL_SERVICE_NAME=supplier
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

## 📊 Features

The service generates random stock updates with:

- Random wood types (oak, maple, birch, elm, pine)
- Random quantities (1-100 units)
- Timestamps

## 🎯 Error Simulation

The service simulates errors based on `ERROR_RATE`:

- Randomly fails to send stock updates
- Logs error details for observability
- Helps test error handling in downstream services

## 📦 Dependencies

- `confluent-kafka`: Kafka Python client
- `common-models`: Shared business models (Stock, WoodType)

## 🔄 Integration

The supplier service integrates with:

- **Kafka**: Sends stock updates to `stocks` topic
- **Stock Service**: Updates are processed by suppliercheck → stock
- **OpenTelemetry**: Auto-instrumented for observability

## 🧪 Testing

```bash
# Run tests
uv run pytest

# Check test coverage
uv run pytest --cov=supplier --cov-report=html
```

## 📝 Example Usage

```bash
# Start with custom interval and error rate
KAFKA_BOOTSTRAP_SERVERS=localhost:9092 INTERVAL_SECONDS=30 ERROR_RATE=0.05 uv run python -m supplier.supplier_producer
```

## 🏗️ Dockerfile

The service uses a multi-stage Docker build:

1. Build stage: Installs dependencies with UV
2. Runtime stage: Runs the producer

See `supplier/Dockerfile` for details.

## 📈 Observability

- **Logs**: Sent to Loki via OpenTelemetry
- **Metrics**: Sent to Mimir via OpenTelemetry
- **Traces**: Sent to Tempo via OpenTelemetry
- **Service Name**: `supplier`

## 🔗 Related Services

- **suppliercheck**: Consumes stock updates from Kafka
- **stock**: Processes validated stock updates
- **order**: Uses stock information for order processing
- **customer**: Places orders that consume stock

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