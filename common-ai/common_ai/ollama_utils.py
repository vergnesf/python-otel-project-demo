"""
Utilities for managing Ollama models and resources.
"""

import asyncio
import httpx
import os


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
        ollama_base = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
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
                print(f"{Colors.GREEN}✓ Unloaded Ollama model(s){Colors.END}")
                await asyncio.sleep(1)  # Give system time to release GPU memory
                return True
            else:
                print(
                    f"{Colors.YELLOW}⚠️  Ollama API returned status {response.status_code}{Colors.END}"
                )
                return False

    except Exception as e:
        print(
            f"{Colors.YELLOW}⚠️  Could not unload Ollama model via API: {e}{Colors.END}"
        )
        return False
