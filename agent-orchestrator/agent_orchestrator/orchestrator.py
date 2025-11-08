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

from common_ai import get_llm

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

        # Initialize LLM for synthesis (optional, can be None if LLM not available)
        try:
            self.llm = get_llm()
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
        if self.llm:
            try:
                prompt = f"Translate the following user question to English. Return only the translated sentence (no explanations):\n\n{query}"
                response = self.llm.invoke(prompt)
                text = (
                    response.content if hasattr(response, "content") else str(response)
                )
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
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
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
        if not self.llm:
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
            response = self.llm.invoke(prompt)
            response_text = (
                response.content if hasattr(response, "content") else str(response)
            )

            # Clean response
            response_text = response_text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1] if len(lines) > 2 else lines[1:])
                response_text = response_text.strip()
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()

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

    def _understand_query_intent(self, query: str) -> str:
        """
        Understand the intent of the user query

        Args:
            query: User query

        Returns:
            Intent type: "greeting", "general", or "observability"
        """
        # Prefer LLM for intent detection when available
        if self.llm:
            try:
                prompt = (
                    "Determine the user's intent given the following query. "
                    "Return one word: 'greeting', 'observability', or 'general'.\n\nQuery: {query}"
                ).format(query=query)
                response = self.llm.invoke(prompt)
                text = (
                    response.content if hasattr(response, "content") else str(response)
                )
                text = text.strip().lower()
                for token in ("greeting", "observability", "general"):
                    if token in text:
                        return token
            except Exception:
                logger.debug(
                    "LLM intent detection failed, falling back to simple heuristics"
                )

        # Simple heuristic fallback: treat short salutations as greetings, otherwise assume observability/general by punctuation
        q = query.strip()
        if len(q.split()) <= 3 and any(
            w.lower() in q.lower() for w in ("hello", "hi", "bonjour", "salut", "hey")
        ):
            return "greeting"
        if "?" in q:
            return "general"
        return "observability"

    def _extract_context(self, query: str) -> dict[str, Any]:
        """
        Extract context from user query

        Args:
            query: User query

        Returns:
            Context dictionary
        """
        # Prefer LLM to extract structured context when available
        context: dict[str, Any] = {}
        if self.llm:
            try:
                prompt = (
                    "Extract a JSON object with possible keys 'services' (list of service names) "
                    "and 'focus' (e.g., 'errors', 'performance') from the user query. Return only JSON.\n\nQuery: {query}"
                ).format(query=query)
                response = self.llm.invoke(prompt)
                text = (
                    response.content if hasattr(response, "content") else str(response)
                )
                # Try to parse JSON
                import json

                text = text.strip()
                # Remove code fences if any
                if text.startswith("```"):
                    lines = text.splitlines()
                    if len(lines) > 2:
                        text = "\n".join(lines[1:-1])
                    else:
                        text = lines[1] if len(lines) > 1 else text
                context = json.loads(text)
                if not isinstance(context, dict):
                    context = {}
                return context
            except Exception:
                logger.debug(
                    "LLM context extraction failed, using conservative fallback"
                )

        # Conservative fallback: minimal context
        return {}

    def _synthesize_responses(
        self,
        query: str,
        logs: dict | None,
        metrics: dict | None,
        traces: dict | None,
    ) -> dict[str, Any]:
        """
        Synthesize responses from all agents into a coherent summary using LLM

        Args:
            query: Original user query
            logs: Response from logs agent
            metrics: Response from metrics agent
            traces: Response from traces agent

        Returns:
            Synthesized summary and recommendations
        """
        from datetime import datetime

        # If LLM is available, use it for intelligent synthesis
        if self.llm:
            try:
                return self._synthesize_with_llm(query, logs, metrics, traces)
            except Exception as e:
                logger.warning(
                    f"LLM synthesis failed, falling back to basic synthesis: {e}"
                )

        # Fallback to basic synthesis
        return self._basic_synthesis(query, logs, metrics, traces)

    def _synthesize_with_llm(
        self,
        query: str,
        logs: dict | None,
        metrics: dict | None,
        traces: dict | None,
    ) -> dict[str, Any]:
        """
        Use LLM to synthesize agent responses intelligently using prompt template

        Args:
            query: Original user query
            logs: Response from logs agent
            metrics: Response from metrics agent
            traces: Response from traces agent

        Returns:
            Synthesized summary and recommendations
        """
        from datetime import datetime

        # Extract data from agent responses
        # Prefer structured data if agent returned JSON data object
        if logs and isinstance(logs.get("data"), dict):
            logs_analysis = logs.get("data", {}).get(
                "summary", logs.get("analysis", "No logs analysis available")
            )
            logs_confidence = logs.get("confidence", 0)
            logs_total = logs.get("data", {}).get("total_logs", 0)
            logs_errors = logs.get("data", {}).get("error_count", 0)
        else:
            logs_analysis = (
                logs.get("analysis", "No logs analysis available")
                if logs
                else "Logs agent unavailable"
            )
            logs_confidence = logs.get("confidence", 0) if logs else 0
            logs_total = logs.get("data", {}).get("total_logs", 0) if logs else 0
            logs_errors = logs.get("data", {}).get("error_count", 0) if logs else 0

        if metrics and isinstance(metrics.get("data"), dict):
            metrics_analysis = metrics.get("data", {}).get(
                "summary", metrics.get("analysis", "No metrics analysis available")
            )
            metrics_confidence = metrics.get("confidence", 0)
            metrics_error_rate = (
                f"{metrics.get('data', {}).get('error_rate', 0)*100:.1f}%"
            )
            metrics_request_rate = (
                f"{metrics.get('data', {}).get('request_rate', 0):.1f}"
            )
            metrics_latency = f"{metrics.get('data', {}).get('latency_p95', 0)}ms"
        else:
            metrics_analysis = (
                metrics.get("analysis", "No metrics analysis available")
                if metrics
                else "Metrics agent unavailable"
            )
            metrics_confidence = metrics.get("confidence", 0) if metrics else 0
            metrics_error_rate = (
                f"{metrics.get('data', {}).get('error_rate', 0)*100:.1f}%"
                if metrics
                else "N/A"
            )
            metrics_request_rate = (
                f"{metrics.get('data', {}).get('request_rate', 0):.1f}"
                if metrics
                else "N/A"
            )
            metrics_latency = (
                f"{metrics.get('data', {}).get('latency_p95', 0)}ms"
                if metrics
                else "N/A"
            )

        traces_analysis = (
            traces.get("analysis", "No traces analysis available")
            if traces
            else "Traces agent unavailable"
        )
        traces_confidence = traces.get("confidence", 0) if traces else 0
        traces_total = traces.get("data", {}).get("total_traces", 0) if traces else 0
        traces_slow = traces.get("data", {}).get("slow_traces", 0) if traces else 0
        traces_failed = traces.get("data", {}).get("failed_traces", 0) if traces else 0

        # Load prompt template from markdown file
        prompt_template = load_prompt("synthesize_analysis.md")
        if not prompt_template:
            # Fallback to basic synthesis
            return self._basic_synthesis(query, logs, metrics, traces)

        # Replace variables in template
        try:
            prompt = prompt_template.format(
                query=query,
                logs_confidence=f"{logs_confidence:.0%}",
                logs_analysis=logs_analysis,
                logs_total=logs_total,
                logs_errors=logs_errors,
                metrics_confidence=f"{metrics_confidence:.0%}",
                metrics_analysis=metrics_analysis,
                metrics_error_rate=metrics_error_rate,
                metrics_request_rate=metrics_request_rate,
                metrics_latency=metrics_latency,
                traces_confidence=f"{traces_confidence:.0%}",
                traces_analysis=traces_analysis,
                traces_total=traces_total,
                traces_slow=traces_slow,
                traces_failed=traces_failed,
            )
        except KeyError as e:
            logger.error(f"Missing variable in synthesize_analysis.md template: {e}")
            return self._basic_synthesis(query, logs, metrics, traces)

        try:
            # Call LLM
            logger.info("Synthesizing agent responses with LLM...")
            response = self.llm.invoke(prompt)

            # Extract text from response
            if hasattr(response, "content"):
                summary = response.content
            else:
                summary = str(response)

            # Extract recommendations from the LLM response
            recommendations = []
            if "recommendations" in summary.lower() or "recommend" in summary.lower():
                # Parse recommendations from the LLM response
                lines = summary.split("\n")
                in_recommendations = False
                for line in lines:
                    if (
                        "recommendation" in line.lower()
                        or "immediate action" in line.lower()
                    ):
                        in_recommendations = True
                        continue
                    if in_recommendations and line.strip().startswith(("-", "*", "•")):
                        recommendations.append(line.strip().lstrip("-*•").strip())
                    elif (
                        in_recommendations
                        and line.strip()
                        and not line.strip().startswith("#")
                    ):
                        recommendations.append(line.strip())
                    elif in_recommendations and line.startswith("#"):
                        break

            # Add data-driven recommendations
            if metrics and metrics.get("data", {}).get("anomalies"):
                for anomaly in metrics["data"]["anomalies"]:
                    recommendations.append(
                        f"Address {anomaly['severity']} severity anomaly in {anomaly['metric']}"
                    )

            return {
                "summary": summary,
                "recommendations": (
                    recommendations
                    if recommendations
                    else [
                        "Monitor the situation closely",
                        "Review Grafana dashboards for additional context",
                    ]
                ),
                "timestamp": datetime.now(),
            }

        except Exception as e:
            logger.warning(f"LLM synthesis failed: {e}, using fallback")
            return self._basic_synthesis(query, logs, metrics, traces)

    def _basic_synthesis(
        self,
        query: str,
        logs: dict | None,
        metrics: dict | None,
        traces: dict | None,
    ) -> dict[str, Any]:
        """
        Basic synthesis without LLM (fallback)

        Args:
            query: Original user query
            logs: Response from logs agent
            metrics: Response from metrics agent
            traces: Response from traces agent

        Returns:
            Basic synthesized summary and recommendations
        """
        from datetime import datetime

        # Build summary from agent responses
        summary_parts = []
        recommendations = []

        if logs and "analysis" in logs:
            summary_parts.append(f"**Logs Analysis**: {logs['analysis']}")
            if "error" not in logs:
                recommendations.append("Review error logs for detailed stack traces")

        if metrics and "analysis" in metrics:
            summary_parts.append(f"**Metrics Analysis**: {metrics['analysis']}")
            if "error" not in metrics:
                recommendations.append("Monitor performance metrics trends")

        if traces and "analysis" in traces:
            summary_parts.append(f"**Traces Analysis**: {traces['analysis']}")
            if "error" not in traces:
                recommendations.append("Investigate slow spans in distributed traces")

        # Combine into final summary
        if summary_parts:
            summary = "\n\n".join(summary_parts)
        else:
            summary = "Unable to analyze the query. Please check agent connectivity."
            recommendations.append("Verify that all agents are running and healthy")

        # Add general recommendations
        recommendations.extend(
            [
                "Check ERROR_RATE environment variable if errors are simulated",
                "Review Grafana dashboards for additional insights",
            ]
        )

        return {
            "summary": summary,
            "recommendations": recommendations,
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
