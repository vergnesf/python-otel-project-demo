"""
MCP (Model Context Protocol) client for Grafana
Provides unified interface to query Loki, Mimir, and Tempo via the Grafana MCP server
"""

import logging
import asyncio
from typing import Any
from datetime import datetime, timedelta
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.sse import sse_client

logger = logging.getLogger(__name__)


class MCPGrafanaClient:
    """
    Client for communicating with Grafana MCP Server via SSE

    The MCP server acts as a unified gateway to Loki (logs), Mimir (metrics), and Tempo (traces).
    Uses Model Context Protocol over SSE transport.
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
        self.loki_uid: str | None = None
        self.prometheus_uid: str | None = None
        self.tempo_uid: str | None = None
        self._session: ClientSession | None = None
        self._exit_stack: AsyncExitStack | None = None
        self._tools_cache: list[dict] | None = None
        self._initialized = False

    async def _ensure_session(self) -> ClientSession:
        """Ensure MCP session is initialized and connected"""
        if self._session and self._initialized:
            return self._session

        try:
            # Create exit stack to manage context
            self._exit_stack = AsyncExitStack()

            # Connect to MCP server via SSE
            logger.info(f"Connecting to MCP server at {self.base_url}/sse")
            read_stream, write_stream = await self._exit_stack.enter_async_context(
                sse_client(f"{self.base_url}/sse")
            )

            # Create MCP session
            self._session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            # Initialize the session
            await self._session.initialize()
            self._initialized = True

            logger.info("MCP session successfully initialized")

            # Fetch datasource UIDs
            await self._fetch_datasource_uids()

            return self._session

        except Exception as e:
            logger.error(f"Failed to establish MCP session: {e}")
            await self._cleanup()
            raise

    async def _cleanup(self):
        """Clean up session resources"""
        self._initialized = False
        self._session = None
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._exit_stack = None

    async def _list_tools(self) -> list[dict]:
        """List available MCP tools"""
        if self._tools_cache:
            return self._tools_cache

        session = await self._ensure_session()
        result = await session.list_tools()

        # Convert MCP Tool objects to dicts
        self._tools_cache = [
            {
                "name": tool.name,
                "description": tool.description if hasattr(tool, 'description') else "",
                "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else {}
            }
            for tool in result.tools
        ]

        logger.info(f"Available MCP tools: {[t['name'] for t in self._tools_cache]}")
        return self._tools_cache

    async def _fetch_datasource_uids(self):
        """Fetch datasource UIDs from Grafana via MCP"""
        try:
            if not self._session:
                return

            # Call list_datasources tool
            result = await self._session.call_tool("list_datasources", arguments={})

            # Parse response to extract UIDs
            if result.content:
                import json
                for content_item in result.content:
                    if hasattr(content_item, 'text'):
                        datasources = json.loads(content_item.text)

                        # Map datasources by type
                        for ds in datasources:
                            ds_type = ds.get("type", "")
                            ds_uid = ds.get("uid", "")
                            ds_name = ds.get("name", "")

                            if ds_type == "loki" and not self.loki_uid:
                                self.loki_uid = ds_uid
                                logger.info(f"Found Loki datasource: {ds_name} (uid: {ds_uid})")
                            elif ds_type == "prometheus" and not self.prometheus_uid:
                                self.prometheus_uid = ds_uid
                                logger.info(f"Found Prometheus/Mimir datasource: {ds_name} (uid: {ds_uid})")
                            elif ds_type == "tempo" and not self.tempo_uid:
                                self.tempo_uid = ds_uid
                                logger.info(f"Found Tempo datasource: {ds_name} (uid: {ds_uid})")

        except Exception as e:
            logger.warning(f"Failed to fetch datasource UIDs: {e}")

    async def close(self):
        """Close the MCP session"""
        await self._cleanup()

    def _parse_time_range(self, time_range: str) -> tuple[str, str]:
        """
        Parse time range string into start and end timestamps
        
        Args:
            time_range: Time range like '1h', '24h', '7d'
            
        Returns:
            Tuple of (start, end) in RFC3339 format (UTC) for MCP compatibility
        """
        from datetime import datetime, timedelta, timezone
        
        now = datetime.now(timezone.utc)
        
        # Parse time range
        if time_range.endswith('h'):
            hours = int(time_range[:-1])
            start = now - timedelta(hours=hours)
        elif time_range.endswith('d'):
            days = int(time_range[:-1])
            start = now - timedelta(days=days)
        elif time_range.endswith('m'):
            minutes = int(time_range[:-1])
            start = now - timedelta(minutes=minutes)
        else:
            # Default to 1 hour
            start = now - timedelta(hours=1)
        
        # Convert to RFC3339 format with timezone (e.g., 2025-11-08T16:09:20Z)
        # Use isoformat() and replace microseconds, then add Z suffix
        start_rfc = start.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        end_rfc = now.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        
        return start_rfc, end_rfc

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
            # Ensure session is initialized
            session = await self._ensure_session()
            await self._list_tools()

            start_rfc, end_rfc = self._parse_time_range(time_range)

            # Check if Loki datasource UID is available
            if not self.loki_uid:
                logger.error("Loki datasource UID not found")
                return {"error": "Loki datasource not configured", "logs": []}

            # Call MCP tool for Loki query with correct parameter names
            result = await session.call_tool(
                "query_loki_logs",
                arguments={
                    "datasourceUid": self.loki_uid,
                    "logql": query,
                    "startRfc3339": start_rfc,
                    "endRfc3339": end_rfc,
                    "limit": limit
                }
            )

            # Extract logs from MCP response
            if result.content:
                import json
                for content_item in result.content:
                    if hasattr(content_item, 'text'):
                        logs_data = json.loads(content_item.text)
                        # MCP peut retourner soit une liste directe, soit un dict
                        if isinstance(logs_data, list):
                            return {"logs": logs_data, "total": len(logs_data)}
                        elif isinstance(logs_data, dict):
                            return logs_data
                        else:
                            return {"logs": [], "total": 0}

            return {"logs": [], "total": 0}

        except Exception as e:
            logger.error(f"Failed to query logs via MCP: {e}")
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
            step: Step interval for range queries (e.g., '1m', '5m')

        Returns:
            Dictionary containing metric query results
        """
        try:
            # Ensure session is initialized
            session = await self._ensure_session()
            await self._list_tools()

            start_rfc, end_rfc = self._parse_time_range(time_range)

            # Check if Prometheus datasource UID is available
            if not self.prometheus_uid:
                logger.error("Prometheus/Mimir datasource UID not found")
                return {"error": "Prometheus datasource not configured"}

            # Parse step to seconds (e.g., "1m" -> 60)
            step_seconds = self._parse_step_to_seconds(step)

            # Call MCP tool with correct parameter names
            result = await session.call_tool(
                "query_prometheus",
                arguments={
                    "datasourceUid": self.prometheus_uid,
                    "expr": query,
                    "queryType": "range",
                    "startTime": start_rfc,
                    "endTime": end_rfc,
                    "stepSeconds": step_seconds
                }
            )

            # Extract metrics from MCP response
            if result.content:
                import json
                for content_item in result.content:
                    if hasattr(content_item, 'text'):
                        metrics_data = json.loads(content_item.text)
                        # MCP peut retourner soit une liste directe, soit un dict
                        if isinstance(metrics_data, list):
                            return {"metrics": metrics_data, "total": len(metrics_data)}
                        elif isinstance(metrics_data, dict):
                            return metrics_data
                        else:
                            return {"metrics": [], "total": 0}

            return {"metrics": [], "total": 0}

        except Exception as e:
            logger.error(f"Failed to query metrics via MCP: {e}")
            return {"error": str(e), "metrics": []}

    def _parse_step_to_seconds(self, step: str) -> int:
        """
        Parse step string to seconds
        
        Args:
            step: Step interval like '1m', '5m', '1h'
            
        Returns:
            Step in seconds
        """
        if step.endswith('s'):
            return int(step[:-1])
        elif step.endswith('m'):
            return int(step[:-1]) * 60
        elif step.endswith('h'):
            return int(step[:-1]) * 3600
        else:
            # Default to 60 seconds
            return 60

    async def query_traces(
        self,
        query: str,
        time_range: str = "1h",
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Query traces from Tempo via MCP
        
        Note: Tempo support in MCP Grafana requires proxied tools which may not
        be available. This method is prepared for future use or when proxied tools
        are enabled.

        Args:
            query: TraceQL query (e.g., '{service.name="order" && status=error}')
            time_range: Time range (e.g., '1h', '24h', '7d')
            limit: Maximum number of traces to return

        Returns:
            Dictionary containing trace query results or error if Tempo tools unavailable
        """
        try:
            # Ensure session is initialized
            session = await self._ensure_session()
            await self._list_tools()

            start_rfc, end_rfc = self._parse_time_range(time_range)

            # Check if Tempo datasource UID is available
            if not self.tempo_uid:
                logger.error("Tempo datasource UID not found")
                return {"error": "Tempo datasource not configured", "traces": []}

            # Try to use tempo_traceql-search tool (proxied tool)
            # This requires proxied tools to be enabled in MCP server
            result = await session.call_tool(
                "tempo_traceql-search",
                arguments={
                    "datasourceUid": self.tempo_uid,
                    "query": query,
                    "start": start_rfc,
                    "end": end_rfc,
                    "limit": limit
                }
            )

            # Extract traces from MCP response
            if result.content:
                import json
                for content_item in result.content:
                    if hasattr(content_item, 'text'):
                        traces_data = json.loads(content_item.text)
                        return traces_data

            return {"traces": [], "total": 0}

        except Exception as e:
            error_msg = str(e)
            # If tool not found, it means proxied tools are disabled
            if "tempo_traceql-search" in error_msg.lower() or "unknown tool" in error_msg.lower():
                logger.warning("Tempo proxied tools not available. Enable with MCP server flag.")
                return {
                    "error": "Tempo tools not available - proxied tools may be disabled in MCP server",
                    "traces": [],
                    "suggestion": "Remove --disable-proxied flag from MCP server or use direct Tempo API"
                }
            logger.error(f"Failed to query traces via MCP: {e}")
            return {"error": str(e), "traces": []}

    async def health_check(self) -> bool:
        """
        Check if MCP server is healthy

        Returns:
            True if server is healthy, False otherwise
        """
        try:
            # Try to establish session and list tools as health check
            await self._ensure_session()
            await self._list_tools()
            return True
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
