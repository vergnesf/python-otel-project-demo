#!/usr/bin/env python3
"""Benchmark runner for agent APIs."""

import asyncio
import logging
from datetime import datetime

import httpx

from benchmark.agents.logs import LogsBenchmark
from benchmark.agents.metrics import MetricsBenchmark
from benchmark.agents.orchestrator import OrchestratorBenchmark
from benchmark.agents.traces import TracesBenchmark
from benchmark.agents.translation import TranslationBenchmark
from benchmark.config import (
    AGENT_LOGS_URL,
    AGENT_METRICS_URL,
    AGENT_TRACES_URL,
    BENCHMARK_MODELS,
    BENCHMARK_TIMEOUT,
    LOG_LEVEL,
    ORCHESTRATOR_URL,
    TRANSLATION_URL,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def check_service_available(url: str, timeout: float = 5.0) -> bool:
    """Check if a service is available via health check."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{url}/health")
            return response.status_code == 200
    except Exception as e:
        logger.warning(f"Service {url} not available: {e}")
        return False


async def benchmark_orchestrator() -> None:
    """Benchmark orchestrator agent."""
    logger.info(f"\n{'='*60}")
    logger.info("Orchestrator Agent Benchmarks")
    logger.info(f"{'='*60}")

    available = await check_service_available(ORCHESTRATOR_URL)
    if not available:
        logger.warning("Orchestrator service not available, skipping")
        return

    benchmark = OrchestratorBenchmark(ORCHESTRATOR_URL, timeout=BENCHMARK_TIMEOUT)
    try:
        for model in BENCHMARK_MODELS:
            logger.info(f"\nBenchmarking {model}...")
            try:
                results = await benchmark.benchmark_analyze(model=model, num_requests=1)
                if results and results[0]["success"]:
                    logger.info(f"✓ {model}: {results[0]['latency_ms']:.2f}ms")
                else:
                    logger.error(f"✗ {model}: Request failed")
            except Exception as e:
                logger.error(f"✗ {model}: {e}")
    finally:
        await benchmark.close()


async def benchmark_logs_agent() -> None:
    """Benchmark logs agent."""
    logger.info(f"\n{'='*60}")
    logger.info("Logs Agent Benchmarks")
    logger.info(f"{'='*60}")

    available = await check_service_available(AGENT_LOGS_URL)
    if not available:
        logger.warning("Logs agent service not available, skipping")
        return

    benchmark = LogsBenchmark(AGENT_LOGS_URL, timeout=BENCHMARK_TIMEOUT)
    try:
        for model in BENCHMARK_MODELS:
            logger.info(f"\nBenchmarking {model}...")
            try:
                results = await benchmark.benchmark_analyze(model=model, num_requests=1)
                if results and results[0]["success"]:
                    logger.info(f"✓ {model}: {results[0]['latency_ms']:.2f}ms")
                else:
                    logger.error(f"✗ {model}: Request failed")
            except Exception as e:
                logger.error(f"✗ {model}: {e}")
    finally:
        await benchmark.close()


async def benchmark_metrics_agent() -> None:
    """Benchmark metrics agent."""
    logger.info(f"\n{'='*60}")
    logger.info("Metrics Agent Benchmarks")
    logger.info(f"{'='*60}")

    available = await check_service_available(AGENT_METRICS_URL)
    if not available:
        logger.warning("Metrics agent service not available, skipping")
        return

    benchmark = MetricsBenchmark(AGENT_METRICS_URL, timeout=BENCHMARK_TIMEOUT)
    try:
        for model in BENCHMARK_MODELS:
            logger.info(f"\nBenchmarking {model}...")
            try:
                results = await benchmark.benchmark_analyze(model=model, num_requests=1)
                if results and results[0]["success"]:
                    logger.info(f"✓ {model}: {results[0]['latency_ms']:.2f}ms")
                else:
                    logger.error(f"✗ {model}: Request failed")
            except Exception as e:
                logger.error(f"✗ {model}: {e}")
    finally:
        await benchmark.close()


async def benchmark_traces_agent() -> None:
    """Benchmark traces agent."""
    logger.info(f"\n{'='*60}")
    logger.info("Traces Agent Benchmarks")
    logger.info(f"{'='*60}")

    available = await check_service_available(AGENT_TRACES_URL)
    if not available:
        logger.warning("Traces agent service not available, skipping")
        return

    benchmark = TracesBenchmark(AGENT_TRACES_URL, timeout=BENCHMARK_TIMEOUT)
    try:
        for model in BENCHMARK_MODELS:
            logger.info(f"\nBenchmarking {model}...")
            try:
                results = await benchmark.benchmark_analyze(model=model, num_requests=1)
                if results and results[0]["success"]:
                    logger.info(f"✓ {model}: {results[0]['latency_ms']:.2f}ms")
                else:
                    logger.error(f"✗ {model}: Request failed")
            except Exception as e:
                logger.error(f"✗ {model}: {e}")
    finally:
        await benchmark.close()


async def benchmark_translation_agent() -> None:
    """Benchmark translation agent."""
    logger.info(f"\n{'='*60}")
    logger.info("Translation Agent Benchmarks")
    logger.info(f"{'='*60}")

    available = await check_service_available(TRANSLATION_URL)
    if not available:
        logger.warning("Translation agent service not available, skipping")
        return

    benchmark = TranslationBenchmark(TRANSLATION_URL, timeout=BENCHMARK_TIMEOUT)
    try:
        for model in BENCHMARK_MODELS:
            logger.info(f"\nBenchmarking {model}...")
            try:
                results = await benchmark.benchmark_translate(model=model, num_requests=1)
                if results and results[0]["success"]:
                    logger.info(f"✓ {model}: {results[0]['latency_ms']:.2f}ms")
                else:
                    logger.error(f"✗ {model}: Request failed")
            except Exception as e:
                logger.error(f"✗ {model}: {e}")
    finally:
        await benchmark.close()


async def main() -> None:
    """Run all benchmarks."""
    logger.info(f"Starting benchmarks at {datetime.now().isoformat()}")
    logger.info(f"Models: {', '.join(BENCHMARK_MODELS)}")

    await benchmark_orchestrator()
    await benchmark_logs_agent()
    await benchmark_metrics_agent()
    await benchmark_traces_agent()
    await benchmark_translation_agent()

    logger.info(f"\n{'='*60}")
    logger.info("Benchmarks completed")
    logger.info(f"{'='*60}")


def cli_main() -> None:
    """CLI entry point for the benchmark command."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
