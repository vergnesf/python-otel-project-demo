# Common AI

> **Status:** `KEEPER` — Stable service. Expected to stay functional and tested.

Shared AI utilities and MCP client for AI agents.

## Contents

- **Agent models**: AgentRequest, AgentResponse, AgentType, OrchestratorResponse
- **MCP Client**: MCPGrafanaClient for interacting with Grafana MCP server
- **LLM Config**: get_llm() helper for Langchain LLM initialization

## Dependencies

- pydantic>=2.9.2
- httpx>=0.27.0
- langchain>=0.3.0
- langchain-openai>=0.2.0

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
