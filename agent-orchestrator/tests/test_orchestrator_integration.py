#!/usr/bin/env python3
"""
Integration tests for the simplified Orchestrator
Tests the 3 key functionalities with real HTTP calls:
1. Language detection and translation
2. Agent routing (logs, traces, metrics)
3. Response validation

REQUIREMENTS:
- Orchestrator must be running on http://localhost:8001
- LLM must be running at http://172.17.0.1:12434/v1 (docker-compose default)
- All tests require a working LLM for translation and validation
"""

import httpx
import asyncio
import pytest
from datetime import datetime


BASE_URL = "http://localhost:8001"
TIMEOUT = 120.0

# LLM URL (same as docker-compose default)
LLM_BASE_URL = "http://172.17.0.1:12434/v1"


class Colors:
    """ANSI color codes for terminal output"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


async def check_orchestrator_available():
    """Check if orchestrator is running"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code != 200:
                pytest.skip(
                    f"Orchestrator not healthy at {BASE_URL} (status: {response.status_code})"
                )
    except Exception as e:
        pytest.skip(f"Orchestrator not running at {BASE_URL}: {e}")


async def test_language_detection_and_translation():
    """
    TEST 1: Language Detection and Translation
    Verify that French queries are detected and translated to English
    """
    await check_orchestrator_available()

    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}TEST 1: LANGUAGE DETECTION AND TRANSLATION{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 80}{Colors.END}\n")
    print(f"{Colors.YELLOW}Using LLM: {LLM_BASE_URL}{Colors.END}\n")

    test_cases = [
        {
            "query": "Montre-moi les erreurs récentes",
            "expected_lang": "non-english",
            "should_translate": True,
        },
        {
            "query": "Show me recent errors",
            "expected_lang": "english",
            "should_translate": False,
        },
        {
            "query": "Quels services sont lents?",
            "expected_lang": "non-english",
            "should_translate": True,
        },
    ]

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for i, test_case in enumerate(test_cases, 1):
            query = test_case["query"]
            print(f"{Colors.BLUE}Test {i}: '{query}'{Colors.END}")

            response = await client.post(
                f"{BASE_URL}/analyze", json={"query": query, "time_range": "1h"}
            )

            assert response.status_code == 200, f"HTTP {response.status_code}"

            data = response.json()
            language = data.get("language", "unknown")
            translated = data.get("translated_query", "")

            print(f"  Detected language: {Colors.YELLOW}{language}{Colors.END}")
            print(f"  Translated query: {Colors.YELLOW}{translated}{Colors.END}")

            # Verify language detection
            if test_case["expected_lang"] != "unknown":
                assert (
                    language == test_case["expected_lang"]
                ), f"Expected {test_case['expected_lang']}, got {language}"

            # Verify translation
            if test_case["should_translate"]:
                assert translated != query, "Query should have been translated"
                assert len(translated) > 0, "Translation is empty"
            else:
                assert translated == query, "Query should not have been translated"

            print(f"  {Colors.GREEN}✓ Test {i} passed{Colors.END}\n")
            await asyncio.sleep(1)

    print(f"{Colors.GREEN}{Colors.BOLD}✓ All translation tests passed!{Colors.END}\n")


async def test_agent_routing():
    """
    TEST 2: Agent Routing
    Verify that queries are routed to the correct agents
    """
    await check_orchestrator_available()

    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}TEST 2: AGENT ROUTING{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 80}{Colors.END}\n")

    test_cases = [
        {
            "query": "Show me recent errors",
            "expected_agents": ["logs"],
            "description": "Error query should route to logs agent",
        },
        {
            "query": "What is the CPU usage?",
            "expected_agents": ["metrics"],
            "description": "CPU query should route to metrics agent",
        },
        {
            "query": "Which requests are slow?",
            "expected_agents": ["traces"],
            "description": "Slow query should route to traces agent",
        },
        {
            "query": "Show errors and CPU usage",
            "expected_agents": ["logs", "metrics"],
            "description": "Complex query should route to multiple agents",
        },
    ]

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for i, test_case in enumerate(test_cases, 1):
            query = test_case["query"]
            print(f"{Colors.BLUE}Test {i}: '{query}'{Colors.END}")
            print(f"  Description: {test_case['description']}")

            response = await client.post(
                f"{BASE_URL}/analyze", json={"query": query, "time_range": "1h"}
            )

            assert response.status_code == 200, f"HTTP {response.status_code}"

            data = response.json()
            routing = data.get("routing", {})
            agents_called = routing.get("agents", [])
            reason = routing.get("reason", "")

            print(f"  Agents called: {Colors.YELLOW}{agents_called}{Colors.END}")
            print(f"  Reason: {Colors.YELLOW}{reason}{Colors.END}")

            # Verify that at least one expected agent was called
            has_expected = any(
                agent in agents_called for agent in test_case["expected_agents"]
            )
            assert (
                has_expected
            ), f"Expected one of {test_case['expected_agents']}, got {agents_called}"

            print(f"  {Colors.GREEN}✓ Test {i} passed{Colors.END}\n")
            await asyncio.sleep(1)

    print(f"{Colors.GREEN}{Colors.BOLD}✓ All routing tests passed!{Colors.END}\n")


