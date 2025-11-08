"""
Metrics analysis logic using MCP Grafana client
"""

import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class MetricsAnalyzer:
    """
    Analyzer for metrics data from Mimir via MCP
    """

    def __init__(self):
        """Initialize metrics analyzer with MCP client"""
        self.mcp_url = os.getenv("MCP_GRAFANA_URL", "http://grafana-mcp:8000")
        
        # Import MCP client (will be available from agents-common)
        # For now, we'll use a mock implementation
        self.mcp_client = None

    async def close(self):
        """Close MCP client"""
        if self.mcp_client:
            await self.mcp_client.close()

    async def analyze(
        self,
        query: str,
        time_range: str = "1h",
        context: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """
        Analyze metrics based on user query
        
        Args:
            query: User query
            time_range: Time range for analysis
            context: Additional context (services, focus, etc.)
            
        Returns:
            Analysis results
        """
        context = context or {}
        logger.info(f"Analyzing metrics for query: {query}")
        
        # Build PromQL queries
        promql_queries = self._build_promql_queries(query, context)
        logger.info(f"Generated PromQL queries: {len(promql_queries)}")
        
        # Query Mimir via MCP (mock for now)
        metrics_data = await self._query_mimir(promql_queries, time_range)
        
        # Analyze metrics data
        analysis = self._analyze_metrics(metrics_data, query, context)
        
        return {
            "agent_name": "metrics",
            "analysis": analysis["summary"],
            "data": analysis["data"],
            "confidence": analysis["confidence"],
            "grafana_links": self._generate_grafana_links(promql_queries[0] if promql_queries else "", time_range),
            "timestamp": datetime.now().isoformat(),
        }

    def _build_promql_queries(self, query: str, context: dict[str, Any]) -> list[str]:
        """
        Build PromQL queries from user query and context
        
        Args:
            query: User query
            context: Context with services, focus, etc.
            
        Returns:
            List of PromQL query strings
        """
        queries = []
        services = context.get("services", [])
        query_lower = query.lower()
        
        # Build service filter
        if services:
            service_filter = f'service=~"{"|".join(services)}"'
        else:
            service_filter = 'service=~".+"'
        
        # Error rate query
        if "error" in query_lower or "fail" in query_lower:
            queries.append(
                f'rate(http_requests_total{{status=~"5..", {service_filter}}}[5m])'
            )
        
        # Latency query
        if "slow" in query_lower or "latency" in query_lower or "performance" in query_lower:
            queries.append(
                f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{{service_filter}}}[5m]))'
            )
        
        # Request rate query
        if "request" in query_lower or "traffic" in query_lower:
            queries.append(
                f'sum(rate(http_requests_total{{{service_filter}}}[5m]))'
            )
        
        # CPU usage query
        if "cpu" in query_lower or "resource" in query_lower:
            queries.append(
                f'avg(rate(process_cpu_seconds_total{{{service_filter}}}[5m])) * 100'
            )
        
        # Memory usage query
        if "memory" in query_lower or "resource" in query_lower:
            queries.append(
                f'process_resident_memory_bytes{{{service_filter}}} / 1024 / 1024'
            )
        
        # Default: error rate and request rate
        if not queries:
            queries.extend([
                f'rate(http_requests_total{{status=~"5..", {service_filter}}}[5m])',
                f'sum(rate(http_requests_total{{{service_filter}}}[5m]))',
            ])
        
        return queries

    async def _query_mimir(self, promql_queries: list[str], time_range: str) -> dict[str, Any]:
        """
        Query Mimir via MCP Grafana
        
        Args:
            promql_queries: List of PromQL queries
            time_range: Time range
            
        Returns:
            Metrics data
        """
        # TODO: Use actual MCP client when available
        # For now, return mock data
        logger.info(f"Querying Mimir with {len(promql_queries)} queries")
        
        return {
            "error_rate": 0.102,  # 10.2% error rate
            "request_rate": 125.5,  # 125.5 req/s
            "latency_p95": 245,  # 245ms
            "cpu_usage": 35.2,  # 35.2%
            "memory_mb": 512,  # 512 MB
        }

    def _analyze_metrics(
        self,
        metrics_data: dict[str, Any],
        query: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Analyze metrics data and generate insights
        
        Args:
            metrics_data: Raw metrics from Mimir
            query: Original user query
            context: Request context
            
        Returns:
            Analysis with summary, data, and confidence
        """
        error_rate = metrics_data.get("error_rate", 0)
        request_rate = metrics_data.get("request_rate", 0)
        latency_p95 = metrics_data.get("latency_p95", 0)
        cpu_usage = metrics_data.get("cpu_usage", 0)
        memory_mb = metrics_data.get("memory_mb", 0)
        
        # Detect anomalies
        anomalies = []
        if error_rate > 0.05:  # > 5% error rate
            anomalies.append({
                "metric": "error_rate",
                "value": error_rate,
                "threshold": 0.05,
                "severity": "high" if error_rate > 0.1 else "medium",
            })
        
        if latency_p95 > 200:  # > 200ms p95 latency
            anomalies.append({
                "metric": "latency_p95",
                "value": latency_p95,
                "threshold": 200,
                "severity": "medium",
            })
        
        if cpu_usage > 80:  # > 80% CPU
            anomalies.append({
                "metric": "cpu_usage",
                "value": cpu_usage,
                "threshold": 80,
                "severity": "high",
            })
        
        # Build summary
        summary_parts = []
        
        services = context.get("services", ["services"])
        service_name = services[0] if services else "services"
        
        if error_rate > 0:
            summary_parts.append(
                f"{service_name} shows {error_rate*100:.1f}% HTTP 500 error rate "
                f"(expected: <1%). This indicates reliability issues."
            )
        
        if latency_p95 > 0:
            summary_parts.append(
                f"Request latency p95: {latency_p95}ms "
                f"({'above' if latency_p95 > 200 else 'within'} baseline of 200ms)."
            )
        
        if request_rate > 0:
            summary_parts.append(
                f"Current request rate: {request_rate:.1f} req/s."
            )
        
        if anomalies:
            summary_parts.append(
                f"Detected {len(anomalies)} anomal{'ies' if len(anomalies) > 1 else 'y'} requiring attention."
            )
        else:
            summary_parts.append("No significant anomalies detected.")
        
        return {
            "summary": " ".join(summary_parts),
            "data": {
                "error_rate": error_rate,
                "request_rate": request_rate,
                "latency_p95": latency_p95,
                "cpu_usage": cpu_usage,
                "memory_mb": memory_mb,
                "anomalies": anomalies,
            },
            "confidence": 0.85 if anomalies else 0.7,
        }

    def _generate_grafana_links(self, promql: str, time_range: str) -> list[str]:
        """
        Generate Grafana Explore links
        
        Args:
            promql: PromQL query
            time_range: Time range
            
        Returns:
            List of Grafana URLs
        """
        # TODO: Generate actual Grafana Explore URLs
        base_url = "http://grafana:3000/explore"
        return [f"{base_url}?query={promql}&range={time_range}"]

    async def check_mcp_health(self) -> bool:
        """
        Check if MCP Grafana server is reachable
        
        Returns:
            True if healthy, False otherwise
        """
        # TODO: Implement actual health check
        return True
