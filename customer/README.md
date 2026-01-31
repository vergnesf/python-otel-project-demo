# Customer Service

The **Customer Service** is a Kafka producer that simulates customer orders being placed in the system. It generates random orders and sends them to the Kafka `orders` topic for processing.

## 📋 Overview

- **Type**: Kafka Producer
- **Topic**: `orders`
- **Frequency**: Configurable interval (default: 60 seconds)
- **Error Simulation**: Configurable error rate (default: 10%)
- **Dependencies**: Kafka broker, common-models

## 🚀 Running the Service

### With Docker

```bash
docker-compose up customer
```

### Local Development

```bash
# Navigate to service directory
cd customer/

# Install dependencies
uv sync

# Run the producer
uv run python -m customer.customer_producer
```

## 🔧 Configuration

Environment variables:

```bash
# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS=broker:29092

# Service behavior
INTERVAL_SECONDS=60          # How often to send orders (seconds)
ERROR_RATE=0.1               # Percentage of orders that will fail (0.0 to 1.0)
LOG_LEVEL=INFO               # Logging level (DEBUG, INFO, WARNING, ERROR)

# OpenTelemetry
OTEL_SERVICE_NAME=customer
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

## 📊 Order Generation

The service generates random orders with:

- Random wood types (oak, maple, birch, elm, pine)
- Random quantities (1-10 units)
- Random customer IDs
- Timestamps

## 🎯 Error Simulation

The service simulates errors based on `ERROR_RATE`:

- Randomly fails to send orders
- Logs error details for observability
- Helps test error handling in downstream services

## 📦 Dependencies

- `confluent-kafka`: Kafka Python client
- `common-models`: Shared business models (Order, WoodType)

## 🔄 Integration

The customer service integrates with:

- **Kafka**: Sends orders to `orders` topic
- **Order Service**: Orders are processed by ordercheck → order
- **OpenTelemetry**: Auto-instrumented for observability

## 🧪 Testing

```bash
# Run tests
uv run pytest

# Check test coverage
uv run pytest --cov=customer --cov-report=html
```

## 📝 Example Usage

```bash
# Start with custom interval and error rate
KAFKA_BOOTSTRAP_SERVERS=localhost:9092 INTERVAL_SECONDS=30 ERROR_RATE=0.05 uv run python -m customer.customer_producer
```

## 🏗️ Dockerfile

The service uses a multi-stage Docker build:

1. Build stage: Installs dependencies with UV
2. Runtime stage: Runs the producer

See `customer/Dockerfile` for details.

## 📈 Observability

- **Logs**: Sent to Loki via OpenTelemetry
- **Metrics**: Sent to Mimir via OpenTelemetry
- **Traces**: Sent to Tempo via OpenTelemetry
- **Service Name**: `customer`

## 🔗 Related Services

- **ordercheck**: Consumes orders from Kafka
- **order**: Processes validated orders
- **stock**: Manages inventory
- **supplier**: Provides stock updates