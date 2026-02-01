"""
Common AI - Shared AI utilities for AI agents

Includes:
- Agent models: AgentRequest, AgentResponse, AgentType, OrchestratorResponse
- Agent requests: Pydantic models for API requests/responses
- MCP client: MCPGrafanaClient
- LLM configuration: get_llm
- LLM utilities: extract_text_from_response
"""

# Agent models (for AI agents)
from .agent_models import (
    AgentRequest,
    AgentResponse,
    AgentType,
    OrchestratorResponse,
)

# LLM configuration
from .llm_config import get_llm, get_model_params

# MCP client
from .mcp_client import MCPGrafanaClient

# LLM utilities
from .llm_utils import extract_text_from_response

# Ollama utilities
from .ollama_utils import unload_ollama_model

__all__ = [
    # Agent models
    "AgentType",
    "AgentRequest",
    "AgentResponse",
    "OrchestratorResponse",
    # MCP
    "MCPGrafanaClient",
    # LLM
    "get_llm",
    "get_model_params",
    "extract_text_from_response",
    # Ollama
    "unload_ollama_model",
]
