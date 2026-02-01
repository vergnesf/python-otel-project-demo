"""Rich UI helpers for benchmark output."""

from __future__ import annotations

import json

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from benchmark.resources import format_optional_metric

console = Console(record=True)


def print_section_header(title: str) -> None:
    """Print a section header using Rich Panel."""
    console.print()
    console.print(Panel(f"[bold cyan]{title}[/bold cyan]", box=box.DOUBLE))


def print_model_header(model: str) -> None:
    """Print model being benchmarked."""
    console.print(f"\n[bold yellow]🔬 Benchmarking model:[/bold yellow] [bold]{model}[/bold]")


def print_endpoint_header(endpoint: str, num_requests: int) -> None:
    """Print endpoint being tested."""
    console.print(f"\n[bold blue]📊 {endpoint} ({num_requests} requests):[/bold blue]")


def print_request_result(
    request_num: int, latency_ms: float, success: bool, error: str | None = None
) -> None:
    """Print request result with status indicator."""
    if success:
        console.print(
            f"  [dim]Request {request_num}:[/dim] {latency_ms:.2f}ms [green]✓[/green]"
        )
    else:
        console.print(
            f"  [dim]Request {request_num}:[/dim] [red]✗ FAILED[/red] - {error or 'Unknown'}"
        )


def print_query(query: str) -> None:
    """Print the query sent."""
    console.print(f"    [cyan]→ Query sent:[/cyan] [italic]{query}[/italic]")


def _format_json(data: dict, max_length: int = 1000) -> str:
    """Format JSON for display with truncation."""
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    if len(json_str) > max_length:
        return json_str[:max_length] + "..."
    return json_str


def print_response(response: dict, max_length: int = 1000) -> None:
    """Print the response received with syntax highlighting."""
    response_str = _format_json(response, max_length)
    syntax = Syntax(response_str, "json", theme="monokai", line_numbers=False)
    console.print("    [magenta]← Response received:[/magenta]")
    console.print(syntax)


def print_expected(expected: str) -> None:
    """Print what is expected from this request."""
    console.print(f"    [green]✓ Expected:[/green] [dim]{expected}[/dim]")


def print_validation(is_valid: bool, message: str) -> None:
    """Print validation result for a response."""
    if is_valid:
        console.print(f"    [green]✓ Validation:[/green] [dim]{message}[/dim]")
    else:
        console.print(f"    [red]✗ Validation:[/red] [dim]{message}[/dim]")


def print_consistency(is_consistent: bool, message: str) -> None:
    """Print consistency check result."""
    if is_consistent:
        console.print(f"  [green]Consistency: {message}[/green]")
    else:
        console.print(f"  [yellow]Consistency: {message}[/yellow]")


def print_summary(
    total_time: float,
    avg_time: float,
    success_rate: str,
    cpu_max: float,
    ram_max_mb: float,
    gpu_util_max: float | None,
    vram_max_mb: float | None,
) -> None:
    """Print summary stats for a model."""
    console.print()
    console.print("[bold green]Summary:[/bold green]")
    console.print(f"  Total time: {total_time:.2f}ms")
    console.print(f"  Avg time: {avg_time:.2f}ms")
    console.print(f"  CPU max: {cpu_max:.2f}%")
    console.print(f"  RAM max: {ram_max_mb:.2f} MB")
    console.print(f"  GPU max: {format_optional_metric(gpu_util_max, '%')}")
    console.print(f"  VRAM max: {format_optional_metric(vram_max_mb, ' MB')}")
    console.print(f"  Success rate: {success_rate}")
