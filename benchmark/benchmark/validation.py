"""Validation helpers for benchmark responses."""

from __future__ import annotations


def _is_probably_french(text: str) -> bool:
    """Heuristic to detect French input."""
    lowered = text.lower()
    french_markers = [
        "bonjour",
        "merci",
        "ceci",
        "traduction",
        "s'il vous plaît",
        "é",
        "à",
        "è",
        "ô",
        "ç",
    ]
    return any(marker in lowered for marker in french_markers)


def validate_translation_response(query: str, response: dict) -> tuple[bool, str]:
    """Validate translation response against expected behavior."""
    if not isinstance(response, dict):
        return False, "invalid response format"
    if response.get("agent_name") != "translation":
        return False, "expected agent_name='translation'"
    language = response.get("language")
    translated = response.get("translated_query")
    if translated is None:
        return False, "missing translated_query"
    if _is_probably_french(query):
        if language != "non-english":
            return False, "expected language='non-english' for French input"
        if translated.strip() == query.strip():
            return False, "expected translation to English (different from input)"
        return True, "FR input translated to English"
    if language != "english":
        return False, "expected language='english' for English input"
    if translated.strip() != query.strip():
        return False, "expected English input to remain unchanged"
    return True, "EN input unchanged"


def validate_agent_response(agent: str, response: dict) -> tuple[bool, str]:
    """Validate common agent response structure."""
    if not isinstance(response, dict):
        return False, "invalid response format"
    if isinstance(response.get("error"), str):
        return False, "response contains error"
    if response.get("agent_name") != agent:
        return False, f"expected agent_name='{agent}'"
    if not response.get("analysis"):
        return False, "missing analysis"
    if not isinstance(response.get("data"), dict):
        return False, "missing data"
    return True, "response structure OK"


def validate_orchestrator_response(response: dict) -> tuple[bool, str]:
    """Validate orchestrator response structure."""
    if not isinstance(response, dict):
        return False, "invalid response format"
    required_keys = ["translated_query", "routing", "agent_responses", "summary"]
    for key in required_keys:
        if key not in response:
            return False, f"missing '{key}'"
    routing = response.get("routing", {})
    if not isinstance(routing, dict) or not isinstance(routing.get("agents"), list):
        return False, "invalid routing"
    if not isinstance(response.get("agent_responses"), dict):
        return False, "invalid agent_responses"
    return True, "response structure OK"


def validate_routing(response: dict, query: str) -> tuple[bool, str]:
    """Validate that routing matches query intent."""
    if not isinstance(response, dict):
        return False, "invalid response format"
    
    routed_agents = response.get("routing", {}).get("agents", [])
    agent_responses = response.get("agent_responses", {})
    
    query_lower = query.lower()
    
    # Define keywords for each agent type
    logs_keywords = {"error", "exception", "warning", "log", "failed", "failure"}
    metrics_keywords = {"cpu", "memory", "ram", "performance", "usage", "latency", "throughput"}
    traces_keywords = {"trace", "request", "slow", "latency", "span", "flow"}
    
    expected_agents = set()
    
    # Determine expected agents based on query keywords
    if any(kw in query_lower for kw in logs_keywords):
        expected_agents.add("logs")
    if any(kw in query_lower for kw in metrics_keywords):
        expected_agents.add("metrics")
    if any(kw in query_lower for kw in traces_keywords):
        expected_agents.add("traces")
    
    # If no specific keywords found, query might be combined
    if not expected_agents:
        # For combined queries, we might expect multiple agents
        if len(routed_agents) == 0:
            return False, "no agents routed"
        return True, f"combined query routed to {', '.join(routed_agents)}"
    
    routed_set = set(routed_agents)
    
    # Check if routed agents match or exceed expected agents
    if expected_agents.issubset(routed_set):
        return True, f"correct routing: {', '.join(sorted(routed_set))}"
    
    # Allow partial matches for closely related queries
    if len(expected_agents & routed_set) > 0:
        return True, f"partial match: expected {expected_agents}, got {routed_set}"
    
    return False, f"expected {expected_agents}, got {routed_set}"
