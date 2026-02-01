"""Translation agent benchmarks."""

import asyncio
import logging
import time
from typing import Any

import httpx

from ..agent_requests import TranslationRequest
from ..metrics import MetricsCollector

logger = logging.getLogger(__name__)


class TranslationBenchmark:
    """Benchmark suite for translation agent."""

    def __init__(
        self,
        translation_url: str = "http://traefik/agent-traduction",
        timeout: float = 600.0,
    ):
        """Initialize translation benchmark."""
        self.translation_url = translation_url
        self.timeout = timeout
        self.metrics = MetricsCollector()

    async def check_health(self) -> bool:
        """Check if translation agent is healthy."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.translation_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def benchmark_translate(
        self,
        model: str,
        text: str = "Bonjour, ceci est un test de traduction",
        num_requests: int = 1,
    ) -> list[dict[str, Any]]:
        """
        Benchmark the /translate endpoint.

        Args:
            model: Model to use for translation
            text: Text to translate (used as query)
            num_requests: Number of requests to send

        Returns:
            List of benchmark results
        """
        logger.info(
            f"Benchmarking translation /translate endpoint "
            f"({num_requests} requests with {model})"
        )

        results = []

        for i in range(num_requests):
            try:
                request = TranslationRequest(
                    query=text,
                    model=model,
                )

                start_time = time.perf_counter()
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.translation_url}/translate",
                        json=request.model_dump(),
                    )
                    response.raise_for_status()
                    data = response.json()
                end_time = time.perf_counter()

                latency_ms = (end_time - start_time) * 1000
                self.metrics.record_result(
                    model=model,
                    agent="translation",
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
                    agent="translation",
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
