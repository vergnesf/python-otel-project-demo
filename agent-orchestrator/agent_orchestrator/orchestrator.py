"""
Simple Orchestrator with 3 core functionalities:
1. Detect language and translate to English
2. Route to appropriate agent (logs, traces, metrics)
3. Validate the response
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx

from common_ai import get_llm, extract_text_from_response

logger = logging.getLogger(__name__)

# Load prompts from markdown files
PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(filename: str) -> str:
    """Load a prompt template from a markdown file"""
    prompt_path = PROMPTS_DIR / filename
    if prompt_path.exists():
        return prompt_path.read_text()
    logger.warning(f"Prompt file not found: {filename}")
    return ""


class Orchestrator:
    """
    Simple orchestrator with 3 functionalities:
    - Language detection & translation
    - Agent routing (logs, traces, metrics)
    - Response validation
    """

    def __init__(self):
        """Initialize orchestrator with agent endpoints"""
        self.logs_agent_url = os.getenv("AGENT_LOGS_URL", "http://agent-logs:8002")
        self.metrics_agent_url = os.getenv(
            "AGENT_METRICS_URL", "http://agent-metrics:8003"
        )
        self.traces_agent_url = os.getenv(
            "AGENT_TRACES_URL", "http://agent-traces:8004"
        )
        self.translation_agent_url = os.getenv(
            "AGENT_TRANSLATION_URL", "http://agent-traduction:8002"
        )

        self.client = httpx.AsyncClient(timeout=60.0)
        self.agent_call_timeout = int(os.getenv("AGENT_CALL_TIMEOUT", "60"))

        # Initialize LLM
        self.llm_ephemeral = (
            os.getenv("LLM_EPHEMERAL_PER_CALL", "false").lower() == "true"
        )
        try:
            self.llm = None if self.llm_ephemeral else get_llm()
            if self.llm:
                logger.info("LLM initialized for orchestrator")
            else:
                logger.info("LLM will be instantiated per call (ephemeral mode)")
        except Exception as e:
            logger.warning(f"LLM not available: {e}")
            self.llm = None

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def analyze(
        self,
        query: str,
        time_range: str = "1h",
        model: str | None = None,
        model_params: dict | None = None,
    ) -> dict[str, Any]:
        """
        Main analysis flow:
        1. Detect language and translate to English
        2. Route to appropriate agents
        3. Call selected agents
        4. Validate responses

        Args:
            query: User query
            time_range: Time range for analysis
            model: Optional model name to use for this request
            model_params: Optional LLM parameters (temperature, top_k, max_tokens)

        Returns:
            Analysis result with validation
        """
        logger.info(
            f"Analyzing query: {query} (model: {model}, params: {model_params})"
        )
        from datetime import datetime

        # Step 1: Detect language and translate
        language_info = await self._detect_and_translate(
            query, model=model, model_params=model_params
        )
        translated_query = language_info["translated_query"]
        logger.info(
            f"Language: {language_info['language']}, Translated: {translated_query}"
        )

        # Step 2: Route to appropriate agents
        routing = await self._route_to_agents(translated_query, model=model)
        logger.info(f"Routing: {routing}")

        # Step 3: Call selected agents
        agent_request = {
            "query": translated_query,
            "time_range": time_range,
            "context": {},
        }

        agent_responses = await self._call_agents(routing["agents"], agent_request)

        # Step 4: Validate responses
        validation = await self._validate_responses(
            translated_query, agent_responses, model=model
        )

        # Build final response
        summary_parts = []
        recommendations = []

        for agent_name, response in agent_responses.items():
            if response and not isinstance(response.get("error"), str):
                if "analysis" in response:
                    summary_parts.append(
                        f"**{agent_name.upper()}**: {response['analysis']}"
                    )
                if "recommendations" in response:
                    recommendations.extend(response["recommendations"])

        summary = (
            "\n\n".join(summary_parts) if summary_parts else "No analysis available"
        )

        return {
            "query": query,
            "translated_query": translated_query,
            "language": language_info["language"],
            "routing": routing,
            "agent_responses": agent_responses,
            "summary": summary,
            "recommendations": recommendations,
            "validation": validation,
            "timestamp": datetime.now(),
        }

    async def _detect_and_translate(
        self, query: str, model: str | None = None, model_params: dict | None = None
    ) -> dict[str, Any]:
        """
        Functionality 1: Detect language and translate to English

        Args:
            query: User query
            model: Optional model override
            model_params: Optional LLM parameters (temperature, top_k, max_tokens)

        Returns:
            Dictionary with language and translated query
        """
        logger.debug(
            "_detect_and_translate() called with model=%s, params=%s",
            model,
            model_params,
        )

        if not query:
            return {"language": "unknown", "translated_query": query}

        payload: dict[str, Any] = {"query": query}
        if model:
            payload["model"] = model
        if model_params:
            payload["model_params"] = model_params

        try:
            response = await self.client.post(
                f"{self.translation_agent_url}/translate",
                json=payload,
                timeout=self.agent_call_timeout,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            logger.warning("Translation service error: %s", exc)
            return {"language": "unknown", "translated_query": query}

        language = data.get("language", "unknown")
        translated_query = data.get("translated_query", query)

        if not translated_query:
            translated_query = query

        return {"language": language, "translated_query": translated_query}

    async def _route_to_agents(
        self, query: str, model: str | None = None, model_params: dict | None = None
    ) -> dict[str, Any]:
        """
        Functionality 2: Decide which agents to call based on query

        Args:
            query: User query (in English)
            model: Optional model override
            model_params: Optional LLM parameters (temperature, top_k, max_tokens)

        Returns:
            Routing decision with agents to call
        """
        # If no LLM available, use keyword-based fallback
        if not self.llm and not self.llm_ephemeral and not model:
            return self._keyword_based_routing(query)

        try:
            # Always use provided model if specified, otherwise fall back to default
            if model:
                llm_client = (
                    get_llm(model=model, **model_params)
                    if model_params
                    else get_llm(model=model)
                )
            elif self.llm_ephemeral:
                llm_client = get_llm(**model_params) if model_params else get_llm()
            else:
                llm_client = self.llm

            if not llm_client:
                logger.warning("No LLM available, using keyword-based routing")
                return self._keyword_based_routing(query)

            # Load routing prompt
            route_prompt = load_prompt("route_agents.md")
            if not route_prompt:
                return self._keyword_based_routing(query)

            route_prompt = route_prompt.format(query=query)
            response_text = await self._invoke_llm_prompt(
                route_prompt, model=model, model_params=model_params
            )
            if not response_text:
                return self._keyword_based_routing(query)

            # Clean response
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1] if len(lines) > 2 else lines[1:])
                response_text = response_text.strip()
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()

            # Extract JSON
            first_brace = response_text.find("{")
            last_brace = response_text.rfind("}")
            if first_brace != -1 and last_brace != -1:
                response_text = response_text[first_brace : last_brace + 1]

            routing = json.loads(response_text)
            return {
                "agents": routing.get("agents", ["logs"]),
                "reason": routing.get("reason", "LLM routing decision"),
            }

        except Exception as e:
            logger.warning(f"LLM routing failed: {e}, using keyword fallback")
            return self._keyword_based_routing(query)

    async def _invoke_llm_prompt(
        self,
        prompt: str,
        *,
        model: str | None,
        model_params: dict | None,
    ) -> str | None:
        try:
            if model:
                llm_client = (
                    get_llm(model=model, **model_params)
                    if model_params
                    else get_llm(model=model)
                )
            elif self.llm_ephemeral:
                llm_client = get_llm(**model_params) if model_params else get_llm()
            else:
                llm_client = self.llm

            if llm_client:
                response = llm_client.invoke(prompt)
                response_text = extract_text_from_response(response).strip()
                if response_text:
                    return response_text
        except Exception as exc:
            logger.warning("LLM invoke failed: %s", exc)

        try:
            return await self._ollama_generate(prompt, model, model_params)
        except Exception as exc:
            logger.warning("Ollama fallback failed: %s", exc)
            return None

    async def _ollama_generate(
        self,
        prompt: str,
        model: str | None,
        model_params: dict | None,
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

        response = await self.client.post(
            url, json=payload, timeout=self.agent_call_timeout
        )
        response.raise_for_status()
        data = response.json()
        text = data.get("response", "") if isinstance(data, dict) else ""
        return text.strip() if text else None

    def _keyword_based_routing(self, query: str) -> dict[str, Any]:
        """
        Simple keyword-based routing fallback

        Args:
            query: User query

        Returns:
            Routing decision
        """
        query_lower = query.lower()
        agents = []

        # Check for logs keywords
        if any(
            word in query_lower for word in ["log", "error", "exception", "message"]
        ):
            agents.append("logs")

        # Check for metrics keywords
        if any(
            word in query_lower
            for word in ["cpu", "memory", "latency", "rate", "throughput"]
        ):
            agents.append("metrics")

        # Check for traces keywords
        if any(word in query_lower for word in ["trace", "slow", "bottleneck", "span"]):
            agents.append("traces")

        # Default to logs if nothing matched
        if not agents:
            agents = ["logs"]

        return {
            "agents": agents,
            "reason": f"Keyword-based routing: {', '.join(agents)}",
        }

    async def _call_agents(
        self, agents: list[str], request: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Call selected agents in parallel

        Args:
            agents: List of agent names to call
            request: Request to send to agents

        Returns:
            Dictionary mapping agent names to responses
        """
        tasks = []
        agent_urls = {
            "logs": self.logs_agent_url,
            "metrics": self.metrics_agent_url,
            "traces": self.traces_agent_url,
        }

        for agent in agents:
            if agent in agent_urls:
                tasks.append(self._query_agent(agent_urls[agent], request))
            else:
                logger.warning(f"Unknown agent: {agent}")

        if not tasks:
            return {}

        # Execute in parallel
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Map responses
        result = {}
        for i, agent in enumerate([a for a in agents if a in agent_urls]):
            response = responses[i] if i < len(responses) else None
            result[agent] = (
                response
                if not isinstance(response, Exception)
                else {"error": str(response)}
            )

        return result

    async def _query_agent(
        self, agent_url: str, request: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Query a single agent

        Args:
            agent_url: Agent URL
            request: Request payload

        Returns:
            Agent response
        """
        try:
            response = await self.client.post(
                f"{agent_url}/analyze",
                json=request,
                timeout=self.agent_call_timeout,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to query agent at {agent_url}: {e}")
            raise

    async def _validate_responses(
        self,
        query: str,
        agent_responses: dict[str, Any],
        model: str | None = None,
        model_params: dict | None = None,
    ) -> dict[str, Any]:
        """
        Functionality 3: Validate that responses properly answer the query

        Args:
            query: Original query
            agent_responses: Responses from agents
            model: Optional model override
            model_params: Optional LLM parameters (temperature, top_k, max_tokens)

        Returns:
            Validation result
        """
        if not self.llm and not self.llm_ephemeral and not model:
            return {
                "validated": False,
                "reason": "No LLM available for validation",
            }

        try:
            # Always use provided model if specified, otherwise fall back to default
            if model:
                llm_client = (
                    get_llm(model=model, **model_params)
                    if model_params
                    else get_llm(model=model)
                )
            elif self.llm_ephemeral:
                llm_client = get_llm(**model_params) if model_params else get_llm()
            else:
                llm_client = self.llm

            if not llm_client:
                logger.warning("No LLM available for validation")
                return {
                    "validated": False,
                    "reason": "No LLM available for validation",
                }

            # Combine all responses for validation
            combined_response = ""
            for agent, response in agent_responses.items():
                if response and not isinstance(response.get("error"), str):
                    if "analysis" in response:
                        combined_response += f"{agent}: {response['analysis']}\n"

            if not combined_response:
                return {
                    "validated": False,
                    "reason": "No valid responses to validate",
                }

            # Load validation prompt
            validate_prompt = load_prompt("validate_response.md")
            if not validate_prompt:
                return {
                    "validated": False,
                    "reason": "Validation prompt not found",
                }

            validate_prompt = validate_prompt.format(
                query=query, response=combined_response
            )
            response_text = await self._invoke_llm_prompt(
                validate_prompt, model=model, model_params=model_params
            )
            if not response_text:
                return {
                    "validated": False,
                    "reason": "LLM returned empty response",
                }

            # Clean response
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1] if len(lines) > 2 else lines[1:])
                response_text = response_text.strip()
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()

            # Extract JSON
            first_brace = response_text.find("{")
            last_brace = response_text.rfind("}")
            if first_brace != -1 and last_brace != -1:
                response_text = response_text[first_brace : last_brace + 1]

            validation = json.loads(response_text)
            return {
                "validated": validation.get("valid", False),
                "issues": validation.get("issues", []),
                "suggestion": validation.get("suggestion", ""),
            }

        except Exception as e:
            logger.warning(f"Response validation failed: {e}")
            return {
                "validated": False,
                "reason": f"Validation error: {str(e)}",
            }

    async def check_agents_health(self) -> dict[str, str]:
        """
        Check health of all specialized agents

        Returns:
            Dictionary mapping agent names to health status
        """

        async def check_agent(url: str) -> str:
            try:
                response = await self.client.get(f"{url}/health", timeout=5.0)
                return "reachable" if response.status_code == 200 else "unreachable"
            except Exception:
                return "unreachable"

        results = await asyncio.gather(
            check_agent(self.logs_agent_url),
            check_agent(self.metrics_agent_url),
            check_agent(self.traces_agent_url),
            check_agent(self.translation_agent_url),
        )

        return {
            "logs": results[0],
            "metrics": results[1],
            "traces": results[2],
            "translation": results[3],
        }
