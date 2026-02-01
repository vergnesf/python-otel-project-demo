"""
Translation service logic for language detection and translation.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import httpx

from common_ai import extract_text_from_response, get_llm

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(filename: str) -> str:
    """Load a prompt template from a markdown file."""
    prompt_path = PROMPTS_DIR / filename
    if prompt_path.exists():
        return prompt_path.read_text()
    logger.warning("Prompt file not found: %s", filename)
    return ""


class TranslationService:
    """Handle language detection and translation using an LLM."""

    def __init__(self) -> None:
        self.llm_ephemeral = (
            os.getenv("LLM_EPHEMERAL_PER_CALL", "false").lower() == "true"
        )
        try:
            self.llm = None if self.llm_ephemeral else get_llm()
            if self.llm:
                logger.info("LLM initialized for translation service")
            else:
                logger.info("LLM will be instantiated per call (ephemeral mode)")
        except Exception as exc:
            logger.warning("LLM not available: %s", exc)
            self.llm = None

    def translate(
        self,
        query: str,
        model: str | None = None,
        model_params: dict | None = None,
    ) -> dict[str, Any]:
        """
        Detect language and translate to English when required.

        Args:
            query: Input query.
            model: Optional model override.
            model_params: Optional LLM parameters.

        Returns:
            Dictionary with language and translated query.
        """
        if not query:
            return {
                "agent_name": "translation",
                "language": "unknown",
                "translated_query": query,
            }

        try:
            language = self._detect_language(query, model, model_params)
            if language == "non-english":
                translated_query = self._translate_to_english(
                    query, model, model_params
                )
            else:
                translated_query = query

            if not translated_query:
                translated_query = query

            return {
                "agent_name": "translation",
                "language": language,
                "translated_query": translated_query,
            }
        except Exception as exc:
            logger.warning("Translation failed: %s", exc)
            return {
                "agent_name": "translation",
                "language": "unknown",
                "translated_query": query,
            }

    def _detect_language(
        self,
        query: str,
        model: str | None,
        model_params: dict | None,
    ) -> str:
        prompt = load_prompt("detect_language.md")
        if not prompt:
            return "unknown"

        response_text = self._invoke_llm_prompt(
            prompt.format(query=query), model, model_params
        )
        if not response_text:
            return "unknown"

        response_text = response_text.upper()

        if "NOT_ENGLISH" in response_text:
            return "non-english"
        if "ENGLISH" in response_text:
            return "english"

        return "unknown"

    def _translate_to_english(
        self,
        query: str,
        model: str | None,
        model_params: dict | None,
    ) -> str:
        prompt = load_prompt("translate_to_english.md")
        if not prompt:
            return query

        response_text = self._invoke_llm_prompt(
            prompt.format(query=query), model, model_params
        )
        if not response_text:
            return query

        translated_text = response_text.strip()

        return translated_text or query

    def _get_llm(self, model: str | None, model_params: dict | None) -> Any:
        params = model_params or {}
        if model:
            return get_llm(model=model, **params)
        if self.llm_ephemeral:
            return get_llm(**params)
        return self.llm

    def _invoke_llm_prompt(
        self, prompt: str, model: str | None, model_params: dict | None
    ) -> str | None:
        llm_client = self._get_llm(model, model_params)
        if llm_client:
            try:
                response = llm_client.invoke(prompt)
                response_text = extract_text_from_response(response).strip()
                if response_text:
                    return response_text
            except Exception as exc:
                logger.warning("LLM invoke failed: %s", exc)

        try:
            return self._ollama_generate(prompt, model, model_params)
        except Exception as exc:
            logger.warning("Ollama fallback failed: %s", exc)
            return None

    def _ollama_generate(
        self, prompt: str, model: str | None, model_params: dict | None
    ) -> str | None:
        base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
        if base_url.endswith("/v1"):
            base_url = base_url[:-3]
        if base_url.endswith("/api"):
            url = f"{base_url}/generate"
        else:
            url = f"{base_url}/api/generate"

        model_name = model or os.getenv("LLM_MODEL", "qwen3:0.6b")
        payload: dict[str, Any] = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
        }

        options: dict[str, Any] = {}
        params = model_params or {}
        if "temperature" in params:
            options["temperature"] = params["temperature"]
        if params.get("top_k") is not None:
            options["top_k"] = params["top_k"]
        if "max_tokens" in params:
            options["num_predict"] = params["max_tokens"]
        if "context_size" in params:
            options["num_ctx"] = params["context_size"]

        if options:
            payload["options"] = options

        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        text = data.get("response", "") if isinstance(data, dict) else ""
        return text.strip() if text else None
