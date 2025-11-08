# pyright: reportMissingImports=false
"""
Traces analysis logic using MCP Grafana client and LLM
NO business logic - just MCP data retrieval + LLM analysis
"""

import logging
import os
from datetime import datetime
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


class TracesAnalyzer:
    """
    Analyzer for distributed traces from Tempo via MCP with LLM-powered analysis
    """

    def __init__(self):
        """Initialize traces analyzer with MCP client and LLM"""
        self.mcp_url = os.getenv("MCP_GRAFANA_URL", "http://grafana-mcp:8000")
        self.mcp_client = MCPGrafanaClient(base_url=self.mcp_url)

        # Initialize LLM for intelligent analysis
        try:
            self.llm = get_llm()
            logger.info("LLM initialized for traces analysis")
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
        Analyze distributed traces based on user query

        Args:
            query: User query
            time_range: Time range for analysis
            context: Additional context (services, focus, etc.)

        Returns:
            Analysis results
        """
        context = context or {}
        logger.info(f"Analyzing traces for query: {query}")

        # Build TraceQL query
        traceql_query = self._build_traceql_query(query, context)
        logger.info(f"Generated TraceQL: {traceql_query}")

        # Query Tempo via MCP
        traces_data = await self._query_tempo(traceql_query, time_range)

        # Analyze trace data with LLM if available
        if self.llm and traces_data.get("traces"):
            analysis = await self._analyze_traces_with_llm(traces_data, query, context, time_range)
        else:
            analysis = self._analyze_traces(traces_data, query, context)

        return {
            "agent_name": "traces",
            "analysis": analysis["summary"],
            "data": analysis["data"],
            "confidence": analysis["confidence"],
            "grafana_links": self._generate_grafana_links(traceql_query, time_range),
            "timestamp": datetime.now().isoformat(),
        }

    def _build_traceql_query(self, query: str, context: dict[str, Any]) -> str:
        """
        Build TraceQL query from user query and context

        Args:
            query: User query
            context: Context with services, focus, etc.

        Returns:
            TraceQL query string
        """
        filters = []
        services = context.get("services", [])
        query_lower = query.lower()

        # Service filter
        if services:
            service_filter = "|".join(services)
            filters.append(f'service.name=~"{service_filter}"')

        # Error filter
        if "error" in query_lower or "fail" in query_lower:
            filters.append("status=error")

        # Slow/latency filter
        if "slow" in query_lower or "latency" in query_lower:
            filters.append("duration > 500ms")

        # Build final query
        if filters:
            traceql = "{" + " && ".join(filters) + "}"
        else:
            traceql = '{service.name=~".+"}'

        return traceql

    async def _query_tempo(self, traceql: str, time_range: str) -> dict[str, Any]:
        """
        Query Tempo via MCP Grafana

        Args:
            traceql: TraceQL query
            time_range: Time range

        Returns:
            Traces data
        """
        logger.info(f"Querying Tempo with: {traceql}")

        # Query via MCP client
        result = await self.mcp_client.query_traces(
            query=traceql, time_range=time_range, limit=50
        )

        # Return in expected format
        if "error" in result:
            logger.warning(f"Tempo query error: {result['error']}")
            # Return mock data as fallback
            return {
                "traces": [],
                "total_count": 0,
                "failed_count": 0,
            }

        return result

    def _analyze_traces(
        self,
        traces_data: dict[str, Any],
        query: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Analyze trace data and generate insights

        Args:
            traces_data: Raw traces from Tempo
            query: Original user query
            context: Request context

        Returns:
            Analysis with summary, data, and confidence
        """
        traces = traces_data.get("traces", [])
        total_count = traces_data.get("total_count", len(traces))
        failed_count = traces_data.get("failed_count", 0)

        # Analyze durations
        durations = [t.get("duration_ms", 0) for t in traces]
        avg_duration = sum(durations) / len(durations) if durations else 0
        slow_traces = [t for t in traces if t.get("duration_ms", 0) > 300]

        # Find bottlenecks (slowest operations)
        bottlenecks = {}
        all_services = set()

        for trace in traces:
            for span in trace.get("spans", []):
                service = span.get("service", "unknown")
                operation = span.get("operation", "unknown")
                duration = span.get("duration_ms", 0)

                key = f"{service}::{operation}"
                if key not in bottlenecks:
                    bottlenecks[key] = {
                        "service": service,
                        "operation": operation,
                        "durations": [],
                    }
                bottlenecks[key]["durations"].append(duration)
                all_services.add(service)

        # Calculate average durations for bottlenecks
        bottleneck_list = []
        for key, data in bottlenecks.items():
            avg_dur = sum(data["durations"]) / len(data["durations"])
            if avg_dur > 100:  # Only include slow operations
                bottleneck_list.append(
                    {
                        "service": data["service"],
                        "operation": data["operation"],
                        "avg_duration_ms": int(avg_dur),
                        "count": len(data["durations"]),
                    }
                )

        bottleneck_list.sort(key=lambda x: x["avg_duration_ms"], reverse=True)

        # Build summary
        summary_parts = [
            f"Analyzed {total_count} traces over the last {context.get('time_range', '1h')}."
        ]

        if failed_count > 0:
            summary_parts.append(
                f"Found {failed_count} failed traces ({failed_count/total_count*100:.1f}% failure rate)."
            )

        summary_parts.append(f"Average trace duration: {int(avg_duration)}ms.")

        if slow_traces:
            summary_parts.append(f"Detected {len(slow_traces)} slow traces (>300ms).")

        if bottleneck_list:
            top_bottleneck = bottleneck_list[0]
            summary_parts.append(
                f"Primary bottleneck: {top_bottleneck['service']}.{top_bottleneck['operation']} "
                f"({top_bottleneck['avg_duration_ms']}ms average)."
            )

        summary_parts.append(
            f"Service dependency chain: {' → '.join(sorted(all_services))}."
        )

        return {
            "summary": " ".join(summary_parts),
            "data": {
                "total_traces": total_count,
                "slow_traces": len(slow_traces),
                "failed_traces": failed_count,
                "avg_duration_ms": int(avg_duration),
                "bottlenecks": bottleneck_list[:5],  # Top 5 bottlenecks
                "service_dependencies": sorted(all_services),
            },
            "confidence": 0.85 if total_count > 10 else 0.5,
        }

    def _generate_grafana_links(self, traceql: str, time_range: str) -> list[str]:
        """
        Generate Grafana Explore links

        Args:
            traceql: TraceQL query
            time_range: Time range

        Returns:
            List of Grafana URLs
        """
        # TODO: Generate actual Grafana Explore URLs
        base_url = "http://grafana:3000/explore"
        return [f"{base_url}?query={traceql}&range={time_range}"]

    async def _analyze_traces_with_llm(
        self,
        traces_data: dict[str, Any],
        query: str,
        context: dict[str, Any],
        time_range: str,
    ) -> dict[str, Any]:
        """
        Use LLM to analyze trace data - NO calculations, just LLM analysis

        Args:
            traces_data: Raw traces from Tempo (via MCP)
            query: Original user query
            context: Request context
            time_range: Time range

        Returns:
            Analysis with summary and raw data from MCP
        """
        traces = traces_data.get("traces", [])
        total_traces = len(traces)

        # Simple statistics (no complex calculations!)
        slow_count = sum(1 for t in traces if t.get("duration_ms", 0) > 500)
        failed_count = sum(1 for t in traces if t.get("error", False))
        avg_duration = sum(t.get("duration_ms", 0) for t in traces) / total_traces if total_traces > 0 else 0

        # Extract unique services (simple set operation)
        services = set()
        for trace in traces:
            for span in trace.get("spans", []):
                services.add(span.get("service_name", "unknown"))

        # Prepare trace samples for LLM
        trace_samples_text = []
        for trace in traces[:5]:
            trace_id = trace.get("trace_id", "")[:16]
            duration = trace.get("duration_ms", 0)
            spans = len(trace.get("spans", []))
            error = trace.get("error", False)
            trace_samples_text.append(f"- {trace_id}: {duration}ms, {spans} spans, error={error}")

        # Load prompt template from markdown file
        prompt_template = load_prompt("analyze_traces.md")
        if not prompt_template:
            # Fallback
            return self._analyze_traces(traces_data, query, context)

        # Replace variables in template
        prompt = prompt_template.format(
            query=query,
            time_range=time_range,
            total_traces=total_traces,
            avg_duration=f"{avg_duration:.0f}",
            slow_traces=slow_count,
            failed_traces=failed_count,
            services_count=len(services),
            trace_samples="\n".join(trace_samples_text) if trace_samples_text else "No traces found"
        )

        try:
            response = self.llm.invoke(prompt)
            llm_analysis = response.content if hasattr(response, "content") else str(response)
            logger.info("LLM traces analysis complete")

            # Return raw MCP data + LLM analysis (no calculations!)
            return {
                "summary": llm_analysis,
                "data": {
                    "total_traces": total_traces,
                    "avg_duration_ms": avg_duration,
                    "sample_traces": traces[:5],  # Raw samples from MCP
                },
                "confidence": 0.95 if total_traces > 0 else 0.5,
            }

        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}, using fallback")
            return self._analyze_traces(traces_data, query, context)

    async def check_mcp_health(self) -> bool:
        """
        Check if MCP Grafana server is reachable

        Returns:
            True if healthy, False otherwise
        """
        return await self.mcp_client.health_check()
