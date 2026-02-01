"""Traces agent benchmark."""

import logging
import statistics
from benchmark.agents.traces import TracesBenchmark
from benchmark.config import BENCHMARK_MODELS, BENCHMARK_TIMEOUT, NUM_TEST_REQUESTS, AGENT_TRACES_URL
from benchmark.resources import start_resource_tracker
from benchmark.ui import (
    console,
    print_endpoint_header,
    print_expected,
    print_model_header,
    print_query,
    print_request_result,
    print_response,
    print_section_header,
    print_summary,
    print_validation,
)
from benchmark.validation import validate_agent_response
from benchmark.benchmarks.base import (
    check_service_available,
    extract_query,
)

logger = logging.getLogger(__name__)


async def benchmark_traces_agent() -> dict:
    """Benchmark traces agent."""
    print_section_header("Traces Agent Benchmarks")

    available = await check_service_available(AGENT_TRACES_URL)
    if not available:
        logger.warning("Traces agent service not available, skipping")
        return {}

    results_by_model = {}
    benchmark = TracesBenchmark(AGENT_TRACES_URL, timeout=BENCHMARK_TIMEOUT)
    
    try:
        for model in BENCHMARK_MODELS:
            print_model_header(model)
            
            # 2 different test queries
            trace_queries = [
                {"service": None},  # All services
                {"service": "order-service"},  # Specific service
            ]
            
            tracker = start_resource_tracker()
            timings = []
            all_results = []
            validation_failed = False
            
            try:
                # Execute each query NUM_TEST_REQUESTS times for consistency checking
                results = []
                for query in trace_queries:
                    results.extend(
                        await benchmark.benchmark_analyze(
                            model=model,
                            query=query,
                            num_requests=NUM_TEST_REQUESTS,
                        )
                    )
                
                # Display request/response details
                total_expected = len(trace_queries) * NUM_TEST_REQUESTS
                print_endpoint_header("Analyze endpoint", f"{len(trace_queries)} tests × {NUM_TEST_REQUESTS} runs = {total_expected} total")
                for i, result in enumerate(results, 1):
                    if result.get("success", False):
                        print_request_result(i, result['latency_ms'], True)
                        # Show request (query only)
                        if result.get("request"):
                            query = extract_query(result["request"])
                            print_query(query)
                            print_expected("Traces analysis: summary of distributed traces, service interactions, latencies, errors, and critical paths")
                        # Show response
                        if result.get("response"):
                            print_response(result["response"])
                            is_valid, validation_msg = validate_agent_response(
                                "traces", result["response"]
                            )
                            print_validation(is_valid, validation_msg)
                            if not is_valid:
                                validation_failed = True
                        timings.append(result['latency_ms'])
                        all_results.append(result)
                    else:
                        print_request_result(i, 0, False, result.get('error', 'Unknown'))
                        if result.get("request"):
                            query = extract_query(result["request"])
                            print_query(query)
                    tracker.sample()
                
                if not all_results:
                    console.print(f"[red]✗ {model}: All requests failed[/red]")
                    results_by_model[model] = {
                        "total_time_ms": 0,
                        "avg_time_ms": 0,
                        "cpu_max": tracker.cpu_max,
                        "ram_max_mb": tracker.ram_max_mb,
                        "gpu_util_max": tracker.gpu_util_max,
                        "vram_max_mb": tracker.vram_max_mb,
                        "success_rate": f"0/{total_expected}",
                        "is_valid": False,
                    }
                    continue
                    
            except Exception as e:
                console.print(f"[red]✗ {model}: {e}[/red]")
                results_by_model[model] = {
                    "total_time_ms": 0,
                    "avg_time_ms": 0,
                    "cpu_max": tracker.cpu_max,
                    "ram_max_mb": tracker.ram_max_mb,
                    "gpu_util_max": tracker.gpu_util_max,
                    "vram_max_mb": tracker.vram_max_mb,
                    "success_rate": f"0/{total_expected}",
                }
                continue
            
            total_time = sum(timings)
            avg_time = statistics.mean(timings) if timings else 0
            
            # Stop continuous sampling
            tracker.stop_continuous_sampling()
            
            print_summary(
                total_time,
                avg_time,
                f"{len(all_results)}/{total_expected}",
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
                "success_rate": f"{len(all_results)}/{total_expected}",
                "is_valid": not validation_failed,
            }
            
    finally:
        await benchmark.close()
    
    return results_by_model
