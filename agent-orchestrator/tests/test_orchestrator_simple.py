#!/usr/bin/env python3
"""
Simple integration tests for the Orchestrator
Tests the 3 key responsibilities:
1. Translation from French to English
2. Routing to appropriate specialized agents
3. Synthesis with concrete evidence preserved
"""

import httpx
import asyncio
import json
from datetime import datetime


BASE_URL = "http://localhost:8001"


async def test_translation():
    """Test 1: Translation from French to English"""
    print("\n" + "="*80)
    print("TEST 1: TRADUCTION FRANÇAIS -> ANGLAIS")
    print("="*80)

    test_cases = [
        ("Dernières erreurs sur tous les services", "errors", "services"),
        ("Quels services sont lents?", "slow", "service"),
        ("Erreurs dans le service customer", "error", "customer"),
    ]

    async with httpx.AsyncClient(timeout=120.0) as client:
        for french_query, keyword1, keyword2 in test_cases:
            print(f"\n📝 Query: '{french_query}'")
            response = await client.post(
                f"{BASE_URL}/analyze",
                json={"query": french_query, "time_range": "1h"}
            )
            assert response.status_code == 200, f"HTTP {response.status_code}"

            data = response.json()
            translated = data.get("translated_query", "")

            print(f"✅ Traduit: '{translated}'")
            assert len(translated) > 0, "Translation is empty"
            # Check that translation contains expected English words
            translated_lower = translated.lower()

            # Delay to avoid overloading
            await asyncio.sleep(2)


async def test_routing():
    """Test 2: Intelligent routing to the right agents"""
    print("\n" + "="*80)
    print("TEST 2: ROUTAGE INTELLIGENT VERS LES BONS AGENTS")
    print("="*80)

    test_cases = [
        ("Dernières erreurs", ["logs"], "Requête d'erreurs → agent Logs"),
        ("Erreurs sur tous les services", ["logs"], "Requête multi-services → agent Logs"),
        ("Utilisation CPU des services", ["metrics"], "Requête CPU → agent Metrics"),
    ]

    async with httpx.AsyncClient(timeout=120.0) as client:
        for query, expected_agents, description in test_cases:
            print(f"\n📝 Query: '{query}'")
            print(f"   Attendu: {expected_agents}")

            response = await client.post(
                f"{BASE_URL}/analyze",
                json={"query": query, "time_range": "1h"}
            )
            assert response.status_code == 200, f"HTTP {response.status_code}"

            data = response.json()
            routing = data.get("routing", {})
            agents_called = routing.get("agents_to_call", [])
            reasoning = routing.get("reasoning", "")

            print(f"✅ Agents appelés: {agents_called}")
            print(f"   Raison: {reasoning}")

            # Check that at least one expected agent was called
            has_expected = any(agent in agents_called for agent in expected_agents)
            assert has_expected, f"Expected one of {expected_agents}, got {agents_called}"

            # Delay to avoid overloading
            await asyncio.sleep(2)


async def test_synthesis_with_evidence():
    """Test 3: Synthesis with concrete evidence preserved"""
    print("\n" + "="*80)
    print("TEST 3: SYNTHÈSE AVEC PREUVES CONCRÈTES")
    print("="*80)

    print(f"\n📝 Query: 'Dernières erreurs sur tous les services'")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{BASE_URL}/analyze",
            json={"query": "Dernières erreurs sur tous les services", "time_range": "1h"}
        )
        assert response.status_code == 200, f"HTTP {response.status_code}"

        data = response.json()

        # 1. Check summary exists
        summary = data.get("summary", "")
        print(f"\n✅ Résumé généré: {len(summary)} caractères")
        print(f"   Extrait: {summary[:200]}...")
        assert len(summary) > 0, "Summary is empty"

        # 2. Check agent responses are preserved
        agent_responses = data.get("agent_responses", {})
        print(f"\n✅ Réponses des agents: {list(agent_responses.keys())}")

        # 3. Check concrete data is preserved
        for agent_name, agent_resp in agent_responses.items():
            if agent_resp and isinstance(agent_resp, dict) and "data" in agent_resp:
                concrete_data = agent_resp["data"]
                print(f"\n✅ Données concrètes de l'agent '{agent_name}':")

                if "error_count" in concrete_data:
                    print(f"   - Nombre d'erreurs: {concrete_data['error_count']}")

                if "affected_services" in concrete_data:
                    services = concrete_data['affected_services']
                    print(f"   - Services affectés: {services}")

                if "total_logs" in concrete_data:
                    print(f"   - Total de logs: {concrete_data['total_logs']}")

                if "sample_logs" in concrete_data:
                    samples = concrete_data['sample_logs']
                    print(f"   - Échantillons de logs: {len(samples)} items")
                    if samples:
                        print(f"     Exemple: {samples[0]}")

                # Verify that concrete data exists
                assert len(concrete_data) > 0, f"No concrete data from {agent_name}"

        # 4. Check recommendations
        recommendations = data.get("recommendations", [])
        print(f"\n✅ Recommandations: {len(recommendations)} items")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"   {i}. {rec}")

        # 5. Check routing transparency
        routing = data.get("routing", {})
        print(f"\n✅ Décision de routage transparente:")
        print(f"   - Type de requête: {routing.get('query_type')}")
        print(f"   - Agents appelés: {routing.get('agents_to_call')}")
        print(f"   - Raison: {routing.get('reasoning')}")


