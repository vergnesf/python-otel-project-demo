# Order Service

FastAPI-based REST API that manages customer orders.

## 📋 Overview

- **Type**: REST API (Flask)
- **Port**: 5000
- **Database**: PostgreSQL
- **Dependencies**: common-models, Flask, SQLAlchemy
- **OpenTelemetry**: Auto-instrumented for observability

## 🚀 Running the Service

### With Docker

```bash
docker-compose up order
```

### Local Development

```bash
# Navigate to service directory
cd order/

# Install dependencies
uv sync

# Run with OpenTelemetry instrumentation
uv run opentelemetry-instrument \
    --traces_exporter otlp \
    --metrics_exporter otlp \
    --service_name order \
    --exporter_otlp_endpoint http://localhost:4317 \
    python -m order.main
```

## 🔧 Configuration

Environment variables:

```bash
# Database configuration
DATABASE_URL=postgresql://postgres:yourpassword@postgres:5432/mydatabase

# Service configuration
HOST=0.0.0.0
PORT=5000
LOG_LEVEL=INFO

# OpenTelemetry
OTEL_SERVICE_NAME=order
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

## 📊 API Endpoints

### POST /orders
Create a new order

**Request:**
```json
{
  "customer_id": "cust_123",
  "wood_type": "oak",
  "quantity": 5,
  "status": "registered"
}
```

**Response:**
```json
{
  "id": 1,
  "customer_id": "cust_123",
  "wood_type": "oak",
  "quantity": 5,
  "status": "registered",
  "created_at": "2025-11-08T10:30:00Z"
}
```

### GET /orders
List all orders

**Response:**
```json
[
  {
    "id": 1,
    "customer_id": "cust_123",
    "wood_type": "oak",
    "quantity": 5,
    "status": "registered"
  }
]
```

### GET /orders/{order_id}
Get specific order

### PUT /orders/{order_id}
Update order status

### GET /orders/status/registered
Get orders with specific status

## 📦 Dependencies

- `flask`: Web framework
- `flasgger`: API documentation
- `sqlalchemy`: ORM for database
- `psycopg2-binary`: PostgreSQL adapter
- `common-models`: Shared business models

## 🔄 Integration

The order service integrates with:

- **Database**: PostgreSQL for order persistence
- **Ordercheck**: Consumes orders from Kafka and calls this API
- **Ordermanagement**: Updates order statuses
- **Stock**: Validates stock availability
- **OpenTelemetry**: Auto-instrumented for observability

## 🧪 Testing

```bash
# Run tests
uv run pytest

# Check test coverage
uv run pytest --cov=order --cov-report=html
```

## 📝 Example Usage

```bash
# Create an order
curl -X POST http://localhost:5000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "cust_123", "wood_type": "oak", "quantity": 5, "status": "registered"}'

# List all orders
curl http://localhost:5000/orders
```

## 🏗️ Dockerfile

The service uses a multi-stage Docker build:

1. Build stage: Installs dependencies with UV
2. Runtime stage: Runs the FastAPI server

See `order/Dockerfile` for details.

## 📈 Observability

- **Logs**: Sent to Loki via OpenTelemetry
- **Metrics**: Sent to Mimir via OpenTelemetry
- **Traces**: Sent to Tempo via OpenTelemetry
- **Service Name**: `order`

## 🔗 Related Services

- **customer**: Sends orders via Kafka
- **ordercheck**: Validates and processes orders
- **ordermanagement**: Updates order statuses
- **stock**: Manages inventory for orders