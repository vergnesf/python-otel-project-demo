"""
Logs analysis logic using MCP Grafana client and LLM
NO business logic - just MCP data retrieval + LLM analysis
"""

import logging
import os
from datetime import datetime
import json
import re
from pathlib import Path
from typing import Any

from common_ai import MCPGrafanaClient, get_llm

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


class LogsAnalyzer:
    """
    Analyzer for log data from Loki via MCP with LLM-powered analysis
    """

    def __init__(self):
        """Initialize logs analyzer with MCP client and LLM"""
        self.mcp_url = os.getenv("MCP_GRAFANA_URL", "http://grafana-mcp:8000")
        self.mcp_client = MCPGrafanaClient(base_url=self.mcp_url)

        # Initialize LLM for intelligent analysis
        try:
            self.llm = get_llm()
            logger.info("LLM initialized for logs analysis")
        except Exception as e:
            logger.warning(f"LLM not available, using basic analysis: {e}")
            self.llm = None

    async def close(self):
        """Close MCP client"""
        if self.mcp_client:
            await self.mcp_client.close()

    async def analyze(
        self,
        query: str,
        time_range: str = "1h",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze logs based on user query using LLM and MCP Grafana

        Args:
            query: User query
            time_range: Time range for analysis
            context: Additional context (services, focus, etc.)

        Returns:
            Analysis results
        """
        context = context or {}
        # Ensure time_range is available in context for fallbacks and prompts
        context["time_range"] = time_range
        logger.info(f"Analyzing logs for query: {query}")

        # Use LLM to build better LogQL query if available
        if self.llm:
            logql_query = await self._build_logql_query_with_llm(query, context)
        else:
            logql_query = self._build_logql_query(query, context)

        logger.info(f"Generated LogQL: {logql_query}")

        # Query Loki via MCP
        logs_data = await self._query_loki(logql_query, time_range)

        # Analyze log data with LLM if available
        if self.llm and logs_data.get("logs"):
            analysis = await self._analyze_logs_with_llm(
                logs_data, query, context, time_range
            )
        else:
            analysis = self._analyze_logs(logs_data, query, context)

        return {
            "agent_name": "logs",
            "analysis": analysis["summary"],
            "data": analysis["data"],
            "confidence": analysis["confidence"],
            "grafana_links": self._generate_grafana_links(logql_query, time_range),
            "timestamp": datetime.now().isoformat(),
        }

    def _build_logql_query(self, query: str, context: dict[str, Any]) -> str:
        """
        Build LogQL query from user query and context

        Args:
            query: User query
            context: Context with services, focus, etc.

        Returns:
            LogQL query string
        """
        # Extract services from context
        services = context.get("services", [])

        # Base query
        if services:
            service_filter = "|".join(services)
            logql = f'{{service_name=~"{service_filter}"}}'
        else:
            logql = '{service_name=~".+"}'

        # Add error filter if needed
        query_lower = query.lower()
        if "error" in query_lower or "fail" in query_lower or "problem" in query_lower:
            logql += ' |= "error"'

        # Add specific patterns
        if "db" in query_lower or "database" in query_lower:
            logql += ' |~ "(?i)(db|database).*error"'

        return logql

    async def _query_loki(self, logql: str, time_range: str) -> dict[str, Any]:
        """
        Query Loki via MCP Grafana

        Args:
            logql: LogQL query
            time_range: Time range

        Returns:
            Logs data
        """
        logger.info(f"Querying Loki with: {logql}")

        # Query via MCP client
        result = await self.mcp_client.query_logs(
            query=logql, time_range=time_range, limit=100
        )

        # Return in expected format
        if "error" in result:
            logger.warning(f"Loki query error: {result['error']}")
            # Return mock data as fallback
            return {
                "logs": [],
                "total_count": 0,
            }

        return result

    def _analyze_logs(
        self,
        logs_data: dict[str, Any],
        query: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Analyze log data and generate insights

        Args:
            logs_data: Raw logs from Loki
            query: Original user query
            context: Request context

        Returns:
            Analysis with summary, data, and confidence
        """
        logs = logs_data.get("logs", [])
        total_count = logs_data.get("total_count", len(logs))

        # Count only ERROR / CRITICAL level logs (be conservative)
        error_types: dict[str, int] = {}
        affected_services: set[str] = set()
        error_count = 0

        for log in logs:
            message = log.get("message", "") or ""
            service = log.get("service_name", "unknown")
            level = (log.get("level") or log.get("severity") or "").upper()

            is_error = False
            if level in ("ERROR", "CRITICAL"):
                is_error = True
            elif re.search(r"\berror\b", message, re.IGNORECASE):
                is_error = True

            if is_error:
                error_count += 1
                error_types[message] = error_types.get(message, 0) + 1
                affected_services.add(service)

        # Build error types list sorted by count
        error_types_list = [
            {"type": error_type, "count": count}
            for error_type, count in sorted(
                error_types.items(), key=lambda x: x[1], reverse=True
            )
        ]

        time_range_checked = context.get("time_range", "1h")
        summary_parts = [
            f"Found {error_count} error logs in the last {time_range_checked}."
        ]

        if error_types_list:
            primary_error = error_types_list[0]
            summary_parts.append(
                f"Primary error: '{primary_error['type']}' ({primary_error['count']} occurrences)."
            )

        if any("Simulated DB" in k for k in error_types):
            summary_parts.append(
                "Note: These appear to be simulated errors (ERROR_RATE environment variable)."
            )

        summary_parts.append(
            f"Affected services: {', '.join(sorted(affected_services))}."
        )

        return {
            "summary": " ".join(summary_parts),
            "data": {
                "total_logs": total_count,
                "error_count": error_count,
                "error_types": error_types_list,
                "affected_services": list(affected_services),
                "sample_logs": logs[:5],
                "time_range_checked": time_range_checked,
            },
            "confidence": 0.9 if error_count > 0 else 0.3,
        }

    def _generate_grafana_links(self, logql: str, time_range: str) -> list[str]:
        """
        Generate Grafana Explore links

        Args:
            logql: LogQL query
            time_range: Time range

        Returns:
            List of Grafana URLs
        """
        # TODO: Generate actual Grafana Explore URLs
        base_url = "http://grafana:3000/explore"
        return [f"{base_url}?query={logql}&range={time_range}"]

    async def _build_logql_query_with_llm(
        self, query: str, context: dict[str, Any]
    ) -> str:
        """
        Use LLM to build an optimized LogQL query from prompt template

        Args:
            query: User query
            context: Request context

        Returns:
            LogQL query string
        """
        services = context.get("services", [])
        services_context = (
            f"Available services: {', '.join(services)}"
            if services
            else "No specific services mentioned"
        )

        # Load prompt template from markdown file
        prompt_template = load_prompt("build_logql.md")
        if not prompt_template:
            # Fallback to simple query building
            return self._build_logql_query(query, context)

        # Replace variables in template
        try:
            prompt = prompt_template.format(
                query=query, services_context=services_context
            )
        except KeyError as e:
            logger.error(f"Missing variable in build_logql.md template: {e}")
            return self._build_logql_query(query, context)

        try:
            response = self.llm.invoke(prompt)
            logql = response.content if hasattr(response, "content") else str(response)
            logql = logql.strip().strip("`").strip()
            # Remove markdown code block markers if present
            if logql.startswith("```"):
                lines = logql.split("\n")
                logql = "\n".join(lines[1:-1] if len(lines) > 2 else lines[1:])
                logql = logql.strip()
            logger.info(f"LLM generated LogQL: {logql}")

            # If LLM returned empty string, use fallback
            if not logql:
                logger.warning("LLM generated empty LogQL, using fallback")
                return self._build_logql_query(query, context)

            return logql
        except Exception as e:
            logger.warning(f"LLM query generation failed: {e}, using fallback")
            return self._build_logql_query(query, context)

    async def _analyze_logs_with_llm(
        self,
        logs_data: dict[str, Any],
        query: str,
        context: dict[str, Any],
        time_range: str,
    ) -> dict[str, Any]:
        """
        Use LLM to analyze log data - NO calculations, just LLM analysis

        Args:
            logs_data: Raw logs from Loki (via MCP)
            query: Original user query
            context: Request context
            time_range: Time range

        Returns:
            Analysis with summary and raw data from MCP
        """
        logs = logs_data.get("logs", [])
        total_logs = logs_data.get("total_count", len(logs))

        # Prepare log samples for LLM (limit to avoid token/window overflow)
        # Start with a modest number of samples and shrink if the final prompt
        # is still too large for the model context.
        max_samples_initial = 5
        log_samples_text = []
        for log in logs[:max_samples_initial]:
            timestamp = log.get("timestamp", "")
            service = log.get("service_name", "unknown")
            message = log.get("message", "")[:200]
            log_samples_text.append(f"- [{timestamp}] [{service}] {message}")

        services = context.get("services", [])
        services_str = ", ".join(services) if services else "All services"

        # Load prompt template from markdown file
        prompt_template = load_prompt("analyze_logs.md")
        if not prompt_template:
            # Fallback
            return self._analyze_logs(logs_data, query, context)

        # Replace variables in template
        try:
            prompt = prompt_template.format(
                query=query,
                time_range=time_range,
                services=services_str,
                total_logs=total_logs,
                log_samples=(
                    "\n".join(log_samples_text) if log_samples_text else "No logs found"
                ),
            )
        except KeyError as e:
            logger.error(f"Missing variable in analyze_logs.md template: {e}")
            return self._analyze_logs(logs_data, query, context)

        try:
            # Guard against sending a prompt that is too large for the LLM
            # Use environment var LLM_MAX_PROMPT_CHARS to control maximum allowed prompt size
            max_prompt_chars = int(os.getenv("LLM_MAX_PROMPT_CHARS", "9000"))

            def build_prompt(samples):
                return prompt_template.format(
                    query=query,
                    time_range=time_range,
                    services=services_str,
                    total_logs=total_logs,
                    log_samples=("\n".join(samples) if samples else "No logs found"),
                )

            prompt = build_prompt(log_samples_text)

            # Iteratively reduce samples until prompt fits within allowed size
            while len(prompt) > max_prompt_chars and len(log_samples_text) > 0:
                # reduce samples aggressively (halve)
                new_count = max(1, len(log_samples_text) // 2)
                log_samples_text = log_samples_text[:new_count]
                prompt = build_prompt(log_samples_text)

            # If still too large, replace samples with a short summary placeholder
            if len(prompt) > max_prompt_chars:
                summary_placeholder = "(truncated logs: too many characters to include samples; please rerun with narrower time range)"
                prompt = prompt_template.format(
                    query=query,
                    time_range=time_range,
                    services=services_str,
                    total_logs=total_logs,
                    log_samples=summary_placeholder,
                )

            response = self.llm.invoke(prompt)
            llm_analysis = (
                response.content if hasattr(response, "content") else str(response)
            )
            logger.info("LLM logs analysis complete")

            # Try to extract JSON object from LLM response
            text = llm_analysis.strip()
            json_text = None
            m = re.search(r"(\{.*\})", text, re.DOTALL)
            if m:
                json_text = m.group(1)

            if json_text:
                try:
                    parsed = json.loads(json_text)
                    # Map parsed JSON to expected structure
                    error_count = parsed.get("error_count", total_logs)
                    summary = parsed.get("summary", "")
                    logger.info("Parsed JSON from LLM logs analysis")
                    return {
                        "summary": summary,
                        "data": parsed,
                        "confidence": 0.95 if error_count > 0 else 0.3,
                    }
                except Exception:
                    logger.warning(
                        "Failed to parse JSON from LLM response, falling back"
                    )

            # If logs empty and user asked for short window, return structured fallback
            if total_logs == 0 and (
                "5m" in time_range or "5" in time_range or "5 minutes" in prompt.lower()
            ):
                return {
                    "summary": f"Found 0 error logs in the last {time_range}.",
                    "data": {
                        "total_logs": 0,
                        "error_count": 0,
                        "affected_services": [],
                        "top_error_patterns": [],
                        "time_range_checked": time_range,
                    },
                    "confidence": 0.3,
                }

            # Fallback to local analyzer
            return self._analyze_logs(logs_data, query, context)

        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}, using fallback")
            return self._analyze_logs(logs_data, query, context)

    async def check_mcp_health(self) -> bool:
        """
        Check if MCP Grafana server is reachable

        Returns:
            True if healthy, False otherwise
        """
        return await self.mcp_client.health_check()
