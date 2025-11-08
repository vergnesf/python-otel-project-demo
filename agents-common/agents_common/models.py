"""
Shared Pydantic models for agent communication
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Type of specialized agent"""

    ORCHESTRATOR = "orchestrator"
    LOGS = "logs"
    METRICS = "metrics"
    TRACES = "traces"


class AgentRequest(BaseModel):
    """Request sent to a specialized agent"""

    query: str = Field(..., description="User query to analyze")
    time_range: str = Field(default="1h", description="Time range for analysis (e.g., '1h', '24h', '7d')")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context for the agent")
    timestamp: datetime = Field(default_factory=datetime.now, description="Request timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Why is the order service failing?",
                "time_range": "1h",
                "context": {"services": ["order", "ordercheck"], "error_rate": 0.1},
            }
        }


class AgentResponse(BaseModel):
    """Response from a specialized agent"""

    agent_name: AgentType = Field(..., description="Name of the agent that produced this response")
    analysis: str = Field(..., description="Natural language analysis of the findings")
    data: dict[str, Any] = Field(default_factory=dict, description="Structured data supporting the analysis")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence score (0-1)")
    grafana_links: list[str] = Field(default_factory=list, description="Links to Grafana dashboards/queries")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    error: Optional[str] = Field(default=None, description="Error message if analysis failed")

    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "logs",
                "analysis": "Found 47 errors in order service over the last hour. Primary cause: Simulated DB insertion errors (ERROR_RATE=0.1).",
                "data": {
                    "error_count": 47,
                    "error_types": [
                        {"type": "Simulated DB insertion error", "count": 42},
                        {"type": "Unexpected error during order creation", "count": 5},
                    ],
                    "affected_services": ["order"],
                },
                "confidence": 0.95,
                "grafana_links": ["http://grafana:3000/explore?..."],
            }
        }


class OrchestratorResponse(BaseModel):
    """Final response from the orchestrator to the UI"""

    query: str = Field(..., description="Original user query")
    summary: str = Field(..., description="Synthesized summary of all agent analyses")
    agent_responses: dict[str, AgentResponse] = Field(..., description="Individual responses from each agent")
    recommendations: list[str] = Field(default_factory=list, description="Actionable recommendations")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Analyze problems with the order service",
                "summary": "The order service has a 10% error rate due to simulated DB failures...",
                "agent_responses": {
                    "logs": {"agent_name": "logs", "analysis": "...", "data": {}},
                    "metrics": {"agent_name": "metrics", "analysis": "...", "data": {}},
                    "traces": {"agent_name": "traces", "analysis": "...", "data": {}},
                },
                "recommendations": [
                    "Check ERROR_RATE environment variable configuration",
                    "Review database connection pool settings",
                ],
            }
        }
