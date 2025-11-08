"""
Logs analysis logic using MCP Grafana client
"""

import logging
import os
from datetime import datetime
from typing import Any

from common_ai import MCPGrafanaClient

logger = logging.getLogger(__name__)


class LogsAnalyzer:
    """
    Analyzer for log data from Loki via MCP
    """

    def __init__(self):
        """Initialize logs analyzer with MCP client"""
        self.mcp_url = os.getenv("MCP_GRAFANA_URL", "http://grafana-mcp:8000")
        self.mcp_client = MCPGrafanaClient(base_url=self.mcp_url)

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
        Analyze logs based on user query

        Args:
            query: User query
            time_range: Time range for analysis
            context: Additional context (services, focus, etc.)

        Returns:
            Analysis results
        """
        context = context or {}
        logger.info(f"Analyzing logs for query: {query}")

        # Build LogQL query
        logql_query = self._build_logql_query(query, context)
        logger.info(f"Generated LogQL: {logql_query}")

        # Query Loki via MCP (mock for now)
        logs_data = await self._query_loki(logql_query, time_range)

        # Analyze log data
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
            logql = '{job=~".+"}'

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

        # Count errors by type
        error_types = {}
        affected_services = set()

        for log in logs:
            error_msg = log.get("message", "")
            service = log.get("service_name", "unknown")

            # Group by error type
            if error_msg in error_types:
                error_types[error_msg] += 1
            else:
                error_types[error_msg] = 1

            affected_services.add(service)

        # Build summary
        error_types_list = [
            {"type": error_type, "count": count}
            for error_type, count in sorted(
                error_types.items(), key=lambda x: x[1], reverse=True
            )
        ]

        summary_parts = [
            f"Found {total_count} error logs in the last {context.get('time_range', '1h')}."
        ]

        if error_types_list:
            primary_error = error_types_list[0]
            summary_parts.append(
                f"Primary error: '{primary_error['type']}' ({primary_error['count']} occurrences)."
            )

        if "Simulated DB" in str(error_types):
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
                "error_count": total_count,
                "error_types": error_types_list,
                "affected_services": list(affected_services),
                "sample_logs": logs[:5],  # First 5 logs as samples
            },
            "confidence": 0.9 if total_count > 0 else 0.3,
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

    async def check_mcp_health(self) -> bool:
        """
        Check if MCP Grafana server is reachable

        Returns:
            True if healthy, False otherwise
        """
        return await self.mcp_client.health_check()
