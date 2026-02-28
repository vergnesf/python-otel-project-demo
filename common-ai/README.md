# Common AI

> **Status:** `KEEPER` — Stable library. Expected to stay functional and tested.

Shared AI utilities and MCP client for all agent services. Not used by KEEPER business services.

## Why I built this

To learn LangChain agent patterns, MCP protocol integration with Grafana for observability
queries, and how to share AI infrastructure across multiple agent services without duplication.

## Contents

| File | Purpose |
|------|---------|
| `agent_models.py` | Pydantic models: `AgentRequest`, `AgentResponse`, `AgentType`, `OrchestratorResponse` |
| `llm_config.py` | LLM initialization and YAML config loading |
| `mcp_client.py` | `MCPGrafanaClient` — queries Grafana via MCP protocol |
| `llm_utils.py` | Text extraction utilities for LLM responses |
| `ollama_utils.py` | Ollama model loading/unloading helpers |

See `common_ai/__init__.py` for the current public API.

## Dependencies

- `langchain` + `langchain-openai` — LLM abstraction layer
- `mcp` — Model Context Protocol client
- `pydantic` — agent request/response models
- `httpx` — async HTTP client
- `pyyaml` — config loading

## Development

```bash
cd common-ai/ && uv sync
uv run ruff check .
uv run pytest
```
