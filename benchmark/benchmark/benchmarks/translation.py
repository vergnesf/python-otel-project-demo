"""Translation agent benchmark."""

import logging
import statistics
from benchmark.agents.translation import TranslationBenchmark
from benchmark.config import BENCHMARK_MODELS, BENCHMARK_TIMEOUT, NUM_TEST_REQUESTS, TRANSLATION_URL
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


async def benchmark_translation_agent() -> dict:
    """Benchmark translation agent."""
    print_section_header("Translation Agent Benchmarks")

    available = await check_service_available(TRANSLATION_URL)
    if not available:
        logger.warning("Translation agent service not available, skipping")
        return {}

    results_by_model = {}
    benchmark = TranslationBenchmark(TRANSLATION_URL, timeout=BENCHMARK_TIMEOUT)
    
    try:
        for model in BENCHMARK_MODELS:
            print_model_header(model)
            
            # 2 different test inputs
            translation_inputs = [
                "Bonjour, comment allez-vous?",
                "Je suis très heureux de vous rencontrer",
            ]
            
            tracker = start_resource_tracker()
            timings = []
            all_results = []
            validation_failed = False
            valid_tests = 0
            total_expected = len(translation_inputs) * NUM_TEST_REQUESTS
            
            try:
                # Execute each input NUM_TEST_REQUESTS times for consistency checking
                results = []
                for text in translation_inputs:
                    results.extend(
                        await benchmark.benchmark_translate(
                            model=model,
                            text=text,
                            num_requests=NUM_TEST_REQUESTS,
                        )
                    )
                
                # Display request/response details
                print_endpoint_header("Translate endpoint", f"{len(translation_inputs)} tests × {NUM_TEST_REQUESTS} runs = {total_expected} total")
                for i, result in enumerate(results, 1):
                    if result.get("success", False):
                        print_request_result(i, result['latency_ms'], True)
                        # Show request (input only)
                        if result.get("request"):
                            input_text = extract_query(result["request"])
                            print_query(input_text)
                            print_expected("Translation: target language version of the input text")
                        # Show response
                        if result.get("response"):
                            print_response(result["response"])
                            is_valid, validation_msg = validate_agent_response(
                                "translation", result["response"]
                            )
                            print_validation(is_valid, validation_msg)
                            if is_valid:
                                valid_tests += 1
                            else:
                                validation_failed = True
                        timings.append(result['latency_ms'])
                        all_results.append(result)
                    else:
                        print_request_result(i, 0, False, result.get('error', 'Unknown'))
                        if result.get("request"):
                            input_text = extract_query(result["request"])
                            print_query(input_text)
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
                "success_rate": f"{valid_tests}/{total_expected}",
                "is_valid": not validation_failed,
            }
            
    finally:
        await benchmark.close()
    
    return results_by_model
