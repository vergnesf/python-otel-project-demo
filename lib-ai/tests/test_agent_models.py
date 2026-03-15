"""Unit tests for lib_ai.agent_models — agent request/response Pydantic models.

Coverage:
- AgentType enum: all 4 values
- AgentRequest: required fields, defaults (time_range, context, timestamp)
- AgentResponse: confidence bounds (0.0–1.0), default fields, optional error
- OrchestratorResponse: nested agent_responses, recommendations list
"""

from datetime import datetime

import pytest
from lib_ai.agent_models import AgentRequest, AgentResponse, AgentType, OrchestratorResponse
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# AgentType
# ---------------------------------------------------------------------------


def test_agent_type_all_values():
    assert set(AgentType) == {
        AgentType.ORCHESTRATOR,
        AgentType.LOGS,
        AgentType.METRICS,
        AgentType.TRACES,
    }


def test_agent_type_string_values():
    assert AgentType.ORCHESTRATOR == "orchestrator"
    assert AgentType.LOGS == "logs"
    assert AgentType.METRICS == "metrics"
    assert AgentType.TRACES == "traces"


# ---------------------------------------------------------------------------
# AgentRequest
# ---------------------------------------------------------------------------


def test_agent_request_required_query():
    with pytest.raises(ValidationError):
        AgentRequest()


def test_agent_request_defaults():
    req = AgentRequest(query="test query")
    assert req.time_range == "1h"
    assert req.context == {}
    assert isinstance(req.timestamp, datetime)


def test_agent_request_custom_values():
    req = AgentRequest(query="why is order failing?", time_range="24h", context={"service": "order"})
    assert req.query == "why is order failing?"
    assert req.time_range == "24h"
    assert req.context == {"service": "order"}


# ---------------------------------------------------------------------------
# AgentResponse
# ---------------------------------------------------------------------------


def test_agent_response_required_fields():
    with pytest.raises(ValidationError):
        AgentResponse()


def test_agent_response_defaults():
    resp = AgentResponse(agent_name=AgentType.LOGS, analysis="all good")
    assert resp.confidence == 0.5
    assert resp.data == {}
    assert resp.grafana_links == []
    assert resp.error is None
    assert isinstance(resp.timestamp, datetime)


def test_agent_response_confidence_lower_bound():
    resp = AgentResponse(agent_name=AgentType.LOGS, analysis="x", confidence=0.0)
    assert resp.confidence == 0.0


def test_agent_response_confidence_upper_bound():
    resp = AgentResponse(agent_name=AgentType.METRICS, analysis="x", confidence=1.0)
    assert resp.confidence == 1.0


def test_agent_response_confidence_out_of_bounds_raises():
    with pytest.raises(ValidationError):
        AgentResponse(agent_name=AgentType.LOGS, analysis="x", confidence=1.1)
    with pytest.raises(ValidationError):
        AgentResponse(agent_name=AgentType.LOGS, analysis="x", confidence=-0.1)


def test_agent_response_optional_error():
    resp = AgentResponse(agent_name=AgentType.TRACES, analysis="failed", error="timeout")
    assert resp.error == "timeout"


# ---------------------------------------------------------------------------
# OrchestratorResponse
# ---------------------------------------------------------------------------


def _make_agent_response(agent_type: AgentType) -> AgentResponse:
    return AgentResponse(agent_name=agent_type, analysis="ok", confidence=0.8)


def test_orchestrator_response_required_fields():
    with pytest.raises(ValidationError):
        OrchestratorResponse()


def test_orchestrator_response_nested_agent_responses():
    resp = OrchestratorResponse(
        query="check errors",
        summary="all fine",
        agent_responses={
            "logs": _make_agent_response(AgentType.LOGS),
            "metrics": _make_agent_response(AgentType.METRICS),
        },
    )
    assert "logs" in resp.agent_responses
    assert resp.agent_responses["logs"].agent_name == AgentType.LOGS


def test_orchestrator_response_recommendations_default():
    resp = OrchestratorResponse(
        query="q",
        summary="s",
        agent_responses={"logs": _make_agent_response(AgentType.LOGS)},
    )
    assert resp.recommendations == []


def test_orchestrator_response_recommendations_list():
    resp = OrchestratorResponse(
        query="q",
        summary="s",
        agent_responses={},
        recommendations=["check logs", "restart service"],
    )
    assert len(resp.recommendations) == 2
