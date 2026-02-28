"""
Utilities for managing Ollama models and resources.
"""

import asyncio
import os

import httpx


class Colors:
    """ANSI color codes for terminal output"""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"


async def unload_ollama_model(model_name: str | None = None) -> bool:
    """
    Unload Ollama models to free GPU memory using the API.

    This function uses the Ollama REST API to unload a specific model
    or all models by setting keep_alive=0 for immediate unload.

    Args:
        model_name: Optional specific model to unload. If None, uses dummy
                   model to trigger general unload.

    Returns:
        bool: True if unload was successful or model not found, False otherwise.
    """
    try:
        # Get Ollama base URL from environment or use default
        # For agents in Docker: http://ollama:11434
        # For external tools via Traefik: http://localhost:8081/ollama
        ollama_base = os.getenv("OLLAMA_URL") or os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
        # Remove /v1 suffix if present to get base API URL
        if ollama_base.endswith("/v1"):
            ollama_base = ollama_base[:-3]

        url = f"{ollama_base}/api/generate"

        async with httpx.AsyncClient(timeout=10.0) as client:
            # If model_name is provided, unload specific model
            # Otherwise, use a dummy request with keep_alive=0 to unload all
            payload = {
                "model": model_name if model_name else "dummy",
                "prompt": "",
                "stream": False,
                "keep_alive": 0,  # 0 = unload immediately
            }

            response = await client.post(url, json=payload)

            if response.status_code in [200, 404]:  # 404 is OK if model not loaded
                await asyncio.sleep(1)  # Give system time to release GPU memory
                return True
            else:
                return False

    except Exception:
        return False


async def load_ollama_model(model_name: str) -> bool:
    """
    Load/warm up an Ollama model by making a minimal request.
    
    This ensures the model is loaded into memory before benchmarking,
    so that the first test doesn't include model loading time.
    
    Args:
        model_name: Name of the model to load (e.g., "qwen3:0.6b")
    
    Returns:
        bool: True if load was successful, False otherwise.
    """
    try:
        # Get Ollama base URL from environment or use default
        # For agents in Docker: http://ollama:11434
        # For external tools via Traefik: http://localhost:8081/ollama
        ollama_base = os.getenv("OLLAMA_URL") or os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
        # Remove /v1 suffix if present to get base API URL
        if ollama_base.endswith("/v1"):
            ollama_base = ollama_base[:-3]

        url = f"{ollama_base}/api/generate"

        # Make a minimal request to load the model (only 1 token)
        payload = {
            "model": model_name,
            "prompt": "Hi",
            "stream": False,
            "options": {
                "num_predict": 1,  # Only generate 1 token for fast warm-up
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

        return True

    except Exception:
        return False
