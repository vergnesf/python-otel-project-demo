#!/usr/bin/env python3
"""Benchmark runner for agent APIs."""

import asyncio
import json
import logging
import statistics
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import httpx
import psutil
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import box

try:
    import pynvml  # type: ignore

    _NVML_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    pynvml = None
    _NVML_AVAILABLE = False

_NVML_INITIALIZED = False

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
    NUM_TEST_REQUESTS,
    ORCHESTRATOR_URL,
    TRANSLATION_URL,
)

# Configure logging (only for errors/warnings)
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Rich console for beautiful output
console = Console(record=True)  # record=True enables HTML export


def _print_section_header(title: str):
    """Print a section header using Rich Panel."""
    console.print()
    console.print(Panel(f"[bold cyan]{title}[/bold cyan]", box=box.DOUBLE))


def _print_model_header(model: str):
    """Print model being benchmarked."""
    console.print(f"\n[bold yellow]🔬 Benchmarking model:[/bold yellow] [bold]{model}[/bold]")


def _print_endpoint_header(endpoint: str, num_requests: int):
    """Print endpoint being tested."""
    console.print(f"\n[bold blue]📊 {endpoint} ({num_requests} requests):[/bold blue]")


def _print_request_result(request_num: int, latency_ms: float, success: bool, error: str = None):
    """Print request result with status indicator."""
    if success:
        console.print(f"  [dim]Request {request_num}:[/dim] {latency_ms:.2f}ms [green]✓[/green]")
    else:
        console.print(f"  [dim]Request {request_num}:[/dim] [red]✗ FAILED[/red] - {error or 'Unknown'}")


def _print_query(query: str):
    """Print the query sent."""
    console.print(f"    [cyan]→ Query sent:[/cyan] [italic]{query}[/italic]")


def _print_response(response: dict, max_length: int = 1000):
    """Print the response received with syntax highlighting."""
    response_str = _format_json(response, max_length)
    syntax = Syntax(response_str, "json", theme="monokai", line_numbers=False)
    console.print("    [magenta]← Response received:[/magenta]")
    console.print(syntax)


def _print_expected(expected: str):
    """Print what is expected from this request."""
    console.print(f"    [green]✓ Expected:[/green] [dim]{expected}[/dim]")


def _print_consistency(is_consistent: bool, message: str):
    """Print consistency check result."""
    if is_consistent:
        console.print(f"  [green]Consistency: {message}[/green]")
    else:
        console.print(f"  [yellow]Consistency: {message}[/yellow]")


def _format_optional_metric(value: float | None, unit: str) -> str:
    """Format optional metric value with unit."""
    if value is None:
        return "N/A"
    return f"{value:.2f}{unit}"


def _print_summary(
    total_time: float,
    avg_time: float,
    success_rate: str,
    cpu_max: float,
    ram_max_mb: float,
    gpu_util_max: float | None,
    vram_max_mb: float | None,
):
    """Print summary stats for a model."""
    console.print()
    console.print("[bold green]Summary:[/bold green]")
    console.print(f"  Total time: {total_time:.2f}ms")
    console.print(f"  Avg time: {avg_time:.2f}ms")
    console.print(f"  CPU max: {cpu_max:.2f}%")
    console.print(f"  RAM max: {ram_max_mb:.2f} MB")
    console.print(f"  GPU max: {_format_optional_metric(gpu_util_max, '%')}")
    console.print(f"  VRAM max: {_format_optional_metric(vram_max_mb, ' MB')}")
    console.print(f"  Success rate: {success_rate}")


def load_model_configs():
    """Load model configurations from config/ai/model-params.yml"""
    config_file = Path(__file__).parent.parent.parent / "config" / "ai" / "model-params.yml"
    try:
        with open(config_file, "r") as f:
            config_data = yaml.safe_load(f)

        model_configs = {}
        models_section = config_data.get("models", {})

        for model_name, model_data in models_section.items():
            context_size = model_data.get("context_size", "N/A")
            temperature = model_data.get("temperature", 0.1)
            top_k = model_data.get("top_k")
            max_tokens = model_data.get("max_tokens", 2000)
            model_configs[model_name] = {
                "context_size": context_size,
                "temperature": temperature,
                "top_k": top_k,
                "max_tokens": max_tokens,
            }

        return model_configs
    except Exception as e:
        logger.warning(f"Could not load model configs: {e}")
        return {}


