"""Metrics agent benchmarks."""

import asyncio
import logging
import time
from typing import Any

import httpx

from ..agent_requests import MetricsAnalysisRequest
from ..metrics import MetricsCollector

logger = logging.getLogger(__name__)


class MetricsBenchmark:
    """Benchmark suite for metrics agent."""

    def __init__(
        self,
        metrics_url: str = "http://traefik/agent-metrics",
        timeout: float = 600.0,
    ):
        """Initialize metrics benchmark."""
        self.metrics_url = metrics_url
        self.timeout = timeout
        self.metrics = MetricsCollector()

    async def check_health(self) -> bool:
        """Check if metrics agent is healthy."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.metrics_url}/health")
                return response.status_code == 200
        except Exception:
            return False
        return await self.client.health_check()

    async def benchmark_analyze(
        self,
        model: str,
        query: str = "Analyze CPU and memory usage trends",
        time_range: str = "1h",
        num_requests: int = 1,
    ) -> list[dict[str, Any]]:
        """
        Benchmark the /analyze endpoint.

        Args:
            model: Model to use for analysis
            query: Metrics analysis query
            time_range: Time range for metrics query
            num_requests: Number of requests to send

        Returns:
            List of benchmark results
        """
        logger.info(
            f"Benchmarking metrics /analyze endpoint "
            f"({num_requests} requests with {model})"
        )

        results = []

        for i in range(num_requests):
            try:
                request = MetricsAnalysisRequest(
                    query=query,
                    model=model,
                    time_range=time_range,
                )

                start_time = time.perf_counter()
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.metrics_url}/analyze",
                        json=request.model_dump(),
                    )
                    response.raise_for_status()
                    data = response.json()
                end_time = time.perf_counter()

                latency_ms = (end_time - start_time) * 1000
                self.metrics.record_result(
                    model=model,
                    agent="metrics",
                    latency_ms=latency_ms,
                    success=True,
                    metadata={"request_num": i + 1, "response_length": len(str(data))},
                )

                results.append({
                    "request_num": i + 1,
                    "latency_ms": latency_ms,
                    "success": True,
                    "request": request.model_dump(),
                    "response": data,
                    "response_preview": str(data)[:100],
                })

                logger.debug(
                    f"Request {i + 1}/{num_requests}: "
                    f"{latency_ms:.2f}ms"
                )

            except Exception as e:
                logger.error(f"Request {i + 1}/{num_requests} failed: {e}")
                self.metrics.record_result(
                    model=model,
                    agent="metrics",
                    latency_ms=0.0,
                    success=False,
                    error=str(e),
                )
                results.append({
                    "request_num": i + 1,
                    "success": False,
                    "error": str(e),
                    "request": request.model_dump() if 'request' in locals() else None,
                })

            if i < num_requests - 1:
                await asyncio.sleep(0.1)

        return results

    async def close(self) -> None:
        """Close client connection (no-op with httpx context manager)."""
        pass
