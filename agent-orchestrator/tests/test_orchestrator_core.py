#!/usr/bin/env python3
"""
Unit tests for orchestrator core behaviors:
1. Agent routing (logs, traces, metrics)
2. Response validation
3. End-to-end flow with translation agent mocked
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from agent_orchestrator.orchestrator import Orchestrator

pytestmark = pytest.mark.unit


class TestAgentRouting:
    """Test Functionality 2: Agent routing"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        with patch("agent_orchestrator.orchestrator.get_llm") as mock_llm:
            mock_llm.return_value = Mock()
            orch = Orchestrator()
            yield orch

    @pytest.mark.asyncio
    async def test_route_to_logs_agent(self, orchestrator):
        """Test routing to logs agent for error queries"""
        with patch.object(orchestrator, "llm") as mock_llm:
            mock_llm.invoke.return_value = Mock(
                content='{"agents": ["logs"], "reason": "Error query"}'
            )

            result = await orchestrator._route_to_agents("Show me recent errors")

            assert "logs" in result["agents"]
            assert len(result["agents"]) >= 1

    @pytest.mark.asyncio
    async def test_route_to_metrics_agent(self, orchestrator):
        """Test routing to metrics agent for performance queries"""
        with patch.object(orchestrator, "llm") as mock_llm:
            mock_llm.invoke.return_value = Mock(
                content='{"agents": ["metrics"], "reason": "CPU query"}'
            )

            result = await orchestrator._route_to_agents("What is the CPU usage?")

            assert "metrics" in result["agents"]

    @pytest.mark.asyncio
    async def test_route_to_traces_agent(self, orchestrator):
        """Test routing to traces agent for slow request queries"""
        with patch.object(orchestrator, "llm") as mock_llm:
            mock_llm.invoke.return_value = Mock(
                content='{"agents": ["traces"], "reason": "Slow query"}'
            )

            result = await orchestrator._route_to_agents("Which services are slow?")

            assert "traces" in result["agents"]

    @pytest.mark.asyncio
    async def test_route_to_multiple_agents(self, orchestrator):
        """Test routing to multiple agents for complex queries"""
        with patch.object(orchestrator, "llm") as mock_llm:
            mock_llm.invoke.return_value = Mock(
                content='{"agents": ["logs", "metrics"], "reason": "Complex query"}'
            )

            result = await orchestrator._route_to_agents("Show errors and CPU usage")

            assert len(result["agents"]) >= 2

    @pytest.mark.asyncio
    async def test_keyword_based_routing_errors(self, orchestrator):
        """Test keyword-based routing for error-related queries"""
        result = orchestrator._keyword_based_routing("Show me errors")

        assert "logs" in result["agents"]
        assert "keyword" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_keyword_based_routing_cpu(self, orchestrator):
        """Test keyword-based routing for CPU queries"""
        result = orchestrator._keyword_based_routing("CPU usage is high")

        assert "metrics" in result["agents"]

    @pytest.mark.asyncio
    async def test_keyword_based_routing_slow(self, orchestrator):
        """Test keyword-based routing for slow queries"""
        result = orchestrator._keyword_based_routing("Requests are slow")

        assert "traces" in result["agents"]

    @pytest.mark.asyncio
    async def test_keyword_based_routing_default(self, orchestrator):
        """Test that default routing goes to logs"""
        result = orchestrator._keyword_based_routing("What's happening?")

        assert "logs" in result["agents"]

    @pytest.mark.asyncio
    async def test_routing_fallback_without_llm(self):
        """Test routing fallback when LLM is not available"""
        with patch("agent_orchestrator.orchestrator.get_llm") as mock_llm:
            mock_llm.side_effect = Exception("LLM not available")
            orch = Orchestrator()

            result = await orch._route_to_agents("Show errors")

            # Should use keyword-based routing
            assert "agents" in result
            assert "logs" in result["agents"]


