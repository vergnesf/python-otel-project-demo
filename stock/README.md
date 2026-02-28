# Stock Service

> **Status:** `KEEPER` — Stable service. Expected to stay functional and tested.

Flask-based REST API that manages wood stock inventory.

## 📋 Overview

- **Type**: REST API (Flask)
- **Port**: 5001
- **Database**: PostgreSQL
- **Dependencies**: common-models, Flask, SQLAlchemy
- **OpenTelemetry**: Auto-instrumented for observability

## 🚀 Running the Service

### With Docker

```bash
docker-compose up stock
```

### Local Development

```bash
# Navigate to service directory
cd stock/

# Install dependencies
uv sync

# Run with OpenTelemetry instrumentation
uv run opentelemetry-instrument \
    --traces_exporter otlp \
    --metrics_exporter otlp \
    --service_name stock \
    --exporter_otlp_endpoint http://localhost:4317 \
    python -m stock.main
```

## 🔧 Configuration

Environment variables:

```bash
# Database configuration
DATABASE_URL=postgresql://postgres:yourpassword@postgres:5432/mydatabase

# Service configuration
HOST=0.0.0.0
PORT=5001
LOG_LEVEL=INFO

# OpenTelemetry
OTEL_SERVICE_NAME=stock
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

## 📊 API Endpoints

### POST /stocks
Create a new stock entry

**Request:**
```json
{
  "wood_type": "oak",
  "quantity": 100,
  "supplier_id": "supp_456"
}
```

**Response:**
```json
{
  "id": 1,
  "wood_type": "oak",
  "quantity": 100,
  "supplier_id": "supp_456",
  "created_at": "2025-11-08T10:30:00Z"
}
```

### GET /stocks
List all stock entries

### GET /stocks/{wood_type}
Get stock for specific wood type

### PUT /stocks/{wood_type}
Update stock quantity

### POST /stocks/decrease
Decrease stock quantity (used by order processing)

**Request:**
```json
{
  "wood_type": "oak",
  "quantity": 5
}
```

## 📦 Dependencies

- `flask`: Web framework
- `flasgger`: API documentation
- `sqlalchemy`: ORM for database
- `psycopg2-binary`: PostgreSQL adapter
- `common-models`: Shared business models

## 🔄 Integration

The stock service integrates with:

- **Database**: PostgreSQL for stock persistence
- **Suppliercheck**: Consumes stock updates from Kafka and calls this API
- **Order**: Validates stock availability before creating orders
- **Ordermanagement**: Decreases stock when orders are processed
- **OpenTelemetry**: Auto-instrumented for observability

## 🧪 Testing

```bash
# Run tests
uv run pytest

# Check test coverage
uv run pytest --cov=stock --cov-report=html
```

## 📝 Example Usage

```bash
# Create stock entry
curl -X POST http://localhost:5001/stocks \
  -H "Content-Type: application/json" \
  -d '{"wood_type": "oak", "quantity": 100, "supplier_id": "supp_456"}'

# Decrease stock (order processing)
curl -X POST http://localhost:5001/stocks/decrease \
  -H "Content-Type: application/json" \
  -d '{"wood_type": "oak", "quantity": 5}'

# Get stock for specific wood type
curl http://localhost:5001/stocks/oak
```

## 🏗️ Dockerfile

The service uses a multi-stage Docker build:

1. Build stage: Installs dependencies with UV
2. Runtime stage: Runs the FastAPI server

See `stock/Dockerfile` for details.

## 📈 Observability

- **Logs**: Sent to Loki via OpenTelemetry
- **Metrics**: Sent to Mimir via OpenTelemetry
- **Traces**: Sent to Tempo via OpenTelemetry
- **Service Name**: `stock`

## 🔗 Related Services

- **supplier**: Sends stock updates via Kafka
- **suppliercheck**: Validates and processes stock updates
- **order**: Checks stock availability before creating orders
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