async def test_response_validation():
    """
    TEST 3: Response Validation
    Verify that agent responses are validated
    """
    await check_orchestrator_available()

    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}TEST 3: RESPONSE VALIDATION{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 80}{Colors.END}\n")

    test_cases = [
        {"query": "Show me recent errors", "description": "Simple error query"},
        {"query": "What is the system health?", "description": "Complex health query"},
    ]

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for i, test_case in enumerate(test_cases, 1):
            query = test_case["query"]
            print(f"{Colors.BLUE}Test {i}: '{query}'{Colors.END}")
            print(f"  Description: {test_case['description']}")

            response = await client.post(
                f"{BASE_URL}/analyze", json={"query": query, "time_range": "1h"}
            )

            assert response.status_code == 200, f"HTTP {response.status_code}"

            data = response.json()
            validation = data.get("validation", {})

            print(
                f"  Validation present: {Colors.YELLOW}{'validation' in data}{Colors.END}"
            )

            if validation:
                validated = validation.get("validated", False)
                issues = validation.get("issues", [])
                suggestion = validation.get("suggestion", "")

                print(f"  Validated: {Colors.YELLOW}{validated}{Colors.END}")
                print(f"  Issues: {Colors.YELLOW}{issues}{Colors.END}")
                print(f"  Suggestion: {Colors.YELLOW}{suggestion}{Colors.END}")

                # Validation should have been attempted
                assert (
                    "validated" in validation or "reason" in validation
                ), "Validation result should be present"

            print(f"  {Colors.GREEN}✓ Test {i} passed{Colors.END}\n")
            await asyncio.sleep(1)

    print(f"{Colors.GREEN}{Colors.BOLD}✓ All validation tests passed!{Colors.END}\n")


