"""
Orchestrator logic for coordinating specialized agents
"""

import asyncio
import logging
import os
from typing import Any

import httpx
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Main orchestrator that coordinates specialized observability agents
    """

    def __init__(self):
        """Initialize orchestrator with agent endpoints"""
        self.logs_agent_url = os.getenv("AGENT_LOGS_URL", "http://agent-logs:8002")
        self.metrics_agent_url = os.getenv("AGENT_METRICS_URL", "http://agent-metrics:8003")
        self.traces_agent_url = os.getenv("AGENT_TRACES_URL", "http://agent-traces:8004")
        
        self.client = httpx.AsyncClient(timeout=60.0)
        
        # LLM will be imported from agents-common when available
        # For now, we'll use simple logic
        self.llm = None

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def analyze(self, query: str, time_range: str = "1h") -> dict[str, Any]:
        """
        Analyze user query by coordinating specialized agents
        
        Args:
            query: User query to analyze
            time_range: Time range for analysis
            
        Returns:
            Synthesized response from all agents
        """
        logger.info(f"Analyzing query: {query}")
        
        # Prepare request for agents
        agent_request = {
            "query": query,
            "time_range": time_range,
            "context": self._extract_context(query),
        }
        
        # Query all agents in parallel
        responses = await asyncio.gather(
            self._query_agent(self.logs_agent_url, agent_request),
            self._query_agent(self.metrics_agent_url, agent_request),
            self._query_agent(self.traces_agent_url, agent_request),
            return_exceptions=True,
        )
        
        logs_response, metrics_response, traces_response = responses
        
        # Synthesize responses
        summary = self._synthesize_responses(
            query=query,
            logs=logs_response if not isinstance(logs_response, Exception) else None,
            metrics=metrics_response if not isinstance(metrics_response, Exception) else None,
            traces=traces_response if not isinstance(traces_response, Exception) else None,
        )
        
        return {
            "query": query,
            "summary": summary["summary"],
            "agent_responses": {
                "logs": logs_response if not isinstance(logs_response, Exception) else {"error": str(logs_response)},
                "metrics": metrics_response if not isinstance(metrics_response, Exception) else {"error": str(metrics_response)},
                "traces": traces_response if not isinstance(traces_response, Exception) else {"error": str(traces_response)},
            },
            "recommendations": summary["recommendations"],
            "timestamp": summary["timestamp"],
        }

    async def _query_agent(self, agent_url: str, request: dict[str, Any]) -> dict[str, Any]:
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

    def _extract_context(self, query: str) -> dict[str, Any]:
        """
        Extract context from user query
        
        Args:
            query: User query
            
        Returns:
            Context dictionary
        """
        context = {}
        
        # Extract service names
        services = ["customer", "order", "stock", "supplier", "ordermanagement", "ordercheck", "suppliercheck"]
        mentioned_services = [s for s in services if s in query.lower()]
        if mentioned_services:
            context["services"] = mentioned_services
        
        # Extract error keywords
        error_keywords = ["error", "fail", "problem", "issue", "slow", "latency"]
        has_errors = any(keyword in query.lower() for keyword in error_keywords)
        if has_errors:
            context["focus"] = "errors"
        
        return context

    def _synthesize_responses(
        self,
        query: str,
        logs: dict | None,
        metrics: dict | None,
        traces: dict | None,
    ) -> dict[str, Any]:
        """
        Synthesize responses from all agents into a coherent summary
        
        Args:
            query: Original user query
            logs: Response from logs agent
            metrics: Response from metrics agent
            traces: Response from traces agent
            
        Returns:
            Synthesized summary and recommendations
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
        recommendations.extend([
            "Check ERROR_RATE environment variable if errors are simulated",
            "Review Grafana dashboards for additional insights",
        ])
        
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
