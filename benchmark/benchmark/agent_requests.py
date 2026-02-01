"""Data models for agent requests and responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BenchmarkResult(BaseModel):
    """Benchmark result for a single request."""

    model: str
    agent: str
    latency_ms: float = Field(..., description="Request latency in milliseconds")
    memory_delta_mb: float = Field(
        default=0.0, description="Memory usage delta in MB"
    )
    success: bool = Field(default=True, description="Whether request succeeded")
    error: str | None = Field(default=None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BenchmarkSummary(BaseModel):
    """Summary statistics for benchmark results."""

    model: str
    agent: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    latency_ms_p50: float
    latency_ms_p95: float
    latency_ms_p99: float
    latency_ms_mean: float
    latency_ms_std: float
    memory_delta_mb_mean: float
    error_rate: float
    requests_per_second: float
    started_at: datetime
    completed_at: datetime


class OrchestratorRequest(BaseModel):
    """Request for orchestrator agent."""

    query: str
    time_range: str = Field(default="1h")
    model: str | None = Field(default="mistral:7b", description="LLM model to use")
    model_params: dict | None = Field(
        default=None, description="Optional LLM parameters (temperature, top_k, max_tokens)"
    )


class LogsAnalysisRequest(BaseModel):
    """Request for logs agent."""

    query: str
    time_range: str = Field(default="1h")
    context: dict = Field(default_factory=dict)


class MetricsAnalysisRequest(BaseModel):
    """Request for metrics agent."""

    query: str
    model: str = Field(default="mistral:7b")
    time_range: str = Field(default="1h")
    aggregation: str = Field(default="mean")
    context: dict[str, Any] = Field(default_factory=dict)


class TracesAnalysisRequest(BaseModel):
    """Request for traces agent."""

    query: str
    model: str = Field(default="mistral:7b")
    service_name: str = Field(default="")
    operation_name: str = Field(default="")
    time_range: str = Field(default="1h")
    context: dict[str, Any] = Field(default_factory=dict)


class TranslationRequest(BaseModel):
    """Request for translation agent."""

    query: str
    model: str | None = Field(default=None)
    model_params: dict | None = Field(default=None)


class HealthStatus(BaseModel):
    """Health check status."""

    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: str = ""
