"""Benchmark summary rendering helpers."""

from __future__ import annotations

import statistics

from rich import box
from rich.panel import Panel
from rich.table import Table

from benchmark.resources import format_optional_metric
from benchmark.ui import console


def render_summary(all_results: dict, benchmark_models: list[str]) -> None:
    """Render summary table and overall statistics."""
    console.print()

    # Collect all data for table
    table_rows: list[dict[str, object]] = []
    for model in benchmark_models:
        for agent_name in ["orchestrator", "logs", "metrics", "traces", "translation"]:
            results = all_results.get(agent_name, {})
            if model in results:
                stats = results[model]
                success_rate_str = stats.get("success_rate", "0/0")
                is_valid = stats.get("is_valid", True)
                # Parse success count and total from "X/Y" format
                try:
                    success_count, total_count = map(int, success_rate_str.split("/"))
                    has_failures = success_count < total_count
                except ValueError:
                    success_count = 0
                    total_count = 0
                    has_failures = True

                row = {
                    "model": model,
                    "agent": agent_name,
                    "avg_time": stats.get("avg_time_ms", stats.get("total_time_ms", 0)),
                    "cpu": stats.get("cpu_max"),
                    "ram": stats.get("ram_max_mb"),
                    "gpu": stats.get("gpu_util_max"),
                    "vram": stats.get("vram_max_mb"),
                    "success_rate": success_rate_str,
                    "is_valid": is_valid,
                    "has_failures": has_failures,
                }
                table_rows.append(row)

    # Create Rich Table
    console.print()
    console.print("=" * 120)
    table = Table(
        title="[bold]BENCHMARK SUMMARY TABLE[/bold]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Model", style="yellow", width=20)
    table.add_column("Agent", style="cyan", width=15)
    table.add_column("Avg Time (ms)", justify="right", width=15)
    table.add_column("CPU %", justify="right", width=10)
    table.add_column("RAM MB", justify="right", width=12)
    table.add_column("GPU %", justify="right", width=10)
    table.add_column("VRAM MB", justify="right", width=12)
    table.add_column("Status", justify="center", width=12)

    # Add rows grouped by model
    current_model: str | None = None
    for row in table_rows:
        model_display = row["model"] if current_model != row["model"] else ""
        current_model = row["model"]

        # Build status: format is "X/Y" with color based on failures/valid status
        valid_icon = "✓" if row["is_valid"] else "✗"
        status_text = f"{row['success_rate']} {valid_icon}"

        # Color red if failures exist or validation failed
        if row["has_failures"] or not row["is_valid"]:
            status_display = f"[red]{status_text}[/red]"
        else:
            status_display = f"[green]{status_text}[/green]"

        table.add_row(
            str(model_display),
            str(row["agent"]),
            f"{row['avg_time']:.2f}",
            format_optional_metric(row["cpu"], "%"),
            format_optional_metric(row["ram"], " MB"),
            format_optional_metric(row["gpu"], "%"),
            format_optional_metric(row["vram"], " MB"),
            status_display,
        )

    console.print(table)

    # Overall statistics with Rich Panel
    console.print()
    all_times: list[float] = []
    all_cpu: list[float] = []
    all_ram: list[float] = []
    all_gpu: list[float] = []
    all_vram: list[float] = []
    for agent_results in all_results.values():
        for model_stats in agent_results.values():
            all_times.append(model_stats.get("avg_time_ms", model_stats.get("total_time_ms", 0)))
            if model_stats.get("cpu_max") is not None:
                all_cpu.append(model_stats["cpu_max"])
            if model_stats.get("ram_max_mb") is not None:
                all_ram.append(model_stats["ram_max_mb"])
            if model_stats.get("gpu_util_max") is not None:
                all_gpu.append(model_stats["gpu_util_max"])
            if model_stats.get("vram_max_mb") is not None:
                all_vram.append(model_stats["vram_max_mb"])

    if all_times:
        stats_text = (
            f"[bold]Overall Statistics:[/bold]\n"
            f"  Total tests: {len(table_rows)}\n"
            f"  Average latency: {statistics.mean(all_times):.2f}ms\n"
            f"  Min latency: {min(all_times):.2f}ms\n"
            f"  Max latency: {max(all_times):.2f}ms"
        )
        if all_cpu:
            stats_text += f"\n  Peak CPU: {max(all_cpu):.2f}%"
        if all_ram:
            stats_text += f"\n  Peak RAM: {max(all_ram):.2f} MB"
        if all_gpu:
            stats_text += f"\n  Peak GPU: {max(all_gpu):.2f}%"
        if all_vram:
            stats_text += f"\n  Peak VRAM: {max(all_vram):.2f} MB"
        stats_panel = Panel(
            stats_text,
            title="[bold green]📊 Statistics[/bold green]",
            border_style="green",
        )
        console.print(stats_panel)
