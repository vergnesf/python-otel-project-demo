"""
LLM configuration for all agents
"""

import os
import logging
from typing import Any
from pathlib import Path

import yaml
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)

# Global cache for model params config
_MODEL_PARAMS_CONFIG = None


def load_model_params_config() -> dict:
    """
    Load model parameters configuration from config/ai/model-params.yml
    
    Returns:
        Dictionary with default and model-specific parameters
    """
    global _MODEL_PARAMS_CONFIG
    
    if _MODEL_PARAMS_CONFIG is not None:
        return _MODEL_PARAMS_CONFIG
    
    # Try multiple paths (development, docker, installed package)
    possible_paths = [
        Path(__file__).parent.parent.parent / "config" / "ai" / "model-params.yml",  # From common-ai in workspace
        Path("/app/config/ai/model-params.yml"),  # Docker container
        Path.cwd() / "config" / "ai" / "model-params.yml",  # Current directory
    ]
    
    for config_path in possible_paths:
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    _MODEL_PARAMS_CONFIG = yaml.safe_load(f)
                    logger.info(f"Loaded model parameters config from {config_path}")
                    return _MODEL_PARAMS_CONFIG
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
    
    # Fallback to default config if file not found
    logger.warning("Model params config file not found, using hardcoded defaults")
    _MODEL_PARAMS_CONFIG = {
        "default": {"temperature": 0.1, "top_k": None, "max_tokens": 2000},
        "models": {}
    }
    return _MODEL_PARAMS_CONFIG


def get_model_params(model_name: str) -> dict:
    """
    Get optimal parameters for a given model from configuration.
    
    Args:
        model_name: Name of the model (e.g., 'qwen3:0.6b')
    
    Returns:
        Dictionary with temperature, top_k, max_tokens, etc.
    """
    config = load_model_params_config()
    models_config = config.get("models", {})
    
    # Try exact match first
    if model_name in models_config:
        logger.debug(f"Found specific config for model: {model_name}")
        return models_config[model_name]
    
    # Try without tag (e.g., 'qwen3' from 'qwen3:0.6b')
    base_name = model_name.split(":")[0] if ":" in model_name else model_name
    for config_key in models_config:
        if config_key.startswith(base_name):
            logger.debug(f"Found config for model {model_name} using key: {config_key}")
            return models_config[config_key]
    
    # Fallback to default
    default_params = config.get("default", {"temperature": 0.1, "top_k": None, "max_tokens": 2000})
    logger.warning(f"No specific config found for model '{model_name}', using default: {default_params}")
    return default_params


class SafeChatOpenAI(ChatOpenAI):
    """
    ChatOpenAI wrapper that handles instrumentation errors gracefully.

    Some local runtimes may return legacy responses that don't include a
    `.model` attribute which causes OpenTelemetry instrumentation to fail.
    This wrapper captures the response content and retries via the configured
    REST API (Ollama by default) when necessary.
    """

    def invoke(self, input: Any, *args, **kwargs) -> BaseMessage:
        """
        Override invoke to handle instrumentation errors gracefully.
        
        Note: Uses OpenAI-compatible API only. Native Ollama API fallback
        removed in favor of simpler, more reliable approach.
        """
        logger.debug(f"SafeChatOpenAI.invoke() called with model={self.model_name}")
        try:
            return super().invoke(input, *args, **kwargs)
        except AttributeError as e:
            if "'LegacyAPIResponse' object has no attribute 'model'" in str(e):
                logger.warning(f"OpenTelemetry instrumentation error (response was generated): {e}")
                # Response was actually generated; error only in instrumentation
                raise
            else:
                raise

    def _convert_input_to_messages(self, input: Any) -> list[dict]:
        """Convert LangChain input format to OpenAI API format."""
        if isinstance(input, str):
            return [{"role": "user", "content": input}]
        elif isinstance(input, list):
            messages = []
            for msg in input:
                if hasattr(msg, "type") and hasattr(msg, "content"):
                    messages.append({"role": msg.type, "content": msg.content})
                elif isinstance(msg, dict):
                    messages.append(msg)
            return messages
        else:
            return [{"role": "user", "content": str(input)}]


def get_llm(
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_k: int | None = None,
    **kwargs,
) -> ChatOpenAI:
    """
    Get configured LLM instance for agents

    Uses the local Ollama endpoint by default.
    Can be overridden with environment variables for production use.
    
    If temperature/max_tokens/top_k are not provided, loads optimal values
    from config/ai/model-params.yml based on the model name.

    Args:
        model: Model name (overrides LLM_MODEL env var if provided)
        temperature: Sampling temperature (0-1), None = use config
        max_tokens: Maximum tokens in response, None = use config
        top_k: Top-k sampling parameter (Ollama-specific), None = use config
        **kwargs: Additional model parameters

    Returns:
        Configured ChatOpenAI instance

    Environment Variables:
        LLM_BASE_URL: Base URL for LLM API (default: http://localhost:11434/v1 for OpenAI-compatible endpoint)
        LLM_API_KEY: API key (default: dummy-token for local model)
        LLM_MODEL: Model name (default: qwen3:0.6b)
    """
    # Default to Ollama local API with OpenAI-compatible endpoint
    base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    api_key = os.getenv("LLM_API_KEY", "dummy-token")

    # Priority:
    # 1. Function argument 'model' (if not None)
    # 2. Environment variable 'LLM_MODEL'
    # 3. Default "qwen3"
    if model:
        model_name = model
    else:
        model_name = os.getenv("LLM_MODEL", "qwen3:0.6b")

    # Load model-specific params from config if not explicitly provided
    model_config = get_model_params(model_name)
    
    if temperature is None:
        temperature = model_config.get("temperature", 0.1)
    if max_tokens is None:
        max_tokens = model_config.get("max_tokens", 2000)
    if top_k is None:
        top_k = model_config.get("top_k")

    logger.info(f"Creating LLM instance: model={model_name}, base_url={base_url}, temp={temperature}, top_k={top_k}, max_tokens={max_tokens}")
    logger.debug(f"get_llm() called with model parameter={model}, final model_name={model_name}")

    # Build model_kwargs for Ollama-specific parameters
    model_kwargs = {}
    if top_k is not None:
        model_kwargs["top_k"] = top_k
    model_kwargs.update(kwargs)

    return SafeChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        model_kwargs=model_kwargs if model_kwargs else None,
    )
