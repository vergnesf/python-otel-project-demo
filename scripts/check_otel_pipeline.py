#!/usr/bin/env python3
"""OTEL pipeline validation script.

Queries Tempo, Loki, and Mimir APIs to verify that recent telemetry data
from KEEPER services is flowing correctly through the observability stack.

Usage:
    uv run python scripts/check_otel_pipeline.py

Exit codes:
    0  All checks passed
    1  One or more checks failed
"""

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TEMPO_URL = "http://localhost:3200"
LOKI_URL = "http://localhost:3100"
MIMIR_BASE_URL = "http://localhost:9009"
MIMIR_URL = f"{MIMIR_BASE_URL}/prometheus"

KEEPER_SERVICES = [
    "ms-customer",
    "ms-supplier",
    "ms-order",
    "ms-stock",
    "ms-ordercheck",
    "ms-suppliercheck",
    "ms-ordermanagement",
]

# Look back window for recent data (seconds)
LOOKBACK_SECONDS = 300  # 5 minutes

TIMEOUT_SECONDS = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    details: str = ""


@dataclass
class Report:
    results: list[CheckResult] = field(default_factory=list)

    def add(self, result: CheckResult) -> None:
        self.results.append(result)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def counts(self) -> tuple[int, int]:
        ok = sum(1 for r in self.results if r.passed)
        return ok, len(self.results)


def _get(url: str, timeout: int = TIMEOUT_SECONDS) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _check_ready(url: str, timeout: int = TIMEOUT_SECONDS) -> None:
    """Check that a /ready endpoint returns HTTP 200. Body is ignored (plain text)."""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status}")


def _now_ns() -> int:
    return int(time.time() * 1e9)


def _ago_ns(seconds: int) -> int:
    return int((time.time() - seconds) * 1e9)


# ---------------------------------------------------------------------------
# Tempo checks
# ---------------------------------------------------------------------------


def check_tempo_ready(report: Report) -> None:
    """Tempo health endpoint responds."""
    try:
        _check_ready(f"{TEMPO_URL}/ready")
        report.add(CheckResult("tempo:ready", True, "Tempo is ready"))
    except Exception as e:
        report.add(CheckResult("tempo:ready", False, f"Tempo not reachable: {e}"))


def check_tempo_traces(report: Report, service: str) -> None:
    """Recent traces exist in Tempo for the given KEEPER service."""
    start_ns = _ago_ns(LOOKBACK_SECONDS)
    end_ns = _now_ns()
    url = f"{TEMPO_URL}/api/search?tags=service.name%3D{service}&start={start_ns}&end={end_ns}&limit=1"
    try:
        data = _get(url)
        traces = data.get("traces", [])
        if traces:
            report.add(CheckResult(f"tempo:{service}", True, f"Found {len(traces)} recent trace(s)"))
        else:
            report.add(CheckResult(f"tempo:{service}", False, "No recent traces found in last 5min"))
    except Exception as e:
        report.add(CheckResult(f"tempo:{service}", False, f"Query failed: {e}"))


# ---------------------------------------------------------------------------
# Loki checks
# ---------------------------------------------------------------------------


def check_loki_ready(report: Report) -> None:
    """Loki ready endpoint responds."""
    try:
        _check_ready(f"{LOKI_URL}/ready")
        report.add(CheckResult("loki:ready", True, "Loki is ready"))
    except Exception as e:
        report.add(CheckResult("loki:ready", False, f"Loki not reachable: {e}"))


def check_loki_logs(report: Report, service: str) -> None:
    """Recent logs exist in Loki for the given KEEPER service."""
    start_ns = _ago_ns(LOOKBACK_SECONDS)
    end_ns = _now_ns()
    query = f'{{service_name="{service}"}}'
    encoded_query = urllib.parse.quote(query)
    url = f"{LOKI_URL}/loki/api/v1/query_range?query={encoded_query}&start={start_ns}&end={end_ns}&limit=1"
    try:
        data = _get(url)
        streams = data.get("data", {}).get("result", [])
        if streams:
            report.add(CheckResult(f"loki:{service}", True, f"Found logs in {len(streams)} stream(s)"))
        else:
            report.add(CheckResult(f"loki:{service}", False, "No recent logs found in last 5min"))
    except Exception as e:
        report.add(CheckResult(f"loki:{service}", False, f"Query failed: {e}"))


