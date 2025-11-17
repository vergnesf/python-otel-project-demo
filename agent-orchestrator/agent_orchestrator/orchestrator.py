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

    async def analyze(self, query: str, time_range: str = "1h") -> dict[str, Any]:
        """
        Main analysis flow:
        1. Detect language and translate to English
        2. Route to appropriate agents
        3. Call selected agents
        4. Validate responses

        Args:
            query: User query
            time_range: Time range for analysis

        Returns:
            Analysis result with validation
        """
        logger.info(f"Analyzing query: {query}")
        from datetime import datetime

        # Step 1: Detect language and translate
        language_info = await self._detect_and_translate(query)
        translated_query = language_info["translated_query"]
        logger.info(
            f"Language: {language_info['language']}, Translated: {translated_query}"
        )

        # Step 2: Route to appropriate agents
        routing = await self._route_to_agents(translated_query)
        logger.info(f"Routing: {routing}")

        # Step 3: Call selected agents
        agent_request = {
            "query": translated_query,
            "time_range": time_range,
            "context": {},
        }

        agent_responses = await self._call_agents(routing["agents"], agent_request)

        # Step 4: Validate responses
        validation = await self._validate_responses(translated_query, agent_responses)

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

    async def _detect_and_translate(self, query: str) -> dict[str, Any]:
        """
        Functionality 1: Detect language and translate to English

        Args:
            query: User query

        Returns:
            Dictionary with language and translated query
        """
        if not query:
            return {"language": "unknown", "translated_query": query}

        # If no LLM available, assume English
        if not self.llm and not self.llm_ephemeral:
            return {"language": "unknown", "translated_query": query}

        try:
            llm_client = get_llm() if self.llm_ephemeral else self.llm
            if not llm_client:
                logger.warning("No LLM available, assuming English")
                return {"language": "unknown", "translated_query": query}

            # First, detect if it's English
            detect_prompt = load_prompt("detect_language.md")
            if detect_prompt:
                detect_prompt = detect_prompt.format(query=query)
                response = llm_client.invoke(detect_prompt)
                language_result = extract_text_from_response(response).strip().upper()

                # If already English, no need to translate
                # Check for exact "ENGLISH" but not "NOT_ENGLISH" or "NON_ENGLISH"
                if language_result == "ENGLISH" or (
                    "ENGLISH" in language_result
                    and "NOT" not in language_result
                    and "NON" not in language_result
                ):
                    return {"language": "english", "translated_query": query}

            # Not English, translate
            translate_prompt = load_prompt("translate_to_english.md")
            if not translate_prompt:
                return {"language": "unknown", "translated_query": query}

            translate_prompt = translate_prompt.format(query=query)
            response = llm_client.invoke(translate_prompt)
            translated = extract_text_from_response(response).strip()

            # Clean up translation (remove code blocks if any)
            if translated.startswith("```"):
                lines = translated.split("\n")
                translated = "\n".join(lines[1:-1] if len(lines) > 2 else lines[1:])
                translated = translated.strip()

            return {
                "language": "non-english",
                "translated_query": translated if translated else query,
            }

        except Exception as e:
            logger.warning(f"Language detection/translation failed: {e}")
            return {"language": "unknown", "translated_query": query}

    async def _route_to_agents(self, query: str) -> dict[str, Any]:
        """
        Functionality 2: Decide which agents to call based on query

        Args:
            query: User query (in English)

        Returns:
            Routing decision with agents to call
        """
        # If no LLM available, use keyword-based fallback
        if not self.llm and not self.llm_ephemeral:
            return self._keyword_based_routing(query)

        try:
            llm_client = get_llm() if self.llm_ephemeral else self.llm
            if not llm_client:
                logger.warning("No LLM available, using keyword-based routing")
                return self._keyword_based_routing(query)

            # Load routing prompt
            route_prompt = load_prompt("route_agents.md")
            if not route_prompt:
                return self._keyword_based_routing(query)

            route_prompt = route_prompt.format(query=query)
            response = llm_client.invoke(route_prompt)
            response_text = extract_text_from_response(response).strip()

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
        self, query: str, agent_responses: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Functionality 3: Validate that responses properly answer the query

        Args:
            query: Original query
            agent_responses: Responses from agents

        Returns:
            Validation result
        """
        if not self.llm and not self.llm_ephemeral:
            return {
                "validated": False,
                "reason": "No LLM available for validation",
            }

        try:
            llm_client = get_llm() if self.llm_ephemeral else self.llm
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
            response = llm_client.invoke(validate_prompt)
            response_text = extract_text_from_response(response).strip()

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
        )

        return {
            "logs": results[0],
            "metrics": results[1],
            "traces": results[2],
        }
