#!/usr/bin/env python3
"""Benchmark runner for agent APIs."""

import asyncio
import logging
import os
import time
from datetime import datetime
from pathlib import Path

import yaml
from rich.panel import Panel
from rich import box

from benchmark.summary import render_summary
from benchmark.ui import console
from benchmark.config import BENCHMARK_MODELS, MODEL_CONFIGS, OLLAMA_URL

from benchmark.benchmarks import (
    benchmark_orchestrator,
    benchmark_logs_agent,
    benchmark_metrics_agent,
    benchmark_traces_agent,
    benchmark_translation_agent,
)

# Import Ollama model management utilities
from common_ai import unload_ollama_model, load_ollama_model

# Configure logging (only for errors/warnings)
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Run all benchmarks."""
    # Set OLLAMA_URL for common-ai to use Traefik proxy
    os.environ["OLLAMA_URL"] = OLLAMA_URL
    
    logger.info(f"Starting benchmarks at {datetime.now().isoformat()}")
    logger.info(f"Models: {', '.join(BENCHMARK_MODELS)}")
    logger.info(f"Ollama URL: {OLLAMA_URL}")

    # Results structure: {agent_name: {model: results}}
    all_results = {
        "orchestrator": {},
        "logs": {},
        "metrics": {},
        "traces": {},
        "translation": {},
    }
    
    console.print("[yellow]ℹ️  Each model will run all agent tests, then unload before the next model[/yellow]")
    console.print()
    
    # Save original BENCHMARK_MODELS and run one model at a time
    original_models = BENCHMARK_MODELS.copy()
    
    # Track benchmark time (excluding warm-up and unload)
    benchmark_start_time = None
    
    # Loop through models first, then run all agents for each model
    for model in original_models:
        console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
        console.print(f"[bold cyan]Testing Model: {model}[/bold cyan]")
        console.print(f"[bold cyan]{'='*80}[/bold cyan]\n")
        
        # Warm up the model before benchmarking to exclude loading time
        console.print(f"[dim yellow]🔥 Warming up {model}...[/dim yellow]", end=" ")
        success = await load_ollama_model(model)
        if success:
            console.print("[dim green]✓[/dim green]")
        else:
            console.print("[dim red]✗[/dim red]")
        console.print()
        
        # Start benchmark timer after warm-up (only on first model)
        if benchmark_start_time is None:
            benchmark_start_time = time.perf_counter()
        
        # Temporarily set BENCHMARK_MODELS to single model
        import benchmark.config as config
        config.BENCHMARK_MODELS = [model]
        
        # Run all agent tests for this model
        orch_results = await benchmark_orchestrator()
        all_results["orchestrator"].update(orch_results)
        
        logs_results = await benchmark_logs_agent()
        all_results["logs"].update(logs_results)
        
        metrics_results = await benchmark_metrics_agent()
        all_results["metrics"].update(metrics_results)
        
        traces_results = await benchmark_traces_agent()
        all_results["traces"].update(traces_results)
        
        translation_results = await benchmark_translation_agent()
        all_results["translation"].update(translation_results)
        
        # Unload this model before moving to next
        console.print()
        console.print(f"[dim yellow]🔄 Unloading {model}...[/dim yellow]", end=" ")
        success = await unload_ollama_model(model)
        if success:
            console.print("[dim green]✓[/dim green]")
        else:
            console.print("[dim red]✗[/dim red]")
    
    # Restore original BENCHMARK_MODELS
    import benchmark.config as config
    config.BENCHMARK_MODELS = original_models

    total_duration = time.perf_counter() - benchmark_start_time

    # Print summary
    console.print()
    console.print(Panel("[bold cyan]BENCHMARK SUMMARY[/bold cyan]", box=box.DOUBLE))
    
    console.print()
    console.print("[bold]Overall Results:[/bold]")
    console.print(f"  Total benchmark duration: {total_duration:.2f}s")
    console.print(f"  Models tested: {', '.join(original_models)}")
    
    render_summary(all_results, original_models)
    
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
