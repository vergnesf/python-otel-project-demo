# CLAUDE.md — common-ai

## What this library does

Shared **AI utilities** for all agent services. Provides LLM configuration,
MCP Grafana client, and Pydantic models for the agent layer. Not used by
KEEPER business services.

## Tech stack

- `langchain` + `langchain-openai` — LLM abstraction layer
- `mcp` — Model Context Protocol client for Grafana integration
- `pydantic` — agent request/response models
- `httpx` — async HTTP client
- `pyyaml` — config loading
- `ollama` — local LLM management utilities

## Key files

| File | Purpose |
|------|---------|
| `agent_models.py` | Pydantic models: `AgentRequest`, `AgentResponse`, `AgentType`, `OrchestratorResponse` |
| `llm_config.py` | LLM initialization and config loading |
| `mcp_client.py` | `MCPGrafanaClient` — queries Grafana via MCP protocol |
| `llm_utils.py` | Text extraction utilities for LLM responses |
| `ollama_utils.py` | Ollama model loading/unloading helpers |

## Key exports

```python
from common_ai import AgentType, AgentRequest, AgentResponse
from common_ai import MCPGrafanaClient, get_llm, extract_text_from_response
```

## What I learned building this

LangChain agent patterns, MCP protocol integration with Grafana for observability
queries, and sharing AI infrastructure across multiple agent services.
