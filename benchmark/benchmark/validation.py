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
