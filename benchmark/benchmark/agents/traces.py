"""Traces agent benchmarks."""

import asyncio
import logging
import time
from typing import Any

import httpx

from ..agent_requests import TracesAnalysisRequest
from ..metrics import MetricsCollector

logger = logging.getLogger(__name__)


class TracesBenchmark:
    """Benchmark suite for traces agent."""

    def __init__(
        self,
        traces_url: str = "http://traefik/agent-traces",
        timeout: float = 30.0,
    ):
        """Initialize traces benchmark."""
        self.traces_url = traces_url
        self.timeout = timeout
        self.metrics = MetricsCollector()

    async def check_health(self) -> bool:
        """Check if traces agent is healthy."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.traces_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def benchmark_analyze(
        self,
        model: str,
        query: str = "Analyze request latency and errors",
        service_name: str = "",
        time_range: str = "1h",
        num_requests: int = 1,
    ) -> list[dict[str, Any]]:
        """
        Benchmark the /analyze endpoint.

        Args:
            model: Model to use for analysis
            query: Trace analysis query
            service_name: Service name to filter traces
            time_range: Time range for trace query
            num_requests: Number of requests to send

        Returns:
            List of benchmark results
        """
        logger.info(
            f"Benchmarking traces /analyze endpoint "
            f"({num_requests} requests with {model})"
        )

        results = []

        for i in range(num_requests):
            try:
                request = TracesAnalysisRequest(
                    query=query,
                    model=model,
                    service_name=service_name,
                    time_range=time_range,
                )

                start_time = time.perf_counter()
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.traces_url}/analyze",
                        json=request.model_dump(),
                    )
                    response.raise_for_status()
                    data = response.json()
                end_time = time.perf_counter()

                latency_ms = (end_time - start_time) * 1000
                self.metrics.record_result(
                    model=model,
                    agent="traces",
                    latency_ms=latency_ms,
                    success=True,
                    metadata={"request_num": i + 1, "response_length": len(str(data))},
                )

                results.append({
                    "request_num": i + 1,
                    "latency_ms": latency_ms,
                    "success": True,
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
                    agent="traces",
                    latency_ms=0.0,
                    success=False,
                    error=str(e),
                )
                results.append({
                    "request_num": i + 1,
                    "success": False,
                    "error": str(e),
                })

            if i < num_requests - 1:
                await asyncio.sleep(0.1)

        return results

    async def close(self) -> None:
        """Close client connection (no-op with httpx context manager)."""
        pass
