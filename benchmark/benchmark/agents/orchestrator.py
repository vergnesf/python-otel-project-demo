"""Orchestrator agent benchmarks."""

import asyncio
import logging
import time
from typing import Any

import httpx

from ..agent_requests import OrchestratorRequest
from ..metrics import MetricsCollector

logger = logging.getLogger(__name__)


class OrchestratorBenchmark:
    """Benchmark suite for orchestrator agent."""

    def __init__(
        self,
        orchestrator_url: str = "http://traefik/agent-orchestrator",
        timeout: float = 30.0,
    ):
        """Initialize orchestrator benchmark."""
        self.orchestrator_url = orchestrator_url
        self.timeout = timeout
        self.metrics = MetricsCollector()

    async def check_health(self) -> bool:
        """Check if orchestrator is healthy."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.orchestrator_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def benchmark_analyze(
        self,
        model: str,
        query: str = "Analyze the system performance and provide insights",
        temperature: float = 0.7,
        num_requests: int = 1,
    ) -> list[dict[str, Any]]:
        """
        Benchmark the /analyze endpoint.

        Args:
            model: Model to use for analysis
            query: Analysis query
            temperature: Model temperature (0-1)
            num_requests: Number of requests to send

        Returns:
            List of benchmark results
        """
        logger.info(
            f"Benchmarking orchestrator /analyze endpoint "
            f"({num_requests} requests with {model})"
        )

        results = []

        for i in range(num_requests):
            try:
                request = OrchestratorRequest(
                    query=query,
                    model=model,
                    temperature=temperature,
                )

                start_time = time.perf_counter()
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.orchestrator_url}/analyze",
                        json=request.model_dump(),
                    )
                    response.raise_for_status()
                    data = response.json()
                end_time = time.perf_counter()

                latency_ms = (end_time - start_time) * 1000
                self.metrics.record_result(
                    model=model,
                    agent="orchestrator",
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
                    agent="orchestrator",
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
                await asyncio.sleep(0.1)  # Small delay between requests

        return results

    async def close(self) -> None:
        """Close client connection (no-op with httpx context manager)."""
        pass
