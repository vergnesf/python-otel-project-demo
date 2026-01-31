# Ordermanagement Service

The **Ordermanagement Service** is a background worker that periodically checks for registered orders, processes them by decreasing stock, and updates their status to reflect the processing state.

## 📋 Overview

- **Type**: Background Worker
- **Frequency**: Configurable interval (default: 5 seconds)
- **Error Simulation**: Configurable error rate (default: 10%)
- **Dependencies**: Order Service API, Stock Service API, common-models

## 🚀 Running the Service

### With Docker

```bash
docker-compose up ordermanagement
```

### Local Development

```bash
# Navigate to service directory
cd ordermanagement/

# Install dependencies
uv sync

# Run the worker
uv run python -m ordermanagement.ordermanagement
```

## 🔧 Configuration

Environment variables:

```bash
# API endpoints
API_URL_ORDERS=http://order:5000
API_URL_STOCKS=http://stock:5001

# Service behavior
INTERVAL_SECONDS=5           # How often to check for orders (seconds)
ERROR_RATE=0.1               # Percentage of operations that will fail (0.0 to 1.0)
LOG_LEVEL=INFO               # Logging level (DEBUG, INFO, WARNING, ERROR)

# OpenTelemetry
OTEL_SERVICE_NAME=ordermanagement
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

## 📊 Order Processing Flow

1. **Fetch**: Retrieves registered orders from Order Service
2. **Process**: For each order:
   - Decreases stock in Stock Service
   - Updates order status to "processed" or "failed"
3. **Simulate Errors**: Randomly fails based on `ERROR_RATE`
4. **Log**: Records processing results for observability
5. **Wait**: Sleeps for configured interval before next cycle

## 🎯 Error Simulation

The service simulates processing errors based on `ERROR_RATE`:

- Randomly fails stock decrease operations
- Randomly fails order status updates
- Logs detailed error information
- Helps test error handling and recovery

## 📦 Dependencies

- `requests`: HTTP client for API calls
- `common-models`: Shared business models (Order, Stock, OrderStatus)

## 🔄 Integration

The ordermanagement service integrates with:

- **Order Service**: Fetches orders and updates statuses
- **Stock Service**: Decreases stock when orders are processed
- **Ordercheck**: Receives orders that need processing
- **OpenTelemetry**: Auto-instrumented for observability

## 🧪 Testing

```bash
# Run tests
uv run pytest

# Check test coverage
uv run pytest --cov=ordermanagement --cov-report=html
```

## 📝 Example Usage

```bash
# Start with custom interval and error rate
API_URL_ORDERS=http://localhost:5000 API_URL_STOCKS=http://localhost:5001 INTERVAL_SECONDS=10 ERROR_RATE=0.05 uv run python -m ordermanagement.ordermanagement
```

## 🏗️ Dockerfile

The service uses a multi-stage Docker build:

1. Build stage: Installs dependencies with UV
2. Runtime stage: Runs the worker

See `ordermanagement/Dockerfile` for details.

## 📈 Observability

- **Logs**: Sent to Loki via OpenTelemetry
- **Metrics**: Sent to Mimir via OpenTelemetry
- **Traces**: Sent to Tempo via OpenTelemetry
- **Service Name**: `ordermanagement`

## 🔗 Related Services

- **order**: Provides order data and status updates
- **stock**: Manages inventory that gets decreased
- **ordercheck**: Validates orders before they reach this service
- **customer**: Creates orders that eventually get processed