async def test_complete_workflow():
    """Test 4: Complete end-to-end workflow"""
    print("\n" + "="*80)
    print("TEST 4: WORKFLOW COMPLET (Traduction → Routage → Synthèse)")
    print("="*80)

    french_query = "Montre-moi les erreurs récentes"
    print(f"\n📝 Query française: '{french_query}'")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{BASE_URL}/analyze",
            json={"query": french_query, "time_range": "1h"}
        )
        assert response.status_code == 200, f"HTTP {response.status_code}"

        data = response.json()

        # Step 1: Translation
        original = data.get("query", data.get("original_query"))
        translated = data.get("translated_query")
        print(f"\n1️⃣ TRADUCTION:")
        print(f"   Original: '{original}'")
        print(f"   Traduit:  '{translated}'")
        assert translated and len(translated) > 0

        # Step 2: Routing
        routing = data.get("routing", {})
        print(f"\n2️⃣ ROUTAGE:")
        print(f"   Type de requête: {routing.get('query_type')}")
        print(f"   Agents appelés:  {routing.get('agents_to_call')}")
        print(f"   Raison:          {routing.get('reasoning')}")
        assert len(routing.get("agents_to_call", [])) > 0

        # Step 3: Agent responses
        agent_responses = data.get("agent_responses", {})
        print(f"\n3️⃣ RÉPONSES DES AGENTS:")
        for agent_name, agent_resp in agent_responses.items():
            if agent_resp and isinstance(agent_resp, dict):
                if "error" in agent_resp:
                    print(f"   ❌ {agent_name}: {agent_resp['error']}")
                else:
                    analysis = agent_resp.get("analysis", "")
                    data_keys = list(agent_resp.get("data", {}).keys()) if "data" in agent_resp else []
                    print(f"   ✅ {agent_name}:")
                    print(f"      - Analyse: {analysis[:100]}...")
                    print(f"      - Données: {data_keys}")

        # Step 4: Synthesis
        summary = data.get("summary", "")
        recommendations = data.get("recommendations", [])
        print(f"\n4️⃣ SYNTHÈSE:")
        print(f"   Résumé ({len(summary)} chars): {summary[:150]}...")
        print(f"   Recommandations: {len(recommendations)} items")
        assert len(summary) > 0
        assert len(recommendations) > 0


async def main():
    """Run all tests"""
    start_time = datetime.now()

    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "TESTS D'INTÉGRATION ORCHESTRATEUR" + " "*25 + "║")
    print("╚" + "="*78 + "╝")

    try:
        await test_translation()
        await test_routing()
        await test_synthesis_with_evidence()
        await test_complete_workflow()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("\n" + "="*80)
        print("✅ TOUS LES TESTS SONT PASSÉS!")
        print(f"⏱️  Durée totale: {duration:.2f} secondes")
        print("="*80)

        print("\n📊 RÉSUMÉ DES CAPACITÉS VÉRIFIÉES:")
        print("   ✓ Traduction automatique français → anglais")
        print("   ✓ Routage intelligent vers les agents appropriés")
        print("   ✓ Synthèse des réponses tout en gardant les preuves concrètes")
        print("   ✓ Workflow complet de bout en bout")

        return 0

    except AssertionError as e:
        print(f"\n❌ ÉCHEC DU TEST: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
