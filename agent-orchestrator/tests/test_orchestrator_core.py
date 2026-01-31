#!/usr/bin/env python3
"""
Unit tests for the 3 core functionalities of the Orchestrator:
1. Language detection and translation
2. Agent routing (logs, traces, metrics)
3. Response validation
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_orchestrator.orchestrator import Orchestrator

pytestmark = pytest.mark.unit


class TestLanguageDetectionAndTranslation:
    """Test Functionality 1: Language detection and translation"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        with patch("agent_orchestrator.orchestrator.get_llm") as mock_llm:
            mock_llm.return_value = Mock()
            orch = Orchestrator()
            yield orch

    @pytest.mark.asyncio
    async def test_detect_english_query(self, orchestrator):
        """Test that English queries are detected correctly"""
        # Mock LLM to return "ENGLISH"
        with patch.object(orchestrator, "llm") as mock_llm:
            mock_llm.invoke.return_value = Mock(content="ENGLISH")

            result = await orchestrator._detect_and_translate("Show me recent errors")

            assert result["language"] == "english"
            assert result["translated_query"] == "Show me recent errors"

    @pytest.mark.asyncio
    async def test_detect_and_translate_french_query(self, orchestrator):
        """Test that French queries are detected and translated"""
        # Mock LLM responses
        with patch.object(orchestrator, "llm") as mock_llm:
            # First call: language detection -> NOT_ENGLISH
            # Second call: translation -> translated text
            mock_llm.invoke.side_effect = [
                Mock(content="NOT_ENGLISH"),
                Mock(content="Show me recent errors"),
            ]

            result = await orchestrator._detect_and_translate(
                "Montre-moi les erreurs récentes"
            )

            assert result["language"] == "non-english"
            assert "error" in result["translated_query"].lower()

    @pytest.mark.asyncio
    async def test_translation_handles_empty_query(self, orchestrator):
        """Test that empty queries are handled gracefully"""
        result = await orchestrator._detect_and_translate("")

        assert result["language"] == "unknown"
        assert result["translated_query"] == ""

    @pytest.mark.asyncio
    async def test_translation_fallback_without_llm(self):
        """Test translation fallback when LLM is not available"""
        with patch("agent_orchestrator.orchestrator.get_llm") as mock_llm:
            mock_llm.side_effect = Exception("LLM not available")
            orch = Orchestrator()

            result = await orch._detect_and_translate("Bonjour")

            assert result["language"] == "unknown"
            assert result["translated_query"] == "Bonjour"

    @pytest.mark.asyncio
    async def test_translation_handles_code_blocks(self, orchestrator):
        """Test that translation removes code blocks from LLM response"""
        with patch.object(orchestrator, "llm") as mock_llm:
            # LLM returns translation wrapped in code blocks
            mock_llm.invoke.side_effect = [
                Mock(content="NOT_ENGLISH"),
                Mock(content="```\nShow me recent errors\n```"),
            ]

            result = await orchestrator._detect_and_translate("Montre-moi les erreurs")

            assert result["language"] == "non-english"
            # Code blocks should be removed
            assert not result["translated_query"].startswith("```")
            assert "error" in result["translated_query"].lower()


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
        # Mock LLM responses for translation and routing
        with patch.object(orchestrator, "llm") as mock_llm:
            mock_llm.invoke.side_effect = [
                Mock(content="NOT_ENGLISH"),  # Language detection
                Mock(content="Show me recent errors"),  # Translation
                Mock(
                    content='{"agents": ["logs"], "reason": "Error query"}'
                ),  # Routing
                Mock(
                    content='{"valid": true, "issues": [], "suggestion": "Good"}'
                ),  # Validation
            ]

            # Mock agent response
            mock_response = AsyncMock(
                status_code=200,
                json=lambda: {
                    "analysis": "Found 3 errors in customer service",
                    "recommendations": ["Check database connection"],
                    "data": {"error_count": 3},
                },
            )
            mock_response.raise_for_status = Mock()
            orchestrator.client.post.return_value = mock_response

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
                Mock(content="ENGLISH"),  # Language detection
                Mock(
                    content='{"agents": ["metrics"], "reason": "CPU query"}'
                ),  # Routing
                Mock(
                    content='{"valid": true, "issues": [], "suggestion": "Good"}'
                ),  # Validation
            ]

            # Mock agent response
            mock_response = AsyncMock(
                status_code=200,
                json=lambda: {
                    "analysis": "CPU usage is at 75%",
                    "recommendations": ["Consider scaling"],
                    "data": {"cpu_usage": 75},
                },
            )
            mock_response.raise_for_status = Mock()
            orchestrator.client.post.return_value = mock_response

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
                Mock(content="ENGLISH"),  # Language detection
                Mock(
                    content='{"agents": ["logs", "metrics"], "reason": "Complex"}'
                ),  # Routing
                Mock(
                    content='{"valid": true, "issues": [], "suggestion": "Good"}'
                ),  # Validation
            ]

            # Mock multiple agent responses
            async def mock_post(url, **kwargs):
                if "logs" in url:
                    return AsyncMock(
                        status_code=200,
                        json=lambda: {
                            "analysis": "Found errors",
                            "recommendations": ["Fix errors"],
                        },
                    )
                elif "metrics" in url:
                    return AsyncMock(
                        status_code=200,
                        json=lambda: {
                            "analysis": "CPU high",
                            "recommendations": ["Scale up"],
                        },
                    )

            orchestrator.client.post = mock_post

            result = await orchestrator.analyze("Show errors and performance")

            # Check that multiple agents were called
            assert len(result["routing"]["agents"]) >= 2
            assert len(result["agent_responses"]) >= 2


def main():
    """Run all tests"""
    print("=" * 80)
    print("TESTS UNITAIRES - ORCHESTRATEUR SIMPLIFIÉ")
    print("=" * 80)
    print()

    # Run pytest
    pytest.main([__file__, "-v", "--tb=short", "-s"])


if __name__ == "__main__":
    main()
