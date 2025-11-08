"""
MCP (Model Context Protocol) client for Grafana
Provides unified interface to query Loki, Mimir, and Tempo via the Grafana MCP server
"""

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class MCPGrafanaClient:
    """
    Client for communicating with Grafana MCP Server
    
    The MCP server acts as a unified gateway to Loki (logs), Mimir (metrics), and Tempo (traces).
    """

    def __init__(
        self,
        base_url: str = "http://grafana-mcp:8000",
        timeout: float = 30.0,
    ):
        """
        Initialize MCP Grafana client
        
        Args:
            base_url: Base URL of the MCP server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """Close the HTTP client"""
        await self._client.aclose()

    async def query_logs(
        self,
        query: str,
        time_range: str = "1h",
        limit: int = 100,
    ) -> dict[str, Any]:
        """
        Query logs from Loki via MCP
        
        Args:
            query: LogQL query (e.g., '{service_name="order"} |= "error"')
            time_range: Time range (e.g., '1h', '24h', '7d')
            limit: Maximum number of log lines to return
            
        Returns:
            Dictionary containing log query results
        """
        try:
            response = await self._client.post(
                f"{self.base_url}/api/logs/query",
                json={
                    "query": query,
                    "time_range": time_range,
                    "limit": limit,
                },
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to query logs: {e}")
            return {"error": str(e), "logs": []}

    async def query_metrics(
        self,
        query: str,
        time_range: str = "1h",
        step: str = "1m",
    ) -> dict[str, Any]:
        """
        Query metrics from Mimir via MCP
        
        Args:
            query: PromQL query (e.g., 'rate(http_requests_total[5m])')
            time_range: Time range (e.g., '1h', '24h', '7d')
            step: Step interval for range queries
            
        Returns:
            Dictionary containing metric query results
        """
        try:
            response = await self._client.post(
                f"{self.base_url}/api/metrics/query",
                json={
                    "query": query,
                    "time_range": time_range,
                    "step": step,
                },
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to query metrics: {e}")
            return {"error": str(e), "metrics": []}

    async def query_traces(
        self,
        query: str,
        time_range: str = "1h",
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Query traces from Tempo via MCP
        
        Args:
            query: TraceQL query (e.g., 'service.name="order" && status=error')
            time_range: Time range (e.g., '1h', '24h', '7d')
            limit: Maximum number of traces to return
            
        Returns:
            Dictionary containing trace query results
        """
        try:
            response = await self._client.post(
                f"{self.base_url}/api/traces/query",
                json={
                    "query": query,
                    "time_range": time_range,
                    "limit": limit,
                },
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to query traces: {e}")
            return {"error": str(e), "traces": []}

    async def health_check(self) -> bool:
        """
        Check if MCP server is healthy
        
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            response = await self._client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except httpx.HTTPError:
            return False
