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

The entire application is containerized, and the `podman-stack.yml` file will build all the microservices and deploy the following additional components:

- **Kafka**: A cluster to receive orders and stock updates 📨
- **PostgreSQL**: PostgreSQL database 🗄️
- **Adminer**: Web tool for viewing your database 📂
- **Grafana**: Visualization tool 📊
- **Loki**: Log database 📝
- **Mimir**: Metrics database 📈
- **Tempo**: Traces database 📍
- **Otel Gateway**: API for receiving observability data 🛠️

## Configuration �️

### Environment Variables
All image versions and registry configuration are managed in the `.env` file:

```bash
# Docker Registry (leave empty for Docker Hub)
DOCKER_REGISTRY=
# DOCKER_REGISTRY=my-registry.com/
# DOCKER_REGISTRY=registry.gitlab.com/myproject/

# Image versions (update as needed)
IMG_GRAFANA=grafana/grafana:12.0.2
IMG_LOKI=grafana/loki:3.5.2
IMG_TEMPO=grafana/tempo:2.8.1
# ... and more
```

Copy `.env.example` to `.env` and customize as needed:
```sh
cp .env.example .env
```

## Running the Application 🚀

### With Docker Compose
```sh
# Start all services
docker-compose up -d

# Build and start
docker-compose up --build -d
```

### With Podman (Legacy)
```sh
# Build all image
podman build -f customer/Dockerfile -t customer:latest .
podman build -f supplier/Dockerfile -t supplier:latest .
podman build -f order/Dockerfile -t order:latest .
podman build -f ordercheck/Dockerfile -t ordercheck:latest .
podman build -f ordermanagement/Dockerfile -t ordermanagement:latest .
podman build -f stock/Dockerfile -t stock:latest .
podman build -f supplier/Dockerfile -t supplier:latest .
podman build -f suppliercheck/Dockerfile -t suppliercheck:latest .

# Run
podman play kube podman-stack.yml --replace
```

### Useful URLs 🌐

- [Grafana](http://localhost:3000/) 📊
- [AKHQ](http://localhost:8080/) 🛠️
- [Adminer](http://localhost:8081/) 🗃️

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