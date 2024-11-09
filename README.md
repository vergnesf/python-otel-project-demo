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

## Kubernetes Section ⚓

Integrating Kubernetes into this project enables efficient deployment and orchestration of microservices. Here are the steps to set up a local test environment using **kind** (Kubernetes IN Docker) 🐳 and to deploy a highly available PostgreSQL database with **CloudNativePG** 🐘.

### Creating a Kubernetes Cluster with kind 🔨

**kind** is a tool that lets you create local Kubernetes clusters using Docker as the container runtime. It’s perfect for quickly testing deployments in a simple environment. ⚡

```sh
kind create cluster -n test-cluster
```

### Deploying CloudNativePG 🐘

**CloudNativePG** is a solution that simplifies managing PostgreSQL databases in a Kubernetes environment, providing high availability features. 🚀 This sets up the necessary resources to run PostgreSQL reliably and efficiently. 🛡️

```sh
kubectl apply --server-side -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.24/releases/cnpg-1.24.1.yaml
```

### Deploy it 🚀

```sh
cd k8s/base
k apply -k .
```