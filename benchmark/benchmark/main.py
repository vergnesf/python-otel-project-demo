#!/usr/bin/env python3
"""Benchmark runner for agent APIs."""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path

import yaml
from rich.panel import Panel
from rich import box

from benchmark.summary import render_summary
from benchmark.ui import console
from benchmark.config import BENCHMARK_MODELS, MODEL_CONFIGS

from benchmark.benchmarks import (
    benchmark_orchestrator,
    benchmark_logs_agent,
    benchmark_metrics_agent,
    benchmark_traces_agent,
    benchmark_translation_agent,
)

# Configure logging (only for errors/warnings)
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Run all benchmarks."""
    start_time = time.perf_counter()
    logger.info(f"Starting benchmarks at {datetime.now().isoformat()}")
    logger.info(f"Models: {', '.join(BENCHMARK_MODELS)}")

    all_results = {}
    
    all_results["orchestrator"] = await benchmark_orchestrator()
    all_results["logs"] = await benchmark_logs_agent()
    all_results["metrics"] = await benchmark_metrics_agent()
    all_results["traces"] = await benchmark_traces_agent()
    all_results["translation"] = await benchmark_translation_agent()

    total_duration = time.perf_counter() - start_time

    # Print summary
    console.print()
    console.print(Panel("[bold cyan]BENCHMARK SUMMARY[/bold cyan]", box=box.DOUBLE))
    
    console.print()
    console.print("[bold]Overall Results:[/bold]")
    console.print(f"  Total benchmark duration: {total_duration:.2f}s")
    console.print(f"  Models tested: {', '.join(BENCHMARK_MODELS)}")
    
    render_summary(all_results, BENCHMARK_MODELS)
    
    # Export to HTML
    console.print()
    console.print("[bold yellow]💾 Exporting to HTML...[/bold yellow]")
    output_file = Path("benchmark_results.html")
    console.save_html(str(output_file), clear=False)
    console.print(f"[green]✓ Saved to {output_file.absolute()}[/green]")


def cli_main() -> None:
    """CLI entry point for the benchmark command."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