# ---------------------------------------------------------------------------
# Mimir checks
# ---------------------------------------------------------------------------


def check_mimir_ready(report: Report) -> None:
    """Mimir /ready endpoint responds."""
    try:
        _check_ready(f"{MIMIR_BASE_URL}/ready")
        report.add(CheckResult("mimir:ready", True, "Mimir is ready"))
    except Exception as e:
        report.add(CheckResult("mimir:ready", False, f"Mimir not reachable: {e}"))


def check_mimir_metrics(report: Report) -> None:
    """Active OTEL metrics exist in Mimir for KEEPER services."""
    # Query for any OTEL-generated metric with a service_name label from our services
    query = 'count by (service_name) ({__name__=~".+", service_name=~"ms-.+"})'
    encoded = urllib.parse.quote(query)
    url = f"{MIMIR_URL}/api/v1/query?query={encoded}"
    try:
        data = _get(url)
        results = data.get("data", {}).get("result", [])
        if results:
            services_with_metrics = [r["metric"].get("service_name", "?") for r in results]
            report.add(
                CheckResult(
                    "mimir:keeper_metrics",
                    True,
                    f"Active metrics found for: {', '.join(sorted(services_with_metrics))}",
                )
            )
        else:
            report.add(CheckResult("mimir:keeper_metrics", False, "No active KEEPER metrics found in Mimir"))
    except Exception as e:
        report.add(CheckResult("mimir:keeper_metrics", False, f"Query failed: {e}"))


def check_mimir_otel_collector_metrics(report: Report) -> None:
    """otelcol metrics are present — confirms collector is exporting."""
    query = 'count({__name__=~"otelcol_.+"})'
    encoded = urllib.parse.quote(query)
    url = f"{MIMIR_URL}/api/v1/query?query={encoded}"
    try:
        data = _get(url)
        results = data.get("data", {}).get("result", [])
        count = int(float(results[0]["value"][1])) if results else 0
        if count > 0:
            report.add(CheckResult("mimir:otelcol", True, f"{count} otelcol metric series active"))
        else:
            report.add(CheckResult("mimir:otelcol", False, "No otelcol metrics found — collector may not be exporting"))
    except Exception as e:
        report.add(CheckResult("mimir:otelcol", False, f"Query failed: {e}"))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_checks() -> Report:
    report = Report()

    print(f"\n🔍 OTEL Pipeline Check — {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"   Lookback window: {LOOKBACK_SECONDS}s | Services: {len(KEEPER_SERVICES)}\n")

    # --- Tempo ---
    print("── Tempo ─────────────────────────────────────────")
    check_tempo_ready(report)
    if report.results[-1].passed:
        for svc in KEEPER_SERVICES:
            check_tempo_traces(report, svc)

    # --- Loki ---
    print("\n── Loki ──────────────────────────────────────────")
    check_loki_ready(report)
    if report.results[-1].passed:
        for svc in KEEPER_SERVICES:
            check_loki_logs(report, svc)

    # --- Mimir ---
    print("\n── Mimir ─────────────────────────────────────────")
    check_mimir_ready(report)
    if report.results[-1].passed:
        check_mimir_metrics(report)
        check_mimir_otel_collector_metrics(report)

    return report


def print_report(report: Report) -> None:
    print("\n── Results ───────────────────────────────────────")
    for r in report.results:
        icon = "✅" if r.passed else "❌"
        print(f"  {icon}  {r.name:<35} {r.message}")

    ok, total = report.counts
    print(f"\n{'✅ All checks passed' if report.passed else '❌ Some checks failed'} ({ok}/{total})\n")


if __name__ == "__main__":
    report = run_checks()
    print_report(report)
    sys.exit(0 if report.passed else 1)
