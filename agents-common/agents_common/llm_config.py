"""
LLM configuration for all agents
"""

import os

from langchain_openai import ChatOpenAI


def get_llm(
    model: str = "qwen3",
    temperature: float = 0.1,
    max_tokens: int = 2000,
) -> ChatOpenAI:
    """
    Get configured LLM instance for agents
    
    Uses the local Docker AI Model Runner endpoint by default.
    Can be overridden with environment variables for production use.
    
    Args:
        model: Model name
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens in response
        
    Returns:
        Configured ChatOpenAI instance
        
    Environment Variables:
        LLM_BASE_URL: Base URL for LLM API (default: http://172.17.0.1:12434/engines/llama.cpp/v1)
        LLM_API_KEY: API key (default: dummy-token for local model)
        LLM_MODEL: Model name (default: qwen3)
    """
    base_url = os.getenv("LLM_BASE_URL", "http://172.17.0.1:12434/engines/llama.cpp/v1")
    api_key = os.getenv("LLM_API_KEY", "dummy-token")
    model_name = os.getenv("LLM_MODEL", model)

    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
    )
