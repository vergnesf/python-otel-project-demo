"""Orchestrator agent benchmark."""

import logging
import statistics
from benchmark.agents.orchestrator import OrchestratorBenchmark
import benchmark.config
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
from benchmark.validation import validate_orchestrator_response, validate_routing, validate_model_in_response
from benchmark.benchmarks.base import (
    check_service_available,
    extract_query,
)

logger = logging.getLogger(__name__)


async def benchmark_orchestrator() -> dict:
    """Benchmark orchestrator agent."""
    print_section_header("Orchestrator Agent Benchmarks")

    available = await check_service_available(benchmark.config.ORCHESTRATOR_URL)
    if not available:
        logger.warning("Orchestrator service not available, skipping")
        return {}

    results_by_model = {}
    benchmark_agent = OrchestratorBenchmark(benchmark.config.ORCHESTRATOR_URL, timeout=benchmark.config.BENCHMARK_TIMEOUT)
    
    try:
        for model in benchmark.config.BENCHMARK_MODELS:
            model_config = benchmark.config.MODEL_CONFIGS.get(model, {})
            temperature = model_config.get("temperature", 0.7)
            
            print_model_header(model)
            
            # Test routing to different agents
            queries = [
                # LOGS routing - specific error queries
                "Show me the 5 most recent errors and exceptions",
                # METRICS routing - performance questions
                "What are the CPU and memory usage across all services?",
                # TRACES routing - request flow questions
                "Show me the slowest requests in the last hour",
                # COMBINED - requires multiple agents
                "Analyze system performance, errors, and request latencies",
            ]
            
            tracker = start_resource_tracker()
            timings = []
            all_results = []
            validation_failed = False
            valid_tests = 0
            total_expected = len(queries) * benchmark.config.NUM_TEST_REQUESTS
            
            try:
                # Test: Execute each query benchmark.config.NUM_TEST_REQUESTS times for consistency
                results = []
                for query in queries:
                    results.extend(
                        await benchmark_agent.benchmark_analyze(
                            model=model,
                            query=query,
                            temperature=temperature,
                            num_requests=benchmark.config.NUM_TEST_REQUESTS,
                        )
                    )
                
                # Display request/response details
                print_endpoint_header("Analyze endpoint", f"{len(queries)} tests × {benchmark.config.NUM_TEST_REQUESTS} iterations = {total_expected} total")
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
                            # Also check model
                            model_valid, model_msg = validate_model_in_response(
                                result["response"], model
                            )
                            print_validation(model_valid, f"model: {model_msg}")
                            # Also validate routing
                            routing_valid = True
                            if is_valid and result.get("request"):
                                routing_valid, routing_msg = validate_routing(
                                    result["response"], 
                                    extract_query(result["request"])
                                )
                                print_validation(routing_valid, f"routing: {routing_msg}")
                            # Count as valid only if both structure and routing are valid
                            if is_valid and routing_valid:
                                valid_tests += 1
                            else:
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
                        "success_rate": f"0/{total_expected}",
                        "is_valid": False,
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
                    "success_rate": f"0/{total_expected}",
                }
                continue
            
            # Calculate statistics
            total_time = sum(timings)
            avg_time = statistics.mean(timings)
            
            # Stop continuous sampling
            tracker.stop_continuous_sampling()
            
            print_summary(
                total_time,
                avg_time,
                f"{valid_tests}/{total_expected}",
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
                "success_rate": f"{valid_tests}/{total_expected}",
                "is_valid": not validation_failed,
            }
            
    finally:
        await benchmark_agent.close()
    
    return results_by_model
