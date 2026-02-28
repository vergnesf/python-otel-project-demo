# Suppliercheck Service

> **Status:** `KEEPER` — Stable service. Expected to stay functional and tested.

Kafka consumer that processes supplier stock updates from the `stocks` topic.

## 📋 Overview

- **Type**: Kafka Consumer
- **Topic**: `stocks`
- **Consumer Group**: `stock-check-group`
- **Error Simulation**: Configurable error rate (default: 10%)
- **Dependencies**: Kafka broker, Stock Service API, common-models

## 🚀 Running the Service

### With Docker

```bash
docker-compose up suppliercheck
```

### Local Development

```bash
# Navigate to service directory
cd suppliercheck/

# Install dependencies
uv sync

# Run the consumer
uv run python -m suppliercheck.suppliercheck_consumer
```

## 🔧 Configuration

Environment variables:

```bash
# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS=broker:29092

# Stock Service API
API_URL=http://stock:5001

# Service behavior
ERROR_RATE=0.1               # Percentage of updates that will fail validation (0.0 to 1.0)
LOG_LEVEL=INFO               # Logging level (DEBUG, INFO, WARNING, ERROR)

# OpenTelemetry
OTEL_SERVICE_NAME=suppliercheck
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

## 📊 Stock Processing Flow

1. **Consume**: Reads stock updates from Kafka `stocks` topic
2. **Validate**: Checks stock data structure and content
3. **Simulate Errors**: Randomly fails based on `ERROR_RATE`
4. **Forward**: Sends valid updates to Stock Service API
5. **Log**: Records processing results for observability

## 🎯 Error Simulation

The service simulates validation errors based on `ERROR_RATE`:

- Randomly rejects stock updates during validation
- Logs detailed error information
- Helps test error handling and retry logic

## 📦 Dependencies

- `confluent-kafka`: Kafka Python client
- `requests`: HTTP client for API calls
- `common-models`: Shared business models (Stock, WoodType)

## 🔄 Integration

The suppliercheck service integrates with:

- **Kafka**: Consumes stock updates from `stocks` topic
- **Stock Service**: Forwards valid updates to API
- **Supplier Service**: Receives updates from supplier producer
- **OpenTelemetry**: Auto-instrumented for observability

## 🧪 Testing

```bash
# Run tests
uv run pytest

# Check test coverage
uv run pytest --cov=suppliercheck --cov-report=html
```

## 📝 Example Usage

```bash
# Start with custom error rate
KAFKA_BOOTSTRAP_SERVERS=localhost:9092 API_URL=http://localhost:5001 ERROR_RATE=0.05 uv run python -m suppliercheck.suppliercheck_consumer
```

## 🏗️ Dockerfile

The service uses a multi-stage Docker build:

1. Build stage: Installs dependencies with UV
2. Runtime stage: Runs the consumer

See `suppliercheck/Dockerfile` for details.

## 📈 Observability

- **Logs**: Sent to Loki via OpenTelemetry
- **Metrics**: Sent to Mimir via OpenTelemetry
- **Traces**: Sent to Tempo via OpenTelemetry
- **Service Name**: `suppliercheck`

## 🔗 Related Services

- **supplier**: Sends stock updates to Kafka
- **stock**: Receives validated updates via API
- **order**: Uses stock information for order processing
- **ordermanagement**: Decreases stock when orders are processed

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