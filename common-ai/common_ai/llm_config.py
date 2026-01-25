"""
LLM configuration for all agents
"""

import os
import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)


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
        Override invoke to handle instrumentation errors.
        """
        try:
            return super().invoke(input, *args, **kwargs)
        except AttributeError as e:
            if "'LegacyAPIResponse' object has no attribute 'model'" in str(e):
                logger.warning(f"OpenTelemetry instrumentation error (ignored): {e}")
                # The response was actually generated successfully,
                # but the instrumentation failed
                # The error happens AFTER the response is received, so we need to
                # extract it from the exception context if possible, or call again
                try:
                    # Prefer calling Ollama REST API directly to avoid OpenTelemetry
                    # instrumentation issues with some legacy model runners.
                    import requests

                    ollama_base = (getattr(self, "openai_api_base", None) or os.getenv("LLM_BASE_URL", "http://localhost:11434/api"))
                    logger.info(
                        f"Retrying LLM call via Ollama API (base_url={ollama_base}, model={self.model_name})"
                    )

                    messages = self._convert_input_to_messages(input)

                    url = ollama_base.rstrip("/") + "/chat"
                    resp = requests.post(
                        url,
                        json={
                            "model": self.model_name,
                            "messages": messages,
                            "stream": False,
                        },
                        timeout=30,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    # Ollama /api/chat returns {'message': {'content': ...}} or
                    # /api/generate returns {'response': ...}. Support both.
                    content = None
                    if isinstance(data, dict):
                        msg = data.get("message") or {}
                        content = msg.get("content") or data.get("response")

                    if not content:
                        raise RuntimeError(f"Empty response from Ollama API: {data}")

                    from langchain_core.messages import AIMessage

                    return AIMessage(content=content)
                except Exception as inner_e:
                    logger.error(
                        f"Failed to get LLM response via Ollama: {inner_e}", exc_info=True
                    )
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
    temperature: float = 0.1,
    max_tokens: int = 2000,
) -> ChatOpenAI:
    """
    Get configured LLM instance for agents

    Uses the local Ollama endpoint by default.
    Can be overridden with environment variables for production use.

    Args:
        model: Model name (overrides LLM_MODEL env var if provided)
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens in response

    Returns:
        Configured ChatOpenAI instance

    Environment Variables:
        LLM_BASE_URL: Base URL for LLM API (default: http://localhost:11434/api)
        LLM_API_KEY: API key (default: dummy-token for local model)
        LLM_MODEL: Model name (default: qwen3)
    """
    # Default to Ollama local API
    base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434/api")
    api_key = os.getenv("LLM_API_KEY", "dummy-token")

    # Priority:
    # 1. Function argument 'model' (if not None)
    # 2. Environment variable 'LLM_MODEL'
    # 3. Default "qwen3"
    if model:
        model_name = model
    else:
        model_name = os.getenv("LLM_MODEL", "qwen3")

    logger.info(f"Creating LLM instance: model={model_name}, base_url={base_url}")

    return SafeChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
    )
