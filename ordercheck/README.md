# Ordercheck Service

> **Status:** `KEEPER` — Stable service. Expected to stay functional and tested.

Kafka consumer that processes customer orders from the `orders` topic.

## 📋 Overview

- **Type**: Kafka Consumer
- **Topic**: `orders`
- **Consumer Group**: `order-check-group`
- **Error Simulation**: Configurable error rate (default: 10%)
- **Dependencies**: Kafka broker, Order Service API, common-models

## 🚀 Running the Service

### With Docker

```bash
docker-compose up ordercheck
```

### Local Development

```bash
# Navigate to service directory
cd ordercheck/

# Install dependencies
uv sync

# Run the consumer
uv run python -m ordercheck.ordercheck_consumer
```

## 🔧 Configuration

Environment variables:

```bash
# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS=broker:29092

# Order Service API
API_URL=http://order:5000

# Service behavior
ERROR_RATE=0.1               # Percentage of orders that will fail validation (0.0 to 1.0)
LOG_LEVEL=INFO               # Logging level (DEBUG, INFO, WARNING, ERROR)

# OpenTelemetry
OTEL_SERVICE_NAME=ordercheck
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

## 📊 Order Processing Flow

1. **Consume**: Reads orders from Kafka `orders` topic
2. **Validate**: Checks order data structure and content
3. **Simulate Errors**: Randomly fails based on `ERROR_RATE`
4. **Forward**: Sends valid orders to Order Service API
5. **Log**: Records processing results for observability

## 🎯 Error Simulation

The service simulates validation errors based on `ERROR_RATE`:

- Randomly rejects orders during validation
- Logs detailed error information
- Helps test error handling and retry logic

## 📦 Dependencies

- `confluent-kafka`: Kafka Python client
- `requests`: HTTP client for API calls
- `common-models`: Shared business models (Order, WoodType)

## 🔄 Integration

The ordercheck service integrates with:

- **Kafka**: Consumes orders from `orders` topic
- **Order Service**: Forwards valid orders to API
- **Customer Service**: Receives orders from customer producer
- **OpenTelemetry**: Auto-instrumented for observability

## 🧪 Testing

```bash
# Run tests
uv run pytest

# Check test coverage
uv run pytest --cov=ordercheck --cov-report=html
```

## 📝 Example Usage

```bash
# Start with custom error rate
KAFKA_BOOTSTRAP_SERVERS=localhost:9092 API_URL=http://localhost:5000 ERROR_RATE=0.05 uv run python -m ordercheck.ordercheck_consumer
```

## 🏗️ Dockerfile

The service uses a multi-stage Docker build:

1. Build stage: Installs dependencies with UV
2. Runtime stage: Runs the consumer

See `ordercheck/Dockerfile` for details.

## 📈 Observability

- **Logs**: Sent to Loki via OpenTelemetry
- **Metrics**: Sent to Mimir via OpenTelemetry
- **Traces**: Sent to Tempo via OpenTelemetry
- **Service Name**: `ordercheck`

## 🔗 Related Services

- **customer**: Sends orders to Kafka
- **order**: Receives validated orders via API
- **ordermanagement**: Updates order statuses after processing
- **stock**: Validates stock availability for orders

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