MODEL_CONFIGS = load_model_configs()


def _init_nvml() -> bool:
    """Initialize NVML if available."""
    global _NVML_INITIALIZED
    if not _NVML_AVAILABLE or pynvml is None:
        return False
    if _NVML_INITIALIZED:
        return True
    try:
        pynvml.nvmlInit()
        _NVML_INITIALIZED = True
        return True
    except Exception:
        return False


def _get_gpu_metrics() -> dict | None:
    """Return GPU utilization and memory usage for the first GPU."""
    if not _init_nvml() or pynvml is None:
        return None
    try:
        device_count = pynvml.nvmlDeviceGetCount()
        if device_count == 0:
            return None
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        return {
            "gpu_util": float(util.gpu),
            "vram_used_mb": float(mem.used) / (1024 * 1024),
            "vram_total_mb": float(mem.total) / (1024 * 1024),
        }
    except Exception:
        return None


@dataclass
class ResourceTracker:
    """Track peak resource usage during a benchmark run."""

    process: psutil.Process
    cpu_max: float = 0.0
    ram_max_mb: float = 0.0
    gpu_util_max: float | None = None
    vram_max_mb: float | None = None

    def sample(self) -> None:
        """Sample current resource usage and update peaks."""
        cpu = self.process.cpu_percent(interval=None)
        ram_mb = self.process.memory_info().rss / (1024 * 1024)
        self.cpu_max = max(self.cpu_max, cpu)
        self.ram_max_mb = max(self.ram_max_mb, ram_mb)

        gpu_metrics = _get_gpu_metrics()
        if gpu_metrics is not None:
            util = gpu_metrics.get("gpu_util")
            vram_mb = gpu_metrics.get("vram_used_mb")
            if util is not None:
                self.gpu_util_max = util if self.gpu_util_max is None else max(self.gpu_util_max, util)
            if vram_mb is not None:
                self.vram_max_mb = vram_mb if self.vram_max_mb is None else max(self.vram_max_mb, vram_mb)


def _start_resource_tracker() -> ResourceTracker:
    """Create a resource tracker and prime CPU measurement."""
    process = psutil.Process()
    process.cpu_percent(interval=None)
    return ResourceTracker(process=process)


def _format_json(data: dict, max_length: int = 1000) -> str:
    """Format JSON for display with truncation."""
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    if len(json_str) > max_length:
        return json_str[:max_length] + "..."
    return json_str


def _extract_query(request: dict) -> str:
    """Extract just the query from a request for simplified display."""
    if "query" in request:
        return request["query"]
    return str(request)


def _validate_response_consistency(responses: list[dict]) -> tuple[bool, str]:
    """Validate that responses are consistent across multiple requests.
    
    Returns:
        Tuple of (is_consistent, message)
    """
    if len(responses) < 2:
        return True, "Single request"
    
    # Check that all responses have similar structure
    successful = [r for r in responses if r.get("success", False)]
    if len(successful) != len(responses):
        return False, f"Only {len(successful)}/{len(responses)} requests succeeded"
    
    # Check response times are within reasonable variance (coefficient of variation < 50%)
    latencies = [r["latency_ms"] for r in responses]
    if len(latencies) > 1:
        mean_lat = statistics.mean(latencies)
        stdev_lat = statistics.stdev(latencies)
        cv = (stdev_lat / mean_lat) * 100 if mean_lat > 0 else 0
        
        if cv > 50:
            return False, f"High latency variance (CV={cv:.1f}%)"
    
    return True, "Consistent"


