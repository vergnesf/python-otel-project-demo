"""
Common AI - Shared AI utilities for AI agents

Includes:
- Agent models: AgentRequest, AgentResponse, AgentType, OrchestratorResponse
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
from .llm_config import get_llm

# MCP client
from .mcp_client import MCPGrafanaClient

# LLM utilities
from .llm_utils import extract_text_from_response

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
    "extract_text_from_response",
]
