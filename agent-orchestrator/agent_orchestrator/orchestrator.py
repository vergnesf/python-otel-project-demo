"""
Orchestrator logic for coordinating specialized agents
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

import httpx
import re

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


# Use extract_text_from_response from common_ai instead of local function


class Orchestrator:
    """
    Main orchestrator that coordinates specialized observability agents
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
        # Per-agent call timeout (seconds) - configurable to avoid UI timeouts
        self.agent_call_timeout = int(os.getenv("AGENT_CALL_TIMEOUT", "60"))

        # Initialize LLM for synthesis (optional, can be None if LLM not available)
        # If LLM_EPHEMERAL_PER_CALL is set to 'true', we will instantiate a fresh
        # LLM client per call to avoid preserving conversation state between calls.
        self.llm_ephemeral = (
            os.getenv("LLM_EPHEMERAL_PER_CALL", "false").lower() == "true"
        )
        try:
            # Keep a shared instance as a fallback when ephemeral is disabled
            self.llm = None if self.llm_ephemeral else get_llm()
            if self.llm:
                logger.info("LLM initialized for orchestrator (shared instance)")
            else:
                logger.info(
                    "LLM will be instantiated per call (ephemeral mode=%s)",
                    self.llm_ephemeral,
                )
        except Exception as e:
            logger.warning(f"LLM not available, using basic synthesis: {e}")
            self.llm = None

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def analyze(self, query: str, time_range: str = "1h") -> dict[str, Any]:
        """
        Analyze user query by coordinating specialized agents
        Uses LLM to intelligently route to the right agents

        Args:
            query: User query to analyze
            time_range: Time range for analysis

        Returns:
            Synthesized response from selected agents
        """
        logger.info(f"Analyzing query: {query}")

        # Translate to English if the query is not English
        translated_query = await self._translate_to_english(query)
        logger.info(f"Translated query: {translated_query}")

        # Use LLM to decide which agents to call (use translated query)
        routing_decision = await self._route_query(translated_query)
        logger.info(f"Routing decision: {routing_decision}")

        # Handle non-observability queries
        if routing_decision["query_type"] in ["greeting", "other"]:
            from datetime import datetime

            if routing_decision["query_type"] == "greeting":
                return {
                    "query": query,
                    "summary": "👋 Bonjour ! Je suis votre assistant d'observabilité. Je peux vous aider à analyser la santé de vos services en examinant les logs, métriques et traces. N'hésitez pas à me poser des questions sur vos applications !",
                    "agent_responses": {},
                    "recommendations": [
                        "Demandez-moi par exemple : 'Quelle est la santé de mes services ?'",
                        "Ou : 'Y a-t-il des erreurs dans le service customer ?'",
                        "Ou : 'Quels services ont des problèmes de performance ?'",
                    ],
                    "timestamp": datetime.now(),
                }
            else:
                return {
                    "query": query,
                    "summary": f"Je suis spécialisé dans l'analyse d'observabilité. {routing_decision['reasoning']}",
                    "agent_responses": {},
                    "recommendations": [
                        "Posez des questions sur les erreurs, la performance, ou la santé des services",
                        "Exemples : 'Y a-t-il des erreurs ?', 'Quel est le taux d'erreur ?', 'Les services sont-ils lents ?'",
                    ],
                    "timestamp": datetime.now(),
                }

        # Prepare request for agents
        agent_request = {
            "query": query,
            "time_range": time_range,
            "context": self._extract_context(query),
        }

        # Query only the selected agents in parallel
        agents_to_call = routing_decision.get("agents_to_call", [])
        tasks = []
        agent_names = []

        if "logs" in agents_to_call:
            tasks.append(self._query_agent(self.logs_agent_url, agent_request))
            agent_names.append("logs")
        if "metrics" in agents_to_call:
            tasks.append(self._query_agent(self.metrics_agent_url, agent_request))
            agent_names.append("metrics")
        if "traces" in agents_to_call:
            tasks.append(self._query_agent(self.traces_agent_url, agent_request))
            agent_names.append("traces")

        # Execute queries in parallel
        if tasks:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            responses = []

        # Map responses to agent names
        agent_responses_dict = {}
        for i, agent_name in enumerate(agent_names):
            response = responses[i] if i < len(responses) else None
            agent_responses_dict[agent_name] = (
                response
                if not isinstance(response, Exception)
                else {"error": str(response)}
            )

        # Add None for agents that were not called
        logs_response = agent_responses_dict.get("logs")
        metrics_response = agent_responses_dict.get("metrics")
        traces_response = agent_responses_dict.get("traces")

        # Synthesize responses
        summary = self._synthesize_responses(
            query=query,
            logs=logs_response,
            metrics=metrics_response,
            traces=traces_response,
        )

        return {
            "query": query,
            "original_query": query,
            "translated_query": translated_query,
            "summary": summary["summary"],
            "agent_responses": agent_responses_dict,
            "recommendations": summary["recommendations"],
            "routing": routing_decision,  # Include routing decision for transparency
            "timestamp": summary["timestamp"],
        }

    async def _translate_to_english(self, query: str) -> str:
        """
        Translate the input query to English using the available LLM.
        If no LLM available or translation fails, return the original query.

        Returns:
            Translated query (or original if translation not possible)
        """
        if not query:
            return query

        # Prefer LLM for language detection/translation when available
        # Fallback: if the query contains any non-ascii letters (e.g., accented), attempt translation
        def _simple_nonascii_check(s: str) -> bool:
            try:
                s.encode("ascii")
                return False
            except UnicodeEncodeError:
                return True

        need_translation = _simple_nonascii_check(query)

        # If no sign of non-ascii and no LLM, assume English
        if not need_translation and not self.llm:
            return query

        # If LLM available, ask it to translate
        if self.llm or self.llm_ephemeral:
            try:
                prompt = f"Translate the following user question to English. Return only the translated sentence (no explanations):\n\n{query}"
                llm_client = get_llm() if self.llm_ephemeral else self.llm
                response = llm_client.invoke(prompt)
                text = extract_text_from_response(response)
                # Strip code blocks and surrounding text
                text = text.strip()
                if text.startswith("```"):
                    parts = text.split("\n")
                    text = "\n".join(parts[1:-1]) if len(parts) > 2 else parts[1]
                # If the translation is empty, fallback
                if not text:
                    return query
                return text.strip()
            except Exception as e:
                logger.warning(
                    f"Translation with LLM failed: {e}, using original query"
                )
                return query

        # No LLM - return original
        return query

    async def _query_agent(
        self, agent_url: str, request: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Query a specialized agent

        Args:
            agent_url: URL of the agent
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
            # Try to log response details if available for easier debugging
            resp = getattr(e, "request", None)
            try:
                status = None
                body = None
                if hasattr(e, "response") and e.response is not None:
                    status = e.response.status_code
                    # read text safely
                    body = e.response.text
                logger.error(
                    "Failed to query agent at %s: %s (status=%s, body=%s)",
                    agent_url,
                    e,
                    status,
                    body,
                )
            except Exception:
                logger.error(f"Failed to query agent at {agent_url}: {e}")
            raise

    async def _route_query(self, query: str) -> dict[str, Any]:
        """
        Use LLM to intelligently decide which agents to call

        Args:
            query: User query

        Returns:
            Routing decision with agents to call
        """
        # If no LLM available, use conservative fallback routing
        if not self.llm and not self.llm_ephemeral:
            logger.warning("LLM not available, using conservative fallback routing")
            return {
                "agents_to_call": ["logs", "metrics", "traces"],
                "reasoning": "LLM unavailable — calling all agents for safety",
                "query_type": "correlation",
            }

        # Load routing prompt
        prompt_template = load_prompt("route_query.md")
        if not prompt_template:
            logger.warning("Routing prompt not found, using fallback")
            return self._fallback_routing(query)

        try:
            prompt = prompt_template.format(query=query)
            llm_client = get_llm() if self.llm_ephemeral else self.llm
            response = llm_client.invoke(prompt)
            response_text = extract_text_from_response(response)
            logger.info(f"LLM routing response (first 200 chars): {response_text[:200] if response_text else '<EMPTY>'}")

            # Clean response
            response_text = response_text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1] if len(lines) > 2 else lines[1:])
                response_text = response_text.strip()
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()

            # Extract JSON from response (in case LLM added preamble)
            # Find first { and last }
            first_brace = response_text.find("{")
            last_brace = response_text.rfind("}")

            if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
                response_text = response_text[first_brace:last_brace + 1]
                logger.info(f"Extracted JSON from response: {response_text[:100]}...")

            # Parse JSON response
            import json

            routing = json.loads(response_text)
            logger.info(f"LLM routing decision: {routing}")
            return routing

        except Exception as e:
            logger.warning(f"LLM routing failed: {e}, using fallback")
            return self._fallback_routing(query)

    def _fallback_routing(self, query: str) -> dict[str, Any]:
        """
        Fallback routing logic when LLM is not available

        Args:
            query: User query

        Returns:
            Routing decision
        """
        # Conservative fallback routing: call all agents
        return {
            "agents_to_call": ["logs", "metrics", "traces"],
            "reasoning": "Conservative fallback: call all agents when LLM unavailable or uncertain",
            "query_type": "correlation",
        }

    def _extract_context(self, query: str) -> dict[str, Any]:
        """
        Extract basic context from query (service names, focus)
        Keep simple - agents will do detailed analysis

        Args:
            query: User query

        Returns:
            Context dictionary with optional 'services' and 'focus'
        """
        context: dict[str, Any] = {}

        # Simple keyword detection for common services
        # Most architectures have these service names
        common_services = ["customer", "order", "stock", "payment", "notification", "ordermanagement", "suppliercheck"]
        found_services = [svc for svc in common_services if svc in query.lower()]
        if found_services:
            context["services"] = found_services

        # Simple focus detection
        if any(word in query.lower() for word in ["error", "erreur", "fail", "exception"]):
            context["focus"] = "errors"
        elif any(word in query.lower() for word in ["slow", "lent", "latency", "performance"]):
            context["focus"] = "performance"

        return context

    def _synthesize_responses(
        self,
        query: str,
        logs: dict | None,
        metrics: dict | None,
        traces: dict | None,
    ) -> dict[str, Any]:
        """
        Format agent responses into a coherent summary
        Agents already did the LLM analysis, just format their output

        Args:
            query: Original user query
            logs: Response from logs agent
            metrics: Response from metrics agent
            traces: Response from traces agent

        Returns:
            Formatted summary and recommendations
        """
        # Simple formatting - agents already did the analysis
        return self._basic_synthesis(query, logs, metrics, traces)

    def _basic_synthesis(
        self,
        query: str,
        logs: dict | None,
        metrics: dict | None,
        traces: dict | None,
    ) -> dict[str, Any]:
        """
        Format agent responses - agents already did LLM analysis

        Args:
            query: Original user query
            logs: Response from logs agent
            metrics: Response from metrics agent
            traces: Response from traces agent

        Returns:
            Formatted summary and recommendations from agents
        """
        from datetime import datetime

        summary_parts = []
        all_recommendations = []

        # Format logs response
        if logs and not isinstance(logs.get("error"), str):
            if "analysis" in logs:
                summary_parts.append(logs["analysis"])
            if "recommendations" in logs:
                all_recommendations.extend(logs["recommendations"])

        # Format metrics response
        if metrics and not isinstance(metrics.get("error"), str):
            if "analysis" in metrics:
                summary_parts.append(metrics["analysis"])
            if "recommendations" in metrics:
                all_recommendations.extend(metrics["recommendations"])

        # Format traces response
        if traces and not isinstance(traces.get("error"), str):
            if "analysis" in traces:
                summary_parts.append(traces["analysis"])
            if "recommendations" in traces:
                all_recommendations.extend(traces["recommendations"])

        # Combine summaries
        summary = "\n\n".join(summary_parts) if summary_parts else "No analysis available from agents"

        return {
            "summary": summary,
            "recommendations": all_recommendations if all_recommendations else ["Check agent connectivity"],
            "timestamp": datetime.now(),
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
