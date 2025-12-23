#!/usr/bin/env python3
"""
Benchmark tests for different AI models
"""

import httpx
import asyncio
import pytest
from datetime import datetime
import time
import json
import psutil
import subprocess
import threading
import statistics
from pathlib import Path
import yaml
from tests.test_orchestrator_integration import (
    run_language_detection_and_translation,
    run_agent_routing,
    run_response_validation,
    run_complete_workflow,
    check_orchestrator_available,
    Colors,
    BASE_URL,
    TIMEOUT,
)

MODELS = [
    "ai/mistral:7B-Q4_0",
    "ai/llama3.2:3B-Q4_K_M",
    "ai/qwen3:0.6B-Q4_0",
    "ai/granite-4.0-h-micro:3B-Q4_K_M",
    "ai/mistral-nemo:12B-Q4_K_M",
    "ai/qwen2.5:7B-Q4_0",
    "ai/phi4:14B-Q4_0",
]


def load_model_configs():
    """Load model configurations from docker-compose.yml"""
    compose_file = Path(__file__).parent.parent.parent / "docker-compose.yml"
    try:
        with open(compose_file, "r") as f:
            compose_data = yaml.safe_load(f)

        model_configs = {}
        models_section = compose_data.get("models", {})

        for model_key, model_data in models_section.items():
            model_name = model_data.get("model")
            context_size = model_data.get("context_size", "N/A")
            if model_name:
                model_configs[model_name] = {"context_size": context_size}

        return model_configs
    except Exception as e:
        print(
            f"{Colors.YELLOW}⚠️  Could not load model configs from docker-compose.yml: {e}{Colors.END}"
        )
        return {}


MODEL_CONFIGS = load_model_configs()