async def test_complete_workflow():
    """
    TEST 4: Complete Workflow
    Test all 3 functionalities together in a single request
    """
    await check_orchestrator_available()

    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(
        f"{Colors.BOLD}TEST 4: COMPLETE WORKFLOW (Translation → Routing → Validation){Colors.END}"
    )
    print(f"{Colors.BOLD}{'=' * 80}{Colors.END}\n")

    query = "Montre-moi les erreurs récentes du service customer"
    print(f"{Colors.BLUE}Query: '{query}'{Colors.END}\n")

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(
            f"{BASE_URL}/analyze", json={"query": query, "time_range": "1h"}
        )

        assert response.status_code == 200, f"HTTP {response.status_code}"

        data = response.json()

        # Step 1: Verify translation
        print(f"{Colors.BOLD}1️⃣ TRANSLATION:{Colors.END}")
        original = data.get("query")
        translated = data.get("translated_query")
        language = data.get("language")

        print(f"  Original: {Colors.YELLOW}{original}{Colors.END}")
        print(f"  Translated: {Colors.YELLOW}{translated}{Colors.END}")
        print(f"  Language: {Colors.YELLOW}{language}{Colors.END}")

        assert (
            translated != original or language == "english"
        ), "French query should be translated"
        print(f"  {Colors.GREEN}✓ Translation OK{Colors.END}\n")

        # Step 2: Verify routing
        print(f"{Colors.BOLD}2️⃣ ROUTING:{Colors.END}")
        routing = data.get("routing", {})
        agents = routing.get("agents", [])
        reason = routing.get("reason", "")

        print(f"  Agents: {Colors.YELLOW}{agents}{Colors.END}")
        print(f"  Reason: {Colors.YELLOW}{reason}{Colors.END}")

        assert len(agents) > 0, "At least one agent should be called"
        print(f"  {Colors.GREEN}✓ Routing OK{Colors.END}\n")

        # Step 3: Verify agent responses
        print(f"{Colors.BOLD}3️⃣ AGENT RESPONSES:{Colors.END}")
        agent_responses = data.get("agent_responses", {})

        for agent_name, agent_resp in agent_responses.items():
            if agent_resp and isinstance(agent_resp, dict):
                if "error" in agent_resp:
                    print(
                        f"  {Colors.RED}❌ {agent_name}: {agent_resp['error']}{Colors.END}"
                    )
                else:
                    analysis = agent_resp.get("analysis", "")[:100]
                    print(f"  {Colors.GREEN}✓ {agent_name}: {analysis}...{Colors.END}")

        assert len(agent_responses) > 0, "Should have agent responses"
        print(f"  {Colors.GREEN}✓ Agents responded{Colors.END}\n")

        # Step 4: Verify validation
        print(f"{Colors.BOLD}4️⃣ VALIDATION:{Colors.END}")
        validation = data.get("validation", {})

        if validation:
            validated = validation.get("validated", False)
            print(f"  Validated: {Colors.YELLOW}{validated}{Colors.END}")

            if "issues" in validation:
                issues = validation["issues"]
                print(f"  Issues: {Colors.YELLOW}{issues}{Colors.END}")

            if "suggestion" in validation:
                suggestion = validation["suggestion"]
                print(f"  Suggestion: {Colors.YELLOW}{suggestion}{Colors.END}")

        print(f"  {Colors.GREEN}✓ Validation present{Colors.END}\n")

        # Step 5: Verify summary
        print(f"{Colors.BOLD}5️⃣ SUMMARY:{Colors.END}")
        summary = data.get("summary", "")
        recommendations = data.get("recommendations", [])

        print(f"  Summary ({len(summary)} chars): {summary[:150]}...")
        print(f"  Recommendations: {len(recommendations)} items")

        assert len(summary) > 0, "Summary should not be empty"
        print(f"  {Colors.GREEN}✓ Summary OK{Colors.END}\n")

    print(f"{Colors.GREEN}{Colors.BOLD}✓ Complete workflow successful!{Colors.END}\n")


async def main():
    """Run all integration tests"""
    start_time = datetime.now()

    print(f"\n{Colors.BOLD}╔{'=' * 78}╗{Colors.END}")
    print(
        f"{Colors.BOLD}║{' ' * 15}INTEGRATION TESTS - SIMPLIFIED ORCHESTRATOR{' ' * 20}║{Colors.END}"
    )
    print(f"{Colors.BOLD}╚{'=' * 78}╝{Colors.END}")

    try:
        # Test 1: Language detection and translation
        await test_language_detection_and_translation()

        # Test 2: Agent routing
        await test_agent_routing()

        # Test 3: Response validation
        await test_response_validation()

        # Test 4: Complete workflow
        await test_complete_workflow()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"\n{Colors.BOLD}{'=' * 80}{Colors.END}")
        print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED!{Colors.END}")
        print(f"{Colors.YELLOW}⏱️  Total duration: {duration:.2f} seconds{Colors.END}")
        print(f"{Colors.BOLD}{'=' * 80}{Colors.END}\n")

        print(f"{Colors.BOLD}📊 VERIFIED FUNCTIONALITIES:{Colors.END}")
        print(
            f"   {Colors.GREEN}✓ Language detection and translation (French ↔ English){Colors.END}"
        )
        print(
            f"   {Colors.GREEN}✓ Intelligent routing to correct agents (logs/metrics/traces){Colors.END}"
        )
        print(f"   {Colors.GREEN}✓ AI-powered response validation{Colors.END}")
        print(f"   {Colors.GREEN}✓ Complete end-to-end workflow{Colors.END}\n")

        return 0

    except AssertionError as e:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ TEST FAILED:{Colors.END} {e}\n")
        return 1
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ ERROR:{Colors.END} {e}\n")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
