# Architecture

## About the Project

This project is a comprehensive microservices platform developed to showcase Python auto-instrumentation with OpenTelemetry. It features:

- **Business Application**: Complete order and stock management system for a wood supply business
- **Observability Stack**: Full Grafana stack (Loki, Mimir, Tempo) with OpenTelemetry auto-instrumentation
- **AI-Powered Analysis**: Intelligent agentic network for natural language observability queries
- **Modern Python Stack**: Python 3.14, UV package manager, FastAPI, Pydantic
- **Production-Ready Patterns**: Docker-first, configurable, with error simulation for testing

This is not just a demo - it's a complete reference implementation demonstrating modern observability best practices.

## Microservices

The application consists of the following microservices:

- **customer** 🪵 - Kafka producer acting as a client for ordering wood
- **supplier** 🪵 - Kafka producer acting as a supplier to replenish stock
- **ordercheck** 📦 - Kafka consumer serving as the order reception service
- **suppliercheck** 📊 - Kafka consumer managing stock levels
- **stock** 🏗️ - Stock management API
- **order** 📝 - Order management API
- **ordermanagement** 😄 - Service for updating order status

## Infrastructure Components

The complete application is containerized. The `docker-compose.yml` file builds all microservices and deploys the following components:

- **Kafka** 📨 - Cluster to receive orders and stock updates
- **PostgreSQL** 🗄️ - Relational database
- **Adminer** 📂 - Web interface for database visualization
- **Grafana** 📊 - Standard visualization tool
- **Grafana with MCP support** 🤖 - Enhanced Grafana with Model Context Protocol for AI integration
- **Loki** 📝 - Log database
- **Mimir** 📈 - Metrics database
- **Tempo** 📍 - Traces database
- **Otel Gateway** 🛠️ - API for receiving observability data

## Project Structure

```
python-otel-project-demo/
├── common-models/                # Shared business models (for all business services)
│   ├── common_models/
│   │   ├── __init__.py
│   │   └── models.py            # Business models (WoodType, Order, Stock, OrderTracking)
│   ├── pyproject.toml
│   └── README.md
├── common-ai/                    # Shared AI utilities (for AI agents only)
│   ├── common_ai/
│   │   ├── __init__.py
│   │   ├── agent_models.py      # Agent models (AgentRequest, AgentResponse, AgentType)
│   │   ├── mcp_client.py        # MCP client for Grafana datasources
│   │   └── llm_config.py        # LLM configuration helper
│   ├── pyproject.toml
│   └── README.md
├── customer/                     # Microservice: Kafka producer (customer orders)
├── order/                        # Microservice: Order management API
├── stock/                        # Microservice: Stock management API
├── supplier/                     # Microservice: Kafka producer (supplier)
├── ordercheck/                   # Microservice: Kafka consumer (order processing)
├── suppliercheck/                # Microservice: Kafka consumer (stock updates)
├── ordermanagement/              # Microservice: Order status updates
├── agent-orchestrator/           # AI Agent: Main coordinator
├── agent-logs/                   # AI Agent: Loki log analysis
├── agent-metrics/                # AI Agent: Mimir metrics analysis
├── agent-traces/                 # AI Agent: Tempo traces analysis
├── agents-ui/                    # Web UI for agents
├── docs/                         # Documentation
└── docker-compose.yml            # Complete stack orchestration
```

### Shared Modules

**common-models/** - Business domain models shared across microservices:
- Used by: `order`, `stock`, `customer`, `supplier`, `ordercheck`, `suppliercheck`, `ordermanagement`
- Contains: `WoodType`, `OrderStatus`, `Stock`, `Order`, `OrderTracking`
- Dependencies: Only `pydantic` (lightweight)

**common-ai/** - AI utilities for intelligent agents:
- Used by: `agent-orchestrator`, `agent-logs`, `agent-metrics`, `agent-traces`
- Contains: MCP client, LLM config, agent models
- Dependencies: `httpx`, `langchain`, `langchain-openai`, `pydantic`

## Technology Stack

- **Python 3.14+** - Latest stable Python version
- **UV** - Fast Python package manager and resolver
- **FastAPI** - Modern web framework for REST APIs
- **Pydantic** - Data validation using Python type annotations
- **OpenTelemetry** - Observability instrumentation
- **LangChain** - Framework for LLM applications (agents only)
- **Kafka** - Message streaming platform
- **PostgreSQL** - Relational database
- **Grafana Stack** - Loki (logs), Mimir (metrics), Tempo (traces)

## Error Simulation

🎭 The application includes built-in error simulation for testing observability:

- **Customer Service** - Simulates Kafka/network failures when sending orders
- **Supplier Check Service** - Simulates API/network failures when processing stock updates
- **Configurable Error Rate** - Set `ERROR_RATE` environment variable (default: 0.1 = 10%)

Example configuration:

```bash
# In docker-compose.yml or your environment
ERROR_RATE=0.2  # 20% error rate for testing
```
