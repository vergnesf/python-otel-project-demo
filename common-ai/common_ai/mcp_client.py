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
            # Verify the session is still alive with a lightweight ping
            try:
                await asyncio.wait_for(self._session.list_tools(), timeout=5.0)
                return self._session
            except Exception:
                logger.warning("MCP session appears dead, reconnecting...")
                await self._cleanup()

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
        self._tools_cache = None
        self.loki_uid = None
        self.prometheus_uid = None
        self.tempo_uid = None
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
                "description": tool.description if hasattr(tool, "description") else "",
                "inputSchema": tool.inputSchema if hasattr(tool, "inputSchema") else {},
            }
            for tool in result.tools
        ]

        logger.debug(f"Available MCP tools: {[t['name'] for t in self._tools_cache]}")
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
                    if hasattr(content_item, "text"):
                        datasources = json.loads(content_item.text)

                        # Map datasources by type
                        for ds in datasources:
                            ds_type = ds.get("type", "")
                            ds_uid = ds.get("uid", "")
                            ds_name = ds.get("name", "")

                            if ds_type == "loki" and not self.loki_uid:
                                self.loki_uid = ds_uid
                                logger.info(
                                    f"Found Loki datasource: {ds_name} (uid: {ds_uid})"
                                )
                            elif ds_type == "prometheus" and not self.prometheus_uid:
                                self.prometheus_uid = ds_uid
                                logger.info(
                                    f"Found Prometheus/Mimir datasource: {ds_name} (uid: {ds_uid})"
                                )
                            elif ds_type == "tempo" and not self.tempo_uid:
                                self.tempo_uid = ds_uid
                                logger.info(
                                    f"Found Tempo datasource: {ds_name} (uid: {ds_uid})"
                                )

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
        if time_range.endswith("h"):
            hours = int(time_range[:-1])
            start = now - timedelta(hours=hours)
        elif time_range.endswith("d"):
            days = int(time_range[:-1])
            start = now - timedelta(days=days)
        elif time_range.endswith("m"):
            minutes = int(time_range[:-1])
            start = now - timedelta(minutes=minutes)
        else:
            # Default to 1 hour
            start = now - timedelta(hours=1)

        # Convert to RFC3339 format with timezone (e.g., 2025-11-08T16:09:20Z)
        # Use isoformat() and replace microseconds, then add Z suffix
        start_rfc = start.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        end_rfc = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")

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
                    "limit": limit,
                },
            )

            # Extract logs from MCP response
            if result.content:
                import json

                for content_item in result.content:
                    if hasattr(content_item, "text"):
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
                    "stepSeconds": step_seconds,
                },
            )

            # Extract metrics from MCP response
            if result.content:
                import json

                for content_item in result.content:
                    if hasattr(content_item, "text"):
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
        if step.endswith("s"):
            return int(step[:-1])
        elif step.endswith("m"):
            return int(step[:-1]) * 60
        elif step.endswith("h"):
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
                    "limit": limit,
                },
            )

            # Extract traces from MCP response
            if result.content:
                import json

                for content_item in result.content:
                    if hasattr(content_item, "text"):
                        traces_data = json.loads(content_item.text)
                        return traces_data

            return {"traces": [], "total": 0}

        except Exception as e:
            error_msg = str(e)
            # If tool not found, it means proxied tools are disabled
            if (
                "tempo_traceql-search" in error_msg.lower()
                or "unknown tool" in error_msg.lower()
            ):
                logger.warning(
                    "Tempo proxied tools not available. Enable with MCP server flag."
                )
                return {
                    "error": "Tempo tools not available - proxied tools may be disabled in MCP server",
                    "traces": [],
                    "suggestion": "Remove --disable-proxied flag from MCP server or use direct Tempo API",
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

    def _parse_mcp_result(self, result: Any) -> Any:
        """
        Parse MCP tool call result

        Args:
            result: MCP CallToolResult

        Returns:
            Parsed JSON data or empty dict/list
        """
        import json

        if result.content:
            for content_item in result.content:
                if hasattr(content_item, "text"):
                    try:
                        return json.loads(content_item.text)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse MCP result: {e}")
                        return content_item.text
        return {}

    # =====================
    # LOKI ADVANCED METHODS
    # =====================

    async def list_loki_label_names(self) -> list[str]:
        """
        List all available label names in Loki

        Returns:
            List of label names (e.g., ['service_name', 'level', 'host'])
        """
        try:
            session = await self._ensure_session()

            if not self.loki_uid:
                logger.error("Loki datasource UID not found")
                return []

            result = await session.call_tool(
                "list_loki_label_names",
                arguments={"datasourceUid": self.loki_uid},
            )

            data = self._parse_mcp_result(result)
            # MCP can return a list directly or a dict with 'data' key
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "data" in data:
                return data["data"]
            return []

        except Exception as e:
            logger.error(f"Failed to list Loki label names: {e}")
            return []

    async def list_loki_label_values(self, label_name: str) -> list[str]:
        """
        List all values for a specific Loki label

        Args:
            label_name: Label name (e.g., 'service_name', 'level')

        Returns:
            List of label values (e.g., ['order', 'stock', 'customer'])
        """
        try:
            session = await self._ensure_session()

            if not self.loki_uid:
                logger.error("Loki datasource UID not found")
                return []

            result = await session.call_tool(
                "list_loki_label_values",
                arguments={
                    "datasourceUid": self.loki_uid,
                    "labelName": label_name,
                },
            )

            data = self._parse_mcp_result(result)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "data" in data:
                return data["data"]
            return []

        except Exception as e:
            logger.error(f"Failed to list Loki label values for '{label_name}': {e}")
            return []

    async def query_loki_stats(
        self,
        query: str,
        time_range: str = "1h",
    ) -> dict[str, Any]:
        """
        Query Loki statistics (volumes, streams, bytes)

        Args:
            query: LogQL query (e.g., '{service_name="order"}')
            time_range: Time range (e.g., '1h', '24h', '7d')

        Returns:
            Dictionary with stats (streams, entries, bytes, etc.)
        """
        try:
            session = await self._ensure_session()

            if not self.loki_uid:
                logger.error("Loki datasource UID not found")
                return {"error": "Loki datasource not configured"}

            start_rfc, end_rfc = self._parse_time_range(time_range)

            result = await session.call_tool(
                "query_loki_stats",
                arguments={
                    "datasourceUid": self.loki_uid,
                    "logql": query,
                    "startRfc3339": start_rfc,
                    "endRfc3339": end_rfc,
                },
            )

            return self._parse_mcp_result(result)

        except Exception as e:
            logger.error(f"Failed to query Loki stats: {e}")
            return {"error": str(e)}

    # =====================
    # PROMETHEUS ADVANCED METHODS
    # =====================

    async def list_prometheus_metric_names(self) -> list[str]:
        """
        List all available metric names in Prometheus/Mimir

        Returns:
            List of metric names (e.g., ['http_requests_total', 'cpu_usage'])
        """
        try:
            session = await self._ensure_session()

            if not self.prometheus_uid:
                logger.error("Prometheus datasource UID not found")
                return []

            result = await session.call_tool(
                "list_prometheus_metric_names",
                arguments={"datasourceUid": self.prometheus_uid},
            )

            data = self._parse_mcp_result(result)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "data" in data:
                return data["data"]
            return []

        except Exception as e:
            logger.error(f"Failed to list Prometheus metric names: {e}")
            return []

    async def list_prometheus_metric_metadata(
        self, metric: str | None = None
    ) -> dict[str, Any]:
        """
        Get metadata for Prometheus metrics (type, help, unit)

        Args:
            metric: Optional metric name to get metadata for. If None, returns all metrics metadata

        Returns:
            Dictionary with metric metadata
        """
        try:
            session = await self._ensure_session()

            if not self.prometheus_uid:
                logger.error("Prometheus datasource UID not found")
                return {}

            arguments = {"datasourceUid": self.prometheus_uid}
            if metric:
                arguments["metric"] = metric

            result = await session.call_tool(
                "list_prometheus_metric_metadata", arguments=arguments
            )

            return self._parse_mcp_result(result)

        except Exception as e:
            logger.error(f"Failed to get Prometheus metric metadata: {e}")
            return {}

    async def list_prometheus_label_names(self) -> list[str]:
        """
        List all available label names in Prometheus/Mimir

        Returns:
            List of label names (e.g., ['job', 'instance', 'service'])
        """
        try:
            session = await self._ensure_session()

            if not self.prometheus_uid:
                logger.error("Prometheus datasource UID not found")
                return []

            result = await session.call_tool(
                "list_prometheus_label_names",
                arguments={"datasourceUid": self.prometheus_uid},
            )

            data = self._parse_mcp_result(result)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "data" in data:
                return data["data"]
            return []

        except Exception as e:
            logger.error(f"Failed to list Prometheus label names: {e}")
            return []

    async def list_prometheus_label_values(
        self, label_name: str, metric: str | None = None
    ) -> list[str]:
        """
        List all values for a specific Prometheus label

        Args:
            label_name: Label name (e.g., 'job', 'instance')
            metric: Optional metric name to filter by

        Returns:
            List of label values
        """
        try:
            session = await self._ensure_session()

            if not self.prometheus_uid:
                logger.error("Prometheus datasource UID not found")
                return []

            arguments = {
                "datasourceUid": self.prometheus_uid,
                "labelName": label_name,
            }
            if metric:
                arguments["metric"] = metric

            result = await session.call_tool(
                "list_prometheus_label_values", arguments=arguments
            )

            data = self._parse_mcp_result(result)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "data" in data:
                return data["data"]
            return []

        except Exception as e:
            logger.error(
                f"Failed to list Prometheus label values for '{label_name}': {e}"
            )
            return []

    async def list_alert_rules(self) -> list[dict[str, Any]]:
        """
        List all alert rules configured in Grafana

        Returns:
            List of alert rule dictionaries with details (name, state, labels, etc.)
        """
        try:
            session = await self._ensure_session()

            result = await session.call_tool("list_alert_rules", arguments={})

            data = self._parse_mcp_result(result)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "data" in data:
                return data["data"]
            return []

        except Exception as e:
            logger.error(f"Failed to list alert rules: {e}")
            return []

    async def get_alert_rule_by_uid(self, uid: str) -> dict[str, Any]:
        """
        Get a specific alert rule by UID

        Args:
            uid: Alert rule UID

        Returns:
            Alert rule details
        """
        try:
            session = await self._ensure_session()

            result = await session.call_tool(
                "get_alert_rule_by_uid", arguments={"uid": uid}
            )

            return self._parse_mcp_result(result)

        except Exception as e:
            logger.error(f"Failed to get alert rule {uid}: {e}")
            return {}

    # =====================
    # ANNOTATIONS METHODS
    # =====================

    async def get_annotations(
        self,
        time_range: str = "1h",
        tags: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get annotations from Grafana

        Args:
            time_range: Time range (e.g., '1h', '24h', '7d')
            tags: Optional list of tags to filter by
            limit: Maximum number of annotations to return

        Returns:
            List of annotation dictionaries
        """
        try:
            session = await self._ensure_session()

            start_rfc, end_rfc = self._parse_time_range(time_range)

            # Convert RFC3339 to milliseconds timestamp
            from datetime import datetime

            start_ms = int(
                datetime.fromisoformat(start_rfc.replace("Z", "+00:00")).timestamp()
                * 1000
            )
            end_ms = int(
                datetime.fromisoformat(end_rfc.replace("Z", "+00:00")).timestamp()
                * 1000
            )

            arguments = {
                "from": start_ms,
                "to": end_ms,
                "limit": limit,
            }
            if tags:
                arguments["tags"] = tags

            result = await session.call_tool("get_annotations", arguments=arguments)

            data = self._parse_mcp_result(result)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "data" in data:
                return data["data"]
            return []

        except Exception as e:
            logger.error(f"Failed to get annotations: {e}")
            return []

    async def create_annotation(
        self,
        text: str,
        tags: list[str] | None = None,
        time: int | None = None,
    ) -> dict[str, Any]:
        """
        Create an annotation in Grafana

        Args:
            text: Annotation text
            tags: Optional list of tags
            time: Optional timestamp in milliseconds. If None, uses current time

        Returns:
            Created annotation details
        """
        try:
            session = await self._ensure_session()

            if time is None:
                time = int(datetime.now().timestamp() * 1000)

            arguments = {
                "text": text,
                "time": time,
            }
            if tags:
                arguments["tags"] = tags

            result = await session.call_tool("create_annotation", arguments=arguments)

            return self._parse_mcp_result(result)

        except Exception as e:
            logger.error(f"Failed to create annotation: {e}")
            return {"error": str(e)}

    async def update_annotation(
        self,
        annotation_id: int,
        text: str | None = None,
        tags: list[str] | None = None,
        time: int | None = None,
        time_end: int | None = None,
    ) -> dict[str, Any]:
        """
        Update an existing annotation

        Args:
            annotation_id: Annotation ID
            text: Optional new text
            tags: Optional new tags
            time: Optional new start time in milliseconds
            time_end: Optional end time in milliseconds (for range annotations)

        Returns:
            Updated annotation details
        """
        try:
            session = await self._ensure_session()

            arguments = {"id": annotation_id}
            if text is not None:
                arguments["text"] = text
            if tags is not None:
                arguments["tags"] = tags
            if time is not None:
                arguments["time"] = time
            if time_end is not None:
                arguments["timeEnd"] = time_end

            result = await session.call_tool("update_annotation", arguments=arguments)

            return self._parse_mcp_result(result)

        except Exception as e:
            logger.error(f"Failed to update annotation {annotation_id}: {e}")
            return {"error": str(e)}

    async def get_annotation_tags(self) -> list[str]:
        """
        Get all annotation tags

        Returns:
            List of annotation tags
        """
        try:
            session = await self._ensure_session()

            result = await session.call_tool("get_annotation_tags", arguments={})

            data = self._parse_mcp_result(result)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Extract tags from result structure
                tags = data.get("tags", []) or data.get("result", [])
                return tags
            return []

        except Exception as e:
            logger.error(f"Failed to get annotation tags: {e}")
            return []
