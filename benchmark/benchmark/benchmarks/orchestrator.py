"""Orchestrator agent benchmark."""

import logging
import statistics
from benchmark.agents.orchestrator import OrchestratorBenchmark
from benchmark.config import BENCHMARK_MODELS, BENCHMARK_TIMEOUT, NUM_TEST_REQUESTS, ORCHESTRATOR_URL, MODEL_CONFIGS
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
from benchmark.validation import validate_orchestrator_response
from benchmark.benchmarks.base import (
    check_service_available,
    extract_query,
)

logger = logging.getLogger(__name__)


async def benchmark_orchestrator() -> dict:
    """Benchmark orchestrator agent."""
    print_section_header("Orchestrator Agent Benchmarks")

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
            
            print_model_header(model)
            
            queries = [
                "Analyze the system performance and provide insights",
                "Investigate latency spikes and error rates in the last hour",
            ]
            
            tracker = start_resource_tracker()
            timings = []
            all_results = []
            validation_failed = False
            
            try:
                # Test: Execute each query NUM_TEST_REQUESTS times for consistency
                results = []
                for query in queries:
                    results.extend(
                        await benchmark.benchmark_analyze(
                            model=model,
                            query=query,
                            temperature=temperature,
                            num_requests=NUM_TEST_REQUESTS,
                        )
                    )
                
                # Display request/response details
                print_endpoint_header("Analyze endpoint", f"{len(queries)} tests × {NUM_TEST_REQUESTS} iterations")
                for i, result in enumerate(results, 1):
                    if result.get("success", False):
                        print_request_result(i, result['latency_ms'], True)
                        # Show request (query only)
                        if result.get("request"):
                            query = extract_query(result["request"])
                            print_query(query)
                            print_expected("Translated query + routing to relevant agents (logs/metrics/traces) + aggregated responses from selected agents")
                        # Show response
                        if result.get("response"):
                            print_response(result["response"])
                            is_valid, validation_msg = validate_orchestrator_response(
                                result["response"]
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
                    # Store failed result for summary table
                    results_by_model[model] = {
                        "total_time_ms": 0,
                        "avg_time_ms": 0,
                        "cpu_max": tracker.cpu_max,
                        "ram_max_mb": tracker.ram_max_mb,
                        "gpu_util_max": tracker.gpu_util_max,
                        "vram_max_mb": tracker.vram_max_mb,
                        "success_rate": "0/" + str(len(queries) * NUM_TEST_REQUESTS),
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
                    "success_rate": "0/" + str(len(queries) * NUM_TEST_REQUESTS),
                }
                continue
            
            # Calculate statistics
            total_time = sum(timings)
            avg_time = statistics.mean(timings)
            
            print_summary(
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
                "success_rate": f"{len(all_results)}/{len(queries) * NUM_TEST_REQUESTS}",
                "is_valid": not validation_failed,
            }
            
    finally:
        await benchmark.close()
    
    return results_by_model
