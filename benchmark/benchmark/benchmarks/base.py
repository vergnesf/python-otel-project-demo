"""Shared utilities for agent benchmarks."""

import logging
import statistics

import httpx

logger = logging.getLogger(__name__)


def validate_response_consistency(responses: list[dict]) -> tuple[bool, str]:
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


def extract_query(request: dict) -> str:
    """Extract just the query from a request for simplified display."""
    if "query" in request:
        return request["query"]
    return str(request)
