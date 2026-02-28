"""Metrics collection and analysis for benchmark results."""

import logging
import statistics
from typing import Any

import psutil

from .models import BenchmarkResult, BenchmarkSummary

logger = logging.getLogger(__name__)


def get_memory_usage_mb() -> float:
    """Get current process memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / (1024 * 1024)


class MetricsCollector:
    """Collects and analyzes benchmark metrics."""

    def __init__(self):
        """Initialize metrics collector."""
        self.results: list[BenchmarkResult] = []
        self.memory_baseline_mb = get_memory_usage_mb()

    def record_result(
        self,
        model: str,
        agent: str,
        latency_ms: float,
        success: bool = True,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> BenchmarkResult:
        """
        Record a benchmark result.

        Args:
            model: Model name
            agent: Agent name
            latency_ms: Request latency in milliseconds
            success: Whether request succeeded
            error: Error message if failed
            metadata: Additional metadata

        Returns:
            Recorded BenchmarkResult
        """
        memory_delta = get_memory_usage_mb() - self.memory_baseline_mb

        result = BenchmarkResult(
            model=model,
            agent=agent,
            latency_ms=latency_ms,
            memory_delta_mb=memory_delta,
            success=success,
            error=error,
            metadata=metadata or {},
        )

        self.results.append(result)
        logger.debug(
            f"Recorded: {agent} ({model}) - {latency_ms:.2f}ms, "
            f"success={success}, memory_delta={memory_delta:.2f}MB"
        )
        return result

    def get_summary(
        self, model: str, agent: str
    ) -> BenchmarkSummary | None:
        """
        Get summary statistics for a model/agent combination.

        Args:
            model: Model name
            agent: Agent name

        Returns:
            BenchmarkSummary or None if no results
        """
        results = [
            r
            for r in self.results
            if r.model == model and r.agent == agent
        ]

        if not results:
            return None

        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        latencies = [r.latency_ms for r in successful]
        if not latencies:
            return None

        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)

        def percentile(p: int) -> float:
            idx = int((p / 100.0) * n)
            return latencies_sorted[min(idx, n - 1)]

        memory_deltas = [r.memory_delta_mb for r in successful]
        memory_mean = (
            statistics.mean(memory_deltas) if memory_deltas else 0.0
        )

        total_time_s = (
            max(r.timestamp for r in results).timestamp()
            - min(r.timestamp for r in results).timestamp()
        )
        rps = len(results) / max(total_time_s, 1.0)

        return BenchmarkSummary(
            model=model,
            agent=agent,
            total_requests=len(results),
            successful_requests=len(successful),
            failed_requests=len(failed),
            latency_ms_p50=percentile(50),
            latency_ms_p95=percentile(95),
            latency_ms_p99=percentile(99),
            latency_ms_mean=statistics.mean(latencies),
            latency_ms_std=(
                statistics.stdev(latencies)
                if len(latencies) > 1
                else 0.0
            ),
            memory_delta_mb_mean=memory_mean,
            error_rate=len(failed) / len(results) if results else 0.0,
            requests_per_second=rps,
            started_at=min(r.timestamp for r in results),
            completed_at=max(r.timestamp for r in results),
        )

    def get_all_summaries(self) -> dict[str, dict[str, BenchmarkSummary]]:
        """
        Get summaries grouped by model and agent.

        Returns:
            Dictionary of summaries keyed by model then agent
        """
        summaries: dict[str, dict[str, BenchmarkSummary]] = {}

        for result in self.results:
            if result.model not in summaries:
                summaries[result.model] = {}

        for model in summaries:
            for result in self.results:
                if result.model == model:
                    agent = result.agent
                    summary = self.get_summary(model, agent)
                    if summary and agent not in summaries[model]:
                        summaries[model][agent] = summary

        return summaries

    def print_summary(self) -> None:
        """Print formatted summary of all results."""
        summaries = self.get_all_summaries()

        if not summaries:
            logger.info("No results to summarize")
            return

        print("\n" + "=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)

        for model, agents in summaries.items():
            print(f"\nModel: {model}")
            print("-" * 80)

            for agent_name, summary in agents.items():
                print(f"\n  Agent: {agent_name}")
                print(
                    f"    Requests: {summary.total_requests} "
                    f"(✓ {summary.successful_requests}, "
                    f"✗ {summary.failed_requests})"
                )
                print(
                    f"    Error Rate: {summary.error_rate * 100:.2f}%"
                )
                print("    Latency (ms):")
                print(f"      p50: {summary.latency_ms_p50:.2f}")
                print(f"      p95: {summary.latency_ms_p95:.2f}")
                print(f"      p99: {summary.latency_ms_p99:.2f}")
                print(
                    f"      mean: {summary.latency_ms_mean:.2f} "
                    f"(σ={summary.latency_ms_std:.2f})"
                )
                print(
                    f"    Memory Delta: {summary.memory_delta_mb_mean:.2f} MB"
                )
                print(
                    f"    Throughput: {summary.requests_per_second:.2f} req/s"
                )

        print("\n" + "=" * 80)