def restart_model_runner():
    """Restart Docker Model Runner to free GPU memory"""
    try:
        result = subprocess.run(
            ["docker", "model", "restart-runner"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print(f"{Colors.GREEN}✓ Docker Model Runner restarted{Colors.END}")
            # Wait for the runner to be ready
            time.sleep(5)
            return True
        else:
            print(
                f"{Colors.RED}❌ Failed to restart Docker Model Runner: {result.stderr}{Colors.END}"
            )
            return False
    except Exception as e:
        print(f"{Colors.RED}❌ Failed to restart Docker Model Runner: {e}{Colors.END}")
        return False


async def check_model_availability(model: str):
    """Check if the model is available in the list of models"""
    print(f"Checking availability for model: {model}...")
    # Assuming the model runner is exposed on localhost:12434
    url = "http://localhost:12434/v1/models"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                print(
                    f"{Colors.RED}❌ Failed to list models: HTTP {response.status_code} - {response.text}{Colors.END}"
                )
                return False

            data = response.json()
            available_models = [m["id"] for m in data.get("data", [])]

            if model in available_models:
                print(f"{Colors.GREEN}✓ Model {model} is available{Colors.END}")
                return True
            else:
                print(
                    f"{Colors.RED}❌ Model {model} not found in available models{Colors.END}"
                )
                return False

    except Exception as e:
        print(f"{Colors.RED}❌ Model {model} check failed: {e}{Colors.END}")
        return False


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
async def test_benchmark_models():
    """Run benchmark for all configured AI models"""
    await check_orchestrator_available()

    print(f"\n{Colors.BOLD}╔{'=' * 78}╗{Colors.END}")
    print(f"{Colors.BOLD}║{' ' * 25}AI MODEL BENCHMARK{' ' * 33}║{Colors.END}")
    print(f"{Colors.BOLD}╚{'=' * 78}╝{Colors.END}")

    # Pre-check: Verify all models are available before starting
    print(f"\n{Colors.BOLD}🔍 Pre-checking model availability...{Colors.END}")
    unavailable_models = []
    for model in MODELS:
        if not await check_model_availability(model):
            unavailable_models.append(model)

    if unavailable_models:
        print(
            f"\n{Colors.RED}{Colors.BOLD}❌ ABORTING BENCHMARK: The following models are unavailable:{Colors.END}"
        )
        for model in unavailable_models:
            print(f"  - {model}")
        print(
            f"\n{Colors.YELLOW}Please ensure all models are pulled and running via 'docker compose up -d'{Colors.END}"
        )
        pytest.fail(f"Benchmark aborted. Unavailable models: {unavailable_models}")

    print(
        f"\n{Colors.GREEN}{Colors.BOLD}✓ All models available. Starting benchmark...{Colors.END}"
    )

    results = {}

    for i, model in enumerate(MODELS):
        # Restart Docker Model Runner between tests to free GPU memory
        if i > 0:  # Skip restart before first model
            print(
                f"\n{Colors.YELLOW}🔄 Restarting Docker Model Runner to free GPU memory...{Colors.END}"
            )
            if not restart_model_runner():
                print(
                    f"{Colors.RED}❌ Failed to restart DMR, continuing anyway...{Colors.END}"
                )

        print(f"\n{Colors.BOLD}Testing Model: {Colors.BLUE}{model}{Colors.END}")
        results[model] = {
            "test1_language": "NOT_RUN",
            "test2_routing": "NOT_RUN",
            "test3_validation": "NOT_RUN",
            "test4_workflow": "NOT_RUN",
            "duration": 0,
            "stats": {},
        }

        monitor = ResourceMonitor()
        monitor.start()
        start_time_model = time.time()

        # Test 1: Language Detection and Translation
        try:
            await run_language_detection_and_translation(model=model)
            results[model]["test1_language"] = "PASSED"
            print(f"{Colors.GREEN}✓ TEST 1 PASSED{Colors.END}")
        except Exception as e:
            results[model]["test1_language"] = "FAILED"
            print(f"{Colors.RED}❌ TEST 1 FAILED: {e}{Colors.END}")

        # Test 2: Agent Routing
        try:
            await run_agent_routing(model=model)
            results[model]["test2_routing"] = "PASSED"
            print(f"{Colors.GREEN}✓ TEST 2 PASSED{Colors.END}")
        except Exception as e:
            results[model]["test2_routing"] = "FAILED"
            print(f"{Colors.RED}❌ TEST 2 FAILED: {e}{Colors.END}")

        # Test 3: Response Validation
        try:
            await run_response_validation(model=model)
            results[model]["test3_validation"] = "PASSED"
            print(f"{Colors.GREEN}✓ TEST 3 PASSED{Colors.END}")
        except Exception as e:
            results[model]["test3_validation"] = "FAILED"
            print(f"{Colors.RED}❌ TEST 3 FAILED: {e}{Colors.END}")

        # Test 4: Complete Workflow
        try:
            await run_complete_workflow(model=model)
            results[model]["test4_workflow"] = "PASSED"
            print(f"{Colors.GREEN}✓ TEST 4 PASSED{Colors.END}")
        except Exception as e:
            results[model]["test4_workflow"] = "FAILED"
            print(f"{Colors.RED}❌ TEST 4 FAILED: {e}{Colors.END}")

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

    # Print Summary
    print(f"\n{Colors.BOLD}╔{'=' * 190}╗{Colors.END}")
    print(f"{Colors.BOLD}║{' ' * 80}BENCHMARK RESULTS{' ' * 91}║{Colors.END}")
    print(f"{Colors.BOLD}╚{'=' * 190}╝{Colors.END}")

    print(
        f"{'Model':<40} | {'Time (s)':<9} | {'T1:Lang':<10} | {'T2:Route':<10} | {'T3:Valid':<10} | {'T4:Work':<10} | {'CPU (%)':<8} | {'GPU (%)':<8} | {'Mem (MiB)':<10} | {'Ctx Size':<10} | {'GPU Card':<25}"
    )
    print("-" * 190)

    for model, metrics in results.items():
        stats = metrics["stats"]
        # Color code the test results
        t1 = (
            f"{Colors.GREEN}{metrics['test1_language']}{Colors.END}"
            if metrics["test1_language"] == "PASSED"
            else f"{Colors.RED}{metrics['test1_language']}{Colors.END}"
        )
        t2 = (
            f"{Colors.GREEN}{metrics['test2_routing']}{Colors.END}"
            if metrics["test2_routing"] == "PASSED"
            else f"{Colors.RED}{metrics['test2_routing']}{Colors.END}"
        )
        t3 = (
            f"{Colors.GREEN}{metrics['test3_validation']}{Colors.END}"
            if metrics["test3_validation"] == "PASSED"
            else f"{Colors.RED}{metrics['test3_validation']}{Colors.END}"
        )
        t4 = (
            f"{Colors.GREEN}{metrics['test4_workflow']}{Colors.END}"
            if metrics["test4_workflow"] == "PASSED"
            else f"{Colors.RED}{metrics['test4_workflow']}{Colors.END}"
        )

        # Use raw strings for alignment (without color codes)
        t1_raw = metrics["test1_language"]
        t2_raw = metrics["test2_routing"]
        t3_raw = metrics["test3_validation"]
        t4_raw = metrics["test4_workflow"]

        # Get model config
        config = MODEL_CONFIGS.get(model, {"context_size": "N/A"})
        ctx_size = config.get("context_size", "N/A")
        gpu_name = stats.get("gpu_name", "Unknown")

        print(
            f"{model:<40} | {metrics['duration']:<9.2f} | {t1_raw:<10} | {t2_raw:<10} | {t3_raw:<10} | {t4_raw:<10} | "
            f"{stats['cpu_avg']:<8.1f} | {stats['gpu_util_avg']:<8.1f} | {stats['gpu_mem_max']:<10.0f} | {ctx_size:<10} | {gpu_name:<25}"
        )