async def check_service_available(url: str, timeout: float = 5.0) -> bool:
    """Check if a service is available via health check."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{url}/health")
            return response.status_code == 200
    except Exception as e:
        logger.warning(f"Service {url} not available: {e}")
        return False


async def benchmark_orchestrator() -> dict:
    """Benchmark orchestrator agent."""
    _print_section_header("Orchestrator Agent Benchmarks")

    available = await check_service_available(ORCHESTRATOR_URL)
    if not available:
        logger.warning("Orchestrator service not available, skipping")
        return {}

    results_by_model = {}
    benchmark = OrchestratorBenchmark(ORCHESTRATOR_URL, timeout=BENCHMARK_TIMEOUT)
    
    try:
        for model in BENCHMARK_MODELS:
            model_config = MODEL_CONFIGS.get(model, {})
            temperature = model_config.get("temperature", 0.7)
            
            _print_model_header(model)
            
            tracker = _start_resource_tracker()
            timings = []
            all_results = []
            
            try:
                # Test: Analyze with multiple requests
                start = time.perf_counter()
                results = await benchmark.benchmark_analyze(
                    model=model, 
                    temperature=temperature,
                    num_requests=NUM_TEST_REQUESTS
                )
                duration = time.perf_counter() - start
                
                # Display request/response details
                _print_endpoint_header("Analyze endpoint", NUM_TEST_REQUESTS)
                for i, result in enumerate(results, 1):
                    if result.get("success", False):
                        _print_request_result(i, result['latency_ms'], True)
                        # Show request (query only)
                        if result.get("request"):
                            query = _extract_query(result["request"])
                            _print_query(query)
                            _print_expected("Translated query + routing to relevant agents (logs/metrics/traces) + aggregated responses from selected agents")
                        # Show response
                        if result.get("response"):
                            _print_response(result["response"])
                        timings.append(result['latency_ms'])
                        all_results.append(result)
                    else:
                        _print_request_result(i, 0, False, result.get('error', 'Unknown'))
                        if result.get("request"):
                            query = _extract_query(result["request"])
                            _print_query(query)
                    tracker.sample()
                
                # Validate consistency
                is_consistent, consistency_msg = _validate_response_consistency(all_results)
                _print_consistency(is_consistent, consistency_msg)
                
                if not all_results:
                    console.print(f"[red]✗ {model}: All requests failed[/red]")
                    # Store failed result for summary table
                    results_by_model[model] = {
                        "total_time_ms": 0,
                        "avg_time_ms": 0,
                        "cpu_max": tracker.cpu_max,
                        "ram_max_mb": tracker.ram_max_mb,
                        "gpu_util_max": tracker.gpu_util_max,
                        "vram_max_mb": tracker.vram_max_mb,
                        "success_rate": "0/" + str(NUM_TEST_REQUESTS),
                        "is_consistent": False
                    }
                    continue
                    
            except Exception as e:
                console.print(f"[red]✗ {model}: {e}[/red]")
                # Store failed result for summary table
                results_by_model[model] = {
                    "total_time_ms": 0,
                    "avg_time_ms": 0,
                    "cpu_max": tracker.cpu_max,
                    "ram_max_mb": tracker.ram_max_mb,
                    "gpu_util_max": tracker.gpu_util_max,
                    "vram_max_mb": tracker.vram_max_mb,
                    "success_rate": "0/" + str(NUM_TEST_REQUESTS),
                    "is_consistent": False
                }
                continue
            
            # Calculate statistics
            total_time = sum(timings)
            avg_time = statistics.mean(timings)
            
            _print_summary(
                total_time,
                avg_time,
                f"{len(all_results)}/{NUM_TEST_REQUESTS}",
                tracker.cpu_max,
                tracker.ram_max_mb,
                tracker.gpu_util_max,
                tracker.vram_max_mb,
            )
            
            results_by_model[model] = {
                "total_time_ms": total_time,
                "avg_time_ms": avg_time,
                "cpu_max": tracker.cpu_max,
                "ram_max_mb": tracker.ram_max_mb,
                "gpu_util_max": tracker.gpu_util_max,
                "vram_max_mb": tracker.vram_max_mb,
                "timings": timings,
                "success_rate": f"{len(all_results)}/{NUM_TEST_REQUESTS}",
                "is_consistent": is_consistent,
            }
            
    finally:
        await benchmark.close()
    
    return results_by_model


async def benchmark_logs_agent() -> dict:
    """Benchmark logs agent."""
    _print_section_header("Logs Agent Benchmarks")

    available = await check_service_available(AGENT_LOGS_URL)
    if not available:
        logger.warning("Logs agent service not available, skipping")
        return {}

    results_by_model = {}
    benchmark = LogsBenchmark(AGENT_LOGS_URL, timeout=BENCHMARK_TIMEOUT)
    
    try:
        for model in BENCHMARK_MODELS:
            _print_model_header(model)
            
            tracker = _start_resource_tracker()
            timings = []
            all_results = []
            
            try:
                # Test: Analyze with multiple requests
                results = await benchmark.benchmark_analyze(model=model, num_requests=NUM_TEST_REQUESTS)
                
                # Display request/response details
                _print_endpoint_header("Analyze endpoint", NUM_TEST_REQUESTS)
                for i, result in enumerate(results, 1):
                    if result.get("success", False):
                        _print_request_result(i, result['latency_ms'], True)
                        # Show request (query only)
                        if result.get("request"):
                            query = _extract_query(result["request"])
                            _print_query(query)
                            _print_expected("Log analysis: summary of errors, affected services, error patterns, severity, insights, and recommendations")
                        # Show response
                        if result.get("response"):
                            _print_response(result["response"])
                        timings.append(result['latency_ms'])
                        all_results.append(result)
                    else:
                        _print_request_result(i, 0, False, result.get('error', 'Unknown'))
                        if result.get("request"):
                            query = _extract_query(result["request"])
                            _print_query(query)
                    tracker.sample()
                
                # Validate consistency
                is_consistent, consistency_msg = _validate_response_consistency(all_results)
                _print_consistency(is_consistent, consistency_msg)
                
                if not all_results:
                    console.print(f"[red]✗ {model}: All requests failed[/red]")
                    # Store failed result for summary table
                    results_by_model[model] = {
                        "total_time_ms": 0,
                        "avg_time_ms": 0,
                        "cpu_max": tracker.cpu_max,
                        "ram_max_mb": tracker.ram_max_mb,
                        "gpu_util_max": tracker.gpu_util_max,
                        "vram_max_mb": tracker.vram_max_mb,
                        "success_rate": "0/" + str(NUM_TEST_REQUESTS),
                        "is_consistent": False
                    }
                    continue
                    
            except Exception as e:
                console.print(f"[red]✗ {model}: {e}[/red]")
                # Store failed result for summary table
                results_by_model[model] = {
                    "total_time_ms": 0,
                    "avg_time_ms": 0,
                    "cpu_max": tracker.cpu_max,
                    "ram_max_mb": tracker.ram_max_mb,
                    "gpu_util_max": tracker.gpu_util_max,
                    "vram_max_mb": tracker.vram_max_mb,
                    "success_rate": "0/" + str(NUM_TEST_REQUESTS),
                    "is_consistent": False
                }
                continue
            
            total_time = sum(timings)
            avg_time = statistics.mean(timings)
            
            _print_summary(
                total_time,
                avg_time,
                f"{len(all_results)}/{NUM_TEST_REQUESTS}",
                tracker.cpu_max,
                tracker.ram_max_mb,
                tracker.gpu_util_max,
                tracker.vram_max_mb,
            )
            
            results_by_model[model] = {
                "total_time_ms": total_time,
                "avg_time_ms": avg_time,
                "cpu_max": tracker.cpu_max,
                "ram_max_mb": tracker.ram_max_mb,
                "gpu_util_max": tracker.gpu_util_max,
                "vram_max_mb": tracker.vram_max_mb,
                "success_rate": f"{len(all_results)}/{NUM_TEST_REQUESTS}",
                "is_consistent": is_consistent,
            }
            
    finally:
        await benchmark.close()
    
    return results_by_model


async def benchmark_metrics_agent() -> dict:
    """Benchmark metrics agent."""
    _print_section_header("Metrics Agent Benchmarks")

    available = await check_service_available(AGENT_METRICS_URL)
    if not available:
        logger.warning("Metrics agent service not available, skipping")
        return {}

    results_by_model = {}
    benchmark = MetricsBenchmark(AGENT_METRICS_URL, timeout=BENCHMARK_TIMEOUT)
    
    try:
        for model in BENCHMARK_MODELS:
            _print_model_header(model)
            
            tracker = _start_resource_tracker()
            timings = []
            all_results = []
            
            try:
                results = await benchmark.benchmark_analyze(model=model, num_requests=NUM_TEST_REQUESTS)
                
                _print_endpoint_header("Analyze endpoint", NUM_TEST_REQUESTS)
                for i, result in enumerate(results, 1):
                    if result.get("success", False):
                        _print_request_result(i, result['latency_ms'], True)
                        # Show request (query only)
                        if result.get("request"):
                            query = _extract_query(result["request"])
                            _print_query(query)
                            _print_expected("Metrics analysis: CPU/memory usage, error rate, request rate, latency p95 with threshold checks and anomaly detection")
                        # Show response
                        if result.get("response"):
                            _print_response(result["response"])
                        timings.append(result['latency_ms'])
                        all_results.append(result)
                    else:
                        _print_request_result(i, 0, False, result.get('error', 'Unknown'))
                        if result.get("request"):
                            query = _extract_query(result["request"])
                            _print_query(query)
                    tracker.sample()
                
                is_consistent, consistency_msg = _validate_response_consistency(all_results)
                _print_consistency(is_consistent, consistency_msg)
                
                if not all_results:
                    console.print(f"[red]✗ {model}: All requests failed[/red]")
                    # Store failed result for summary table
                    results_by_model[model] = {
                        "total_time_ms": 0,
                        "avg_time_ms": 0,
                        "cpu_max": tracker.cpu_max,
                        "ram_max_mb": tracker.ram_max_mb,
                        "gpu_util_max": tracker.gpu_util_max,
                        "vram_max_mb": tracker.vram_max_mb,
                        "success_rate": "0/" + str(NUM_TEST_REQUESTS),
                        "is_consistent": False
                    }
                    continue
            except Exception as e:
                console.print(f"[red]✗ {model}: {e}[/red]")
                # Store failed result for summary table
                results_by_model[model] = {
                    "total_time_ms": 0,
                    "avg_time_ms": 0,
                    "cpu_max": tracker.cpu_max,
                    "ram_max_mb": tracker.ram_max_mb,
                    "gpu_util_max": tracker.gpu_util_max,
                    "vram_max_mb": tracker.vram_max_mb,
                    "success_rate": "0/" + str(NUM_TEST_REQUESTS),
                    "is_consistent": False
                }
                continue
            
            total_time = sum(timings)
            avg_time = statistics.mean(timings)
            
            _print_summary(
                total_time,
                avg_time,
                f"{len(all_results)}/{NUM_TEST_REQUESTS}",
                tracker.cpu_max,
                tracker.ram_max_mb,
                tracker.gpu_util_max,
                tracker.vram_max_mb,
            )
            
            results_by_model[model] = {
                "total_time_ms": total_time,
                "avg_time_ms": avg_time,
                "cpu_max": tracker.cpu_max,
                "ram_max_mb": tracker.ram_max_mb,
                "gpu_util_max": tracker.gpu_util_max,
                "vram_max_mb": tracker.vram_max_mb,
                "success_rate": f"{len(all_results)}/{NUM_TEST_REQUESTS}",
                "is_consistent": is_consistent,
            }
            
    finally:
        await benchmark.close()
    
    return results_by_model


async def benchmark_traces_agent() -> dict:
    """Benchmark traces agent."""
    _print_section_header("Traces Agent Benchmarks")

    available = await check_service_available(AGENT_TRACES_URL)
    if not available:
        logger.warning("Traces agent service not available, skipping")
        return {}

    results_by_model = {}
    benchmark = TracesBenchmark(AGENT_TRACES_URL, timeout=BENCHMARK_TIMEOUT)
    
    try:
        for model in BENCHMARK_MODELS:
            _print_model_header(model)
            
            tracker = _start_resource_tracker()
            timings = []
            all_results = []
            
            try:
                results = await benchmark.benchmark_analyze(model=model, num_requests=NUM_TEST_REQUESTS)
                
                _print_endpoint_header("Analyze endpoint", NUM_TEST_REQUESTS)
                for i, result in enumerate(results, 1):
                    if result.get("success", False):
                        _print_request_result(i, result['latency_ms'], True)
                        # Show request (query only)
                        if result.get("request"):
                            query = _extract_query(result["request"])
                            _print_query(query)
                            _print_expected("Trace analysis: total traces, slow/failed traces, bottlenecks, service dependencies, average duration")
                        # Show response
                        if result.get("response"):
                            _print_response(result["response"])
                        timings.append(result['latency_ms'])
                        all_results.append(result)
                    else:
                        _print_request_result(i, 0, False, result.get('error', 'Unknown'))
                        if result.get("request"):
                            query = _extract_query(result["request"])
                            _print_query(query)
                    tracker.sample()
                
                is_consistent, consistency_msg = _validate_response_consistency(all_results)
                _print_consistency(is_consistent, consistency_msg)
                
                if not all_results:
                    console.print(f"[red]✗ {model}: All requests failed[/red]")
                    # Store failed result for summary table
                    results_by_model[model] = {
                        "total_time_ms": 0,
                        "avg_time_ms": 0,
                        "cpu_max": tracker.cpu_max,
                        "ram_max_mb": tracker.ram_max_mb,
                        "gpu_util_max": tracker.gpu_util_max,
                        "vram_max_mb": tracker.vram_max_mb,
                        "success_rate": "0/" + str(NUM_TEST_REQUESTS),
                        "is_consistent": False
                    }
                    continue
            except Exception as e:
                console.print(f"[red]✗ {model}: {e}[/red]")
                # Store failed result for summary table
                results_by_model[model] = {
                    "total_time_ms": 0,
                    "avg_time_ms": 0,
                    "cpu_max": tracker.cpu_max,
                    "ram_max_mb": tracker.ram_max_mb,
                    "gpu_util_max": tracker.gpu_util_max,
                    "vram_max_mb": tracker.vram_max_mb,
                    "success_rate": "0/" + str(NUM_TEST_REQUESTS),
                    "is_consistent": False
                }
                continue
            
            total_time = sum(timings)
            avg_time = statistics.mean(timings)
            
            _print_summary(
                total_time,
                avg_time,
                f"{len(all_results)}/{NUM_TEST_REQUESTS}",
                tracker.cpu_max,
                tracker.ram_max_mb,
                tracker.gpu_util_max,
                tracker.vram_max_mb,
            )
            
            results_by_model[model] = {
                "total_time_ms": total_time,
                "avg_time_ms": avg_time,
                "cpu_max": tracker.cpu_max,
                "ram_max_mb": tracker.ram_max_mb,
                "gpu_util_max": tracker.gpu_util_max,
                "vram_max_mb": tracker.vram_max_mb,
                "success_rate": f"{len(all_results)}/{NUM_TEST_REQUESTS}",
                "is_consistent": is_consistent,
            }
            
    finally:
        await benchmark.close()
    
    return results_by_model


async def benchmark_translation_agent() -> dict:
    """Benchmark translation agent."""
    _print_section_header("Translation Agent Benchmarks")

    available = await check_service_available(TRANSLATION_URL)
    if not available:
        logger.warning("Translation agent service not available, skipping")
        return {}

    results_by_model = {}
    benchmark = TranslationBenchmark(TRANSLATION_URL, timeout=BENCHMARK_TIMEOUT)
    
    try:
        for model in BENCHMARK_MODELS:
            _print_model_header(model)
            
            tracker = _start_resource_tracker()
            timings = []
            all_results = []
            
            try:
                results = await benchmark.benchmark_translate(model=model, num_requests=NUM_TEST_REQUESTS)
                
                _print_endpoint_header("Translate endpoint", NUM_TEST_REQUESTS)
                for i, result in enumerate(results, 1):
                    if result.get("success", False):
                        _print_request_result(i, result['latency_ms'], True)
                        # Show request (query only)
                        if result.get("request"):
                            query = _extract_query(result["request"])
                            _print_query(query)
                            _print_expected("English translation with language='non-english' if input was French, or language='english' if already in English")
                        # Show response
                        if result.get("response"):
                            _print_response(result["response"])
                        timings.append(result['latency_ms'])
                        all_results.append(result)
                    else:
                        _print_request_result(i, 0, False, result.get('error', 'Unknown'))
                        if result.get("request"):
                            query = _extract_query(result["request"])
                            _print_query(query)
                    tracker.sample()
                
                is_consistent, consistency_msg = _validate_response_consistency(all_results)
                _print_consistency(is_consistent, consistency_msg)
                
                if not all_results:
                    console.print(f"[red]✗ {model}: All requests failed[/red]")
                    # Store failed result for summary table
                    results_by_model[model] = {
                        "total_time_ms": 0,
                        "avg_time_ms": 0,
                        "cpu_max": tracker.cpu_max,
                        "ram_max_mb": tracker.ram_max_mb,
                        "gpu_util_max": tracker.gpu_util_max,
                        "vram_max_mb": tracker.vram_max_mb,
                        "success_rate": "0/" + str(NUM_TEST_REQUESTS),
                        "is_consistent": False
                    }
                    continue
            except Exception as e:
                console.print(f"[red]✗ {model}: {e}[/red]")
                # Store failed result for summary table
                results_by_model[model] = {
                    "total_time_ms": 0,
                    "avg_time_ms": 0,
                    "cpu_max": tracker.cpu_max,
                    "ram_max_mb": tracker.ram_max_mb,
                    "gpu_util_max": tracker.gpu_util_max,
                    "vram_max_mb": tracker.vram_max_mb,
                    "success_rate": "0/" + str(NUM_TEST_REQUESTS),
                    "is_consistent": False
                }
                continue
            
            total_time = sum(timings)
            avg_time = statistics.mean(timings)
            
            _print_summary(
                total_time,
                avg_time,
                f"{len(all_results)}/{NUM_TEST_REQUESTS}",
                tracker.cpu_max,
                tracker.ram_max_mb,
                tracker.gpu_util_max,
                tracker.vram_max_mb,
            )
            
            results_by_model[model] = {
                "total_time_ms": total_time,
                "avg_time_ms": avg_time,
                "cpu_max": tracker.cpu_max,
                "ram_max_mb": tracker.ram_max_mb,
                "gpu_util_max": tracker.gpu_util_max,
                "vram_max_mb": tracker.vram_max_mb,
                "success_rate": f"{len(all_results)}/{NUM_TEST_REQUESTS}",
                "is_consistent": is_consistent,
            }
            
    finally:
        await benchmark.close()
    
    return results_by_model


async def main() -> None:
    """Run all benchmarks."""
    start_time = time.perf_counter()
    logger.info(f"Starting benchmarks at {datetime.now().isoformat()}")
    logger.info(f"Models: {', '.join(BENCHMARK_MODELS)}")
    logger.info(f"Test requests per model: {NUM_TEST_REQUESTS}")

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
    console.print(f"  Test requests per model: {NUM_TEST_REQUESTS}")
    
    # Create summary table (printed without logger)
    console.print()
    
    # Collect all data for table
    table_rows = []
    for model in BENCHMARK_MODELS:
        for agent_name in ["orchestrator", "logs", "metrics", "traces", "translation"]:
            results = all_results.get(agent_name, {})
            if model in results:
                stats = results[model]
                row = {
                    "model": model,
                    "agent": agent_name,
                    "avg_time": stats.get("avg_time_ms", stats.get("total_time_ms", 0)),
                    "cpu": stats.get("cpu_max"),
                    "ram": stats.get("ram_max_mb"),
                    "gpu": stats.get("gpu_util_max"),
                    "vram": stats.get("vram_max_mb"),
                    "success": stats.get("success_rate", "N/A"),
                    "consistent": "✓" if stats.get("is_consistent", True) else "✗",
                }
                table_rows.append(row)
    
    # Create Rich Table
    console.print()
    console.print("=" * 120)
    table = Table(title="[bold]BENCHMARK SUMMARY TABLE[/bold]", box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Model", style="yellow", width=20)
    table.add_column("Agent", style="cyan", width=15)
    table.add_column("Avg Time (ms)", justify="right", width=15)
    table.add_column("CPU %", justify="right", width=10)
    table.add_column("RAM MB", justify="right", width=12)
    table.add_column("GPU %", justify="right", width=10)
    table.add_column("VRAM MB", justify="right", width=12)
    table.add_column("Success", justify="center", width=10)
    table.add_column("Consistent", justify="center", width=10)
    
    # Add rows grouped by model
    current_model = None
    for row in table_rows:
        model_display = row["model"] if current_model != row["model"] else ""
        current_model = row["model"]
        
        consistent_display = f"[green]{row['consistent']}[/green]" if row["consistent"] == "✓" else f"[yellow]{row['consistent']}[/yellow]"
        
        table.add_row(
            model_display,
            row['agent'],
            f"{row['avg_time']:.2f}",
            _format_optional_metric(row['cpu'], "%"),
            _format_optional_metric(row['ram'], " MB"),
            _format_optional_metric(row['gpu'], "%"),
            _format_optional_metric(row['vram'], " MB"),
            row['success'],
            consistent_display
        )
    
    console.print(table)
    
    # Overall statistics with Rich Panel
    console.print()
    all_times = []
    all_cpu = []
    all_ram = []
    all_gpu = []
    all_vram = []
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
        stats_panel = Panel(stats_text, title="[bold green]📊 Statistics[/bold green]", border_style="green")
        console.print(stats_panel)
    
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
