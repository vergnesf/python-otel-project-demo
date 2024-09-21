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

The entire application is containerized, and the `docker-compose` file will build all the microservices and deploy the following additional components:

- **Kafka**: A cluster to receive orders and stock updates 📨
- **PostgreSQL**: PostgreSQL database 🗄️
- **Adminer**: Web tool for viewing your database 📂
- **Grafana**: Visualization tool 📊
- **Loki**: Log database 📝
- **Mimir**: Metrics database 📈
- **Tempo**: Traces database 📍
- **Otel Gateway**: API for receiving observability data 🛠️

To run everything, use:

```sh
docker compose up -d --build
```

### Useful URLs 🌐

- [Grafana](http://localhost:3000/) 📊
- [AKHQ](http://localhost:8080/) 🛠️
- [Adminer](http://localhost:8081/) 🗃️

## Running Locally 🐛

Each microservice is set up with **Poetry**, so you can launch the different services using `poetry run`.

Locally, you'll need to modify `PYTHONPATH` to include the project and access the "common" part, which simplifies things for me.

To run a microservice with auto-instrumentation:

```sh
poetry run opentelemetry-instrument \
    --traces_exporter console,otlp \
    --metrics_exporter console,otlp \
    --service_name customer2 \
    --exporter_otlp_endpoint http://localhost:4317 \
    --log_level debug \
    python -m order.main
```