class TestResponseValidation:
    """Test Functionality 3: Response validation"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        with patch("agent_orchestrator.orchestrator.get_llm") as mock_llm:
            mock_llm.return_value = Mock()
            orch = Orchestrator()
            yield orch

    @pytest.mark.asyncio
    async def test_validate_valid_response(self, orchestrator):
        """Test validation of a good response"""
        with patch.object(orchestrator, "llm") as mock_llm:
            mock_llm.invoke.return_value = Mock(
                content='{"valid": true, "issues": [], "suggestion": "Good response"}'
            )

            agent_responses = {
                "logs": {"analysis": "Found 5 errors in the customer service"}
            }

            result = await orchestrator._validate_responses(
                "Show me errors", agent_responses
            )

            assert result["validated"]
            assert result["issues"] == []

    @pytest.mark.asyncio
    async def test_validate_invalid_response(self, orchestrator):
        """Test validation of an incomplete response"""
        with patch.object(orchestrator, "llm") as mock_llm:
            mock_llm.invoke.return_value = Mock(
                content='{"valid": false, "issues": ["Missing concrete data"], "suggestion": "Add specific examples"}'
            )

            agent_responses = {"logs": {"analysis": "There might be some issues"}}

            result = await orchestrator._validate_responses(
                "Show me errors", agent_responses
            )

            assert not result["validated"]
            assert len(result["issues"]) > 0

    @pytest.mark.asyncio
    async def test_validate_empty_responses(self, orchestrator):
        """Test validation with empty responses"""
        result = await orchestrator._validate_responses("Show errors", {})

        assert not result["validated"]
        assert "no valid" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_validate_error_responses(self, orchestrator):
        """Test validation with error responses"""
        agent_responses = {"logs": {"error": "Connection failed"}}

        result = await orchestrator._validate_responses("Show errors", agent_responses)

        assert not result["validated"]

    @pytest.mark.asyncio
    async def test_validation_without_llm(self):
        """Test that validation fails gracefully without LLM"""
        with patch("agent_orchestrator.orchestrator.get_llm") as mock_llm:
            mock_llm.side_effect = Exception("LLM not available")
            orch = Orchestrator()

            result = await orch._validate_responses("Show errors", {})

            assert not result["validated"]
            assert "no llm" in result["reason"].lower()


class TestEndToEndFlow:
    """Test complete end-to-end flow"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance with mocked HTTP client"""
        with patch("agent_orchestrator.orchestrator.get_llm") as mock_llm:
            mock_llm.return_value = Mock()
            orch = Orchestrator()
            # Mock the HTTP client
            orch.client = AsyncMock()
            yield orch

    @pytest.mark.asyncio
    async def test_french_query_full_flow(self, orchestrator):
        """Test complete flow with French query"""
        # Mock LLM responses for routing and validation
        with patch.object(orchestrator, "llm") as mock_llm:
            mock_llm.invoke.side_effect = [
                Mock(
                    content='{"agents": ["logs"], "reason": "Error query"}'
                ),  # Routing
                Mock(
                    content='{"valid": true, "issues": [], "suggestion": "Good"}'
                ),  # Validation
            ]

            def build_response(payload: dict):
                response = AsyncMock()
                response.status_code = 200
                response.json = Mock(return_value=payload)
                response.raise_for_status = Mock()
                return response

            translate_response = build_response(
                {
                    "language": "non-english",
                    "translated_query": "Show me recent errors",
                }
            )
            agent_response = build_response(
                {
                    "analysis": "Found 3 errors in customer service",
                    "recommendations": ["Check database connection"],
                    "data": {"error_count": 3},
                }
            )

            async def mock_post(url, **kwargs):
                if url.endswith("/translate"):
                    return translate_response
                return agent_response

            orchestrator.client.post = mock_post

            result = await orchestrator.analyze("Montre-moi les erreurs récentes")

            # Check that translation happened
            assert result["language"] == "non-english"
            assert result["translated_query"] != result["query"]

            # Check that routing happened
            assert "logs" in result["routing"]["agents"]

            # Check that agent was called
            assert "logs" in result["agent_responses"]

            # Check validation
            assert "validation" in result

    @pytest.mark.asyncio
    async def test_english_query_full_flow(self, orchestrator):
        """Test complete flow with English query"""
        with patch.object(orchestrator, "llm") as mock_llm:
            mock_llm.invoke.side_effect = [
                Mock(
                    content='{"agents": ["metrics"], "reason": "CPU query"}'
                ),  # Routing
                Mock(
                    content='{"valid": true, "issues": [], "suggestion": "Good"}'
                ),  # Validation
            ]

            def build_response(payload: dict):
                response = AsyncMock()
                response.status_code = 200
                response.json = Mock(return_value=payload)
                response.raise_for_status = Mock()
                return response

            translate_response = build_response(
                {
                    "language": "english",
                    "translated_query": "What is the CPU usage?",
                }
            )
            agent_response = build_response(
                {
                    "analysis": "CPU usage is at 75%",
                    "recommendations": ["Consider scaling"],
                    "data": {"cpu_usage": 75},
                }
            )

            async def mock_post(url, **kwargs):
                if url.endswith("/translate"):
                    return translate_response
                return agent_response

            orchestrator.client.post = mock_post

            result = await orchestrator.analyze("What is the CPU usage?")

            # Check that no translation happened (already English)
            assert result["language"] == "english"
            assert result["translated_query"] == result["query"]

            # Check that routing happened
            assert "metrics" in result["routing"]["agents"]

            # Check that agent was called
            assert "metrics" in result["agent_responses"]

    @pytest.mark.asyncio
    async def test_multi_agent_flow(self, orchestrator):
        """Test flow with multiple agents"""
        with patch.object(orchestrator, "llm") as mock_llm:
            mock_llm.invoke.side_effect = [
                Mock(
                    content='{"agents": ["logs", "metrics"], "reason": "Complex"}'
                ),  # Routing
                Mock(
                    content='{"valid": true, "issues": [], "suggestion": "Good"}'
                ),  # Validation
            ]

            def build_response(payload: dict):
                response = AsyncMock()
                response.status_code = 200
                response.json = Mock(return_value=payload)
                response.raise_for_status = Mock()
                return response

            translate_response = build_response(
                {
                    "language": "english",
                    "translated_query": "Show errors and performance",
                }
            )

            async def mock_post(url, **kwargs):
                if url.endswith("/translate"):
                    return translate_response
                if "logs" in url:
                    return build_response(
                        {
                            "analysis": "Found errors",
                            "recommendations": ["Fix errors"],
                        }
                    )
                if "metrics" in url:
                    return build_response(
                        {
                            "analysis": "CPU high",
                            "recommendations": ["Scale up"],
                        }
                    )

            orchestrator.client.post = mock_post

            result = await orchestrator.analyze("Show errors and performance")

            # Check that multiple agents were called
            assert len(result["routing"]["agents"]) >= 2
            assert len(result["agent_responses"]) >= 2


def main():
    """Run all tests"""
    print("=" * 80)
    print("UNIT TESTS - SIMPLIFIED ORCHESTRATOR")
    print("=" * 80)
    print()

    # Run pytest
    pytest.main([__file__, "-v", "--tb=short", "-s"])


if __name__ == "__main__":
    main()
