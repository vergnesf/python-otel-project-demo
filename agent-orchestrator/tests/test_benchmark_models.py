#!/usr/bin/env python3
"""
Benchmark tests for different AI models
"""

import pytest
import time
import psutil
import statistics
import asyncio
import os
import threading
import subprocess
from pathlib import Path
import yaml
from tests.test_orchestrator_integration import (
    run_agent_routing,
    run_response_validation,
    run_complete_workflow,
    check_orchestrator_available,
    list_available_models,
    Colors,
    BASE_URL,
    TIMEOUT,
)
from common_ai import get_model_params, unload_ollama_model

MODELS = [
    "mistral:7b",
    "llama3.2:3b",
    "qwen3:0.6b",
    "granite4:3b",
    "mistral-nemo:12b",
    "qwen2.5:7b",
    "phi4:14b",
]


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
            model_configs[model_name] = {"context_size": context_size}

        return model_configs
    except Exception as e:
        print(
            f"{Colors.YELLOW}⚠️  Could not load model configs from config/ai/model-params.yml: {e}{Colors.END}"
        )
        return {}


MODEL_CONFIGS = load_model_configs()








class ResourceMonitor:
    def __init__(self, interval=0.5):
        self.interval = interval
        self.running = False
        self.thread = None
        self.cpu_readings = []
        self.gpu_util_readings = []
        self.gpu_mem_readings = []
        self.gpu_name = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        return self.get_stats()

    def _monitor_loop(self):
        # Get GPU name once
        if self.gpu_name is None:
            try:
                result = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=name",
                        "--format=csv,noheader",
                    ],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    self.gpu_name = result.stdout.strip().split("\n")[0].strip()
            except Exception:
                self.gpu_name = "Unknown"

        while self.running:
            # CPU
            self.cpu_readings.append(psutil.cpu_percent(interval=None))

            # GPU
            try:
                result = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=utilization.gpu,memory.used",
                        "--format=csv,noheader,nounits",
                    ],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    # Output format: "3, 5439" (util %, mem MiB)
                    lines = result.stdout.strip().split("\n")
                    utils = []
                    mems = []
                    for line in lines:
                        if "," in line:
                            u, m = line.split(",")
                            utils.append(float(u.strip()))
                            mems.append(float(m.strip()))

                    if utils:
                        self.gpu_util_readings.append(max(utils))
                        self.gpu_mem_readings.append(max(mems))
            except Exception:
                pass

            time.sleep(self.interval)

    def get_stats(self):
        return {
            "cpu_avg": (statistics.mean(self.cpu_readings) if self.cpu_readings else 0),
            "cpu_max": max(self.cpu_readings) if self.cpu_readings else 0,
            "gpu_util_avg": (
                statistics.mean(self.gpu_util_readings) if self.gpu_util_readings else 0
            ),
            "gpu_util_max": (
                max(self.gpu_util_readings) if self.gpu_util_readings else 0
            ),
            "gpu_mem_max": (max(self.gpu_mem_readings) if self.gpu_mem_readings else 0),
            "gpu_name": self.gpu_name if self.gpu_name else "Unknown",
        }


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.order(-1)  # Run last
async def test_benchmark_models():
    """Run benchmark for all configured AI models"""
    await check_orchestrator_available()

    print(f"\n{Colors.BOLD}╔{'=' * 78}╗{Colors.END}")
    print(f"{Colors.BOLD}║{' ' * 25}AI MODEL BENCHMARK{' ' * 33}║{Colors.END}")
    print(f"{Colors.BOLD}╚{'=' * 78}╝{Colors.END}")

    # Pre-check: Verify all models are available before starting
    print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Starting benchmark...{Colors.END}")

    results = {}
    available_models = await list_available_models()
    available_set = {name.lower() for name in available_models}

    for i, model in enumerate(MODELS):
        if model.lower() not in available_set:
            print(
                f"{Colors.YELLOW}⚠️  Skipping unavailable model: {model}{Colors.END}"
            )
            continue
        # Unload previous model before loading the next one
        if i > 0:
            print(f"\n{Colors.YELLOW}🔄 Unloading previous model to free GPU memory...{Colors.END}")
            await unload_ollama_model(MODELS[i-1])

        print(f"\n{Colors.BOLD}Testing Model: {Colors.BLUE}{model}{Colors.END}")
        
        # Get optimal parameters for this model
        params = get_model_params(model)
        print(f"{Colors.YELLOW}Using parameters: temp={params['temperature']}, top_k={params['top_k']}, max_tokens={params['max_tokens']}{Colors.END}")
        
        results[model] = {
            "test1_routing": "NOT_RUN",
            "test2_validation": "NOT_RUN",
            "test3_workflow": "NOT_RUN",
            "test1_warnings": [],
            "test2_warnings": [],
            "test3_warnings": [],
            "duration": 0,
            "stats": {},
        }

        monitor = ResourceMonitor()
        monitor.start()
        start_time_model = time.time()

        # Test 1: Agent Routing
        try:
            await run_agent_routing(model=model, strict=False, model_params=params)
            results[model]["test1_routing"] = "✓ OK"
            print(f"{Colors.GREEN}→ TEST 1 OK (no exceptions){Colors.END}")
        except AssertionError as e:
            results[model]["test1_routing"] = f"⚠️  {str(e)[:40]}"
            print(f"{Colors.YELLOW}⚠️  TEST 1 ASSERTION: {e}{Colors.END}")
        except Exception as e:
            results[model]["test1_routing"] = f"❌ {str(e)[:40]}"
            print(f"{Colors.RED}❌ TEST 1 ERROR: {e}{Colors.END}")

        # Test 2: Response Validation
        try:
            await run_response_validation(model=model, strict=False, model_params=params)
            results[model]["test2_validation"] = "✓ OK"
            print(f"{Colors.GREEN}→ TEST 2 OK (no exceptions){Colors.END}")
        except AssertionError as e:
            results[model]["test2_validation"] = f"⚠️  {str(e)[:40]}"
            print(f"{Colors.YELLOW}⚠️  TEST 2 ASSERTION: {e}{Colors.END}")
        except Exception as e:
            results[model]["test2_validation"] = f"❌ {str(e)[:40]}"
            print(f"{Colors.RED}❌ TEST 2 ERROR: {e}{Colors.END}")

        # Test 3: Complete Workflow
        try:
            await run_complete_workflow(model=model, strict=False, model_params=params)
            results[model]["test3_workflow"] = "✓ OK"
            print(f"{Colors.GREEN}→ TEST 3 OK (no exceptions){Colors.END}")
        except AssertionError as e:
            results[model]["test3_workflow"] = f"⚠️  {str(e)[:40]}"
            print(f"{Colors.YELLOW}⚠️  TEST 3 ASSERTION: {e}{Colors.END}")
        except Exception as e:
            results[model]["test3_workflow"] = f"❌ {str(e)[:40]}"
            print(f"{Colors.RED}❌ TEST 3 ERROR: {e}{Colors.END}")

        duration = time.time() - start_time_model
        stats = monitor.stop()

        results[model]["duration"] = duration
        results[model]["stats"] = stats

        print(f"{Colors.YELLOW}⏱️  Model duration: {duration:.2f}s{Colors.END}")
        print(
            f"{Colors.YELLOW}💻 CPU Avg: {stats['cpu_avg']:.1f}% (Max: {stats['cpu_max']:.1f}%){Colors.END}"
        )
        print(
            f"{Colors.YELLOW}🎮 GPU Avg: {stats['gpu_util_avg']:.1f}% (Max: {stats['gpu_util_max']:.1f}%){Colors.END}"
        )
        print(
            f"{Colors.YELLOW}🧠 GPU Mem Max: {stats['gpu_mem_max']:.0f} MiB{Colors.END}"
        )

        # Unload model after tests complete to free GPU memory
        if i < len(MODELS) - 1:  # Don't unload after the last model
            await asyncio.sleep(1)
            await unload_ollama_model(model)

    # Print Summary
    print(f"\n{Colors.BOLD}╔{'=' * 190}╗{Colors.END}")
    print(f"{Colors.BOLD}║{' ' * 80}BENCHMARK RESULTS{' ' * 91}║{Colors.END}")
    print(f"{Colors.BOLD}╚{'=' * 190}╝{Colors.END}")

    print(
        f"{'Model':<40} | {'Time (s)':<9} | {'T1:Route':<10} | {'T2:Valid':<10} | {'T3:Work':<10} | {'CPU (%)':<8} | {'GPU (%)':<8} | {'Mem (MiB)':<10} | {'Ctx Size':<10} | {'GPU Card':<25}"
    )
    print("-" * 190)

    for model, metrics in results.items():
        stats = metrics["stats"]
        
        # Color code the test results
        def colorize_status(status):
            if "✓" in status:
                return f"{Colors.GREEN}{status}{Colors.END}"
            elif "⚠️" in status:
                return f"{Colors.YELLOW}{status}{Colors.END}"
            elif "❌" in status:
                return f"{Colors.RED}{status}{Colors.END}"
            return status
        
        t1 = colorize_status(metrics['test1_routing'])
        t2 = colorize_status(metrics['test2_validation'])
        t3 = colorize_status(metrics['test3_workflow'])

        # Use raw strings for alignment (without color codes)
        t1_raw = metrics["test1_routing"][:10]
        t2_raw = metrics["test2_validation"][:10]
        t3_raw = metrics["test3_workflow"][:10]

        # Get model config
        config = MODEL_CONFIGS.get(model, {"context_size": "N/A"})
        ctx_size = config.get("context_size", "N/A")
        gpu_name = stats.get("gpu_name", "Unknown")

        print(
            f"{model:<40} | {metrics['duration']:<9.2f} | {t1_raw:<10} | {t2_raw:<10} | {t3_raw:<10} | "
            f"{stats['cpu_avg']:<8.1f} | {stats['gpu_util_avg']:<8.1f} | {stats['gpu_mem_max']:<10.0f} | {ctx_size:<10} | {gpu_name:<25}"
        )

    # Check if any tests failed
    print()
    has_errors = False
    has_assertions = False
    
    for model, metrics in results.items():
        for test_key in ["test1_routing", "test2_validation", "test3_workflow"]:
            status = metrics[test_key]
            if "❌" in status:
                has_errors = True
                print(f"{Colors.RED}❌ {model} - {test_key}: {status}{Colors.END}")
            elif "⚠️" in status:
                has_assertions = True
                print(f"{Colors.YELLOW}⚠️ {model} - {test_key}: {status}{Colors.END}")
    
    # Fail the test if there were any errors
    if has_errors:
        pytest.fail(f"Benchmark tests failed with {sum(1 for m in results.values() for t in ['test1_routing', 'test2_validation', 'test3_workflow'] if '❌' in m[t])} errors")
    
    if has_assertions:
        print(f"\n{Colors.YELLOW}⚠️  Some assertions failed but tests continued{Colors.END}")
