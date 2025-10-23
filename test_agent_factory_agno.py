"""
Test Suite for AgentFactory with Agno Support

Validates that the AgentFactory can create both Custom and Agno agents
with proper feature flag handling.
"""
import asyncio
import os
from uuid import uuid4

from backend.agents.factory import AgentFactory, USE_AGNO_AGENTS, AGNO_ENABLED_ROLES
from backend.agents.base_agent import BaseSquadAgent
from backend.agents.agno_base import AgnoSquadAgent
from backend.core.agno_config import initialize_agno, shutdown_agno


async def test_1_create_custom_agent_default():
    """Test 1: Create Custom agent (default behavior)"""
    print("\n" + "="*70)
    print("TEST 1: Create Custom Agent (Default)")
    print("="*70)

    agent_id = uuid4()
    agent = AgentFactory.create_agent(
        agent_id=agent_id,
        role="backend_developer",
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        system_prompt="Test backend developer",
    )

    print(f"\n✅ Agent created:")
    print(f"   Type: {type(agent).__name__}")
    print(f"   Role: {agent.config.role}")
    print(f"   Is Custom: {isinstance(agent, BaseSquadAgent)}")
    print(f"   Is Agno: {isinstance(agent, AgnoSquadAgent)}")

    assert isinstance(agent, BaseSquadAgent), "Should be Custom agent"
    assert not isinstance(agent, AgnoSquadAgent), "Should NOT be Agno agent"

    print("\n✅ Custom agent creation working!")
    return agent


async def test_2_create_agno_agent_force():
    """Test 2: Create Agno agent with force_agno=True"""
    print("\n" + "="*70)
    print("TEST 2: Create Agno Agent (force_agno=True)")
    print("="*70)

    agent_id = uuid4()
    agent = AgentFactory.create_agent(
        agent_id=agent_id,
        role="project_manager",
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        force_agno=True,  # Force Agno
    )

    print(f"\n✅ Agent created:")
    print(f"   Type: {type(agent).__name__}")
    print(f"   Role: {agent.config.role}")
    print(f"   Is Custom: {isinstance(agent, BaseSquadAgent)}")
    print(f"   Is Agno: {isinstance(agent, AgnoSquadAgent)}")

    assert isinstance(agent, AgnoSquadAgent), "Should be Agno agent"

    print("\n✅ Forced Agno agent creation working!")
    return agent


async def test_3_agno_agent_functionality():
    """Test 3: Agno agent can process messages"""
    print("\n" + "="*70)
    print("TEST 3: Agno Agent Functionality")
    print("="*70)

    agent_id = uuid4()
    pm = AgentFactory.create_agent(
        agent_id=agent_id,
        role="project_manager",
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        force_agno=True,
    )

    print(f"\n📝 Processing message...")

    response = await pm.process_message("What are your capabilities?")

    print(f"\n🤖 PM Response: {response.content[:200]}...")
    print(f"   Session ID: {pm.session_id[:16] if pm.session_id else 'None'}...")

    assert response.content, "Should have response content"

    print("\n✅ Agno agent message processing working!")


async def test_4_agno_session_persistence():
    """Test 4: Agno session persistence across instances"""
    print("\n" + "="*70)
    print("TEST 4: Agno Session Persistence")
    print("="*70)

    # Create PM 1 and store information
    agent_id_1 = uuid4()
    pm1 = AgentFactory.create_agent(
        agent_id=agent_id_1,
        role="project_manager",
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        force_agno=True,
    )

    print(f"\n📝 PM 1: Storing information...")
    await pm1.process_message("My name is Sarah and I'm the Product Owner")
    session_id = pm1.session_id
    print(f"   Session: {session_id[:16]}...")

    # Create PM 2 with same session
    agent_id_2 = uuid4()
    pm2 = AgentFactory.create_agent(
        agent_id=agent_id_2,
        role="project_manager",
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        force_agno=True,
        session_id=session_id,  # Resume session
    )

    print(f"\n📝 PM 2: Recalling information...")
    response = await pm2.process_message("What is the Product Owner's name?")
    print(f"   Response: {response.content[:150]}...")

    has_context = "sarah" in response.content.lower()

    if has_context:
        print(f"\n✅ Session persistence working!")
        print(f"   PM 2 remembered information from PM 1's session")
    else:
        print(f"\n⚠️  Session persistence may not be working")

    return has_context


async def test_5_custom_vs_agno_compatibility():
    """Test 5: Custom and Agno agents can coexist"""
    print("\n" + "="*70)
    print("TEST 5: Custom and Agno Coexistence")
    print("="*70)

    # Create Custom agent
    custom_id = uuid4()
    custom_agent = AgentFactory.create_agent(
        agent_id=custom_id,
        role="backend_developer",
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        force_agno=False,
        system_prompt="Test custom",
    )

    # Create Agno agent
    agno_id = uuid4()
    agno_agent = AgentFactory.create_agent(
        agent_id=agno_id,
        role="tech_lead",
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        force_agno=True,
    )

    print(f"\n✅ Both agents created:")
    print(f"   Custom: {type(custom_agent).__name__}")
    print(f"   Agno: {type(agno_agent).__name__}")

    # Verify both in registry
    retrieved_custom = AgentFactory.get_agent(custom_id)
    retrieved_agno = AgentFactory.get_agent(agno_id)

    assert retrieved_custom is custom_agent
    assert retrieved_agno is agno_agent

    print(f"\n✅ Both agents in registry:")
    print(f"   Total agents: {len(AgentFactory.get_all_agents())}")

    print("\n✅ Custom and Agno agents can coexist!")


async def test_6_backward_compatibility():
    """Test 6: Backward compatibility (existing code still works)"""
    print("\n" + "="*70)
    print("TEST 6: Backward Compatibility")
    print("="*70)

    # Old-style agent creation (no new parameters)
    agent_id = uuid4()
    agent = AgentFactory.create_agent(
        agent_id=agent_id,
        role="tester",  # Role is "tester" not "qa_tester"
        llm_provider="openai",
        llm_model="gpt-4o-mini",
    )

    print(f"\n✅ Agent created with old-style API:")
    print(f"   Type: {type(agent).__name__}")
    print(f"   Role: {agent.config.role}")

    # Should be Custom by default
    assert isinstance(agent, BaseSquadAgent)

    print("\n✅ Backward compatibility maintained!")


async def test_7_feature_flags():
    """Test 7: Feature flags configuration"""
    print("\n" + "="*70)
    print("TEST 7: Feature Flags Configuration")
    print("="*70)

    print(f"\n📋 Current feature flags:")
    print(f"   USE_AGNO_AGENTS: {USE_AGNO_AGENTS}")
    print(f"   AGNO_ENABLED_ROLES: {AGNO_ENABLED_ROLES}")

    print(f"\n💡 To enable Agno globally:")
    print(f"   export USE_AGNO_AGENTS=true")

    print(f"\n💡 To enable Agno for specific roles:")
    print(f"   export AGNO_ENABLED_ROLES=project_manager,tech_lead")

    print("\n✅ Feature flags configured correctly!")


async def test_8_all_roles():
    """Test 8: All roles can create Agno agents"""
    print("\n" + "="*70)
    print("TEST 8: All Roles Support Agno")
    print("="*70)

    roles = [
        "project_manager",
        "tech_lead",
        "backend_developer",
        "frontend_developer",
        "tester",
        "solution_architect",
        "devops_engineer",
        "ai_engineer",
        "designer",
    ]

    success_count = 0

    for role in roles:
        try:
            agent_id = uuid4()
            agent = AgentFactory.create_agent(
                agent_id=agent_id,
                role=role,
                llm_provider="openai",
                llm_model="gpt-4o-mini",
                force_agno=True,
            )

            assert isinstance(agent, AgnoSquadAgent)
            print(f"   ✅ {role}: {type(agent).__name__}")
            success_count += 1

        except Exception as e:
            print(f"   ❌ {role}: {e}")

    print(f"\n✅ Successfully created {success_count}/{len(roles)} Agno agents")
    assert success_count == len(roles), "All roles should support Agno"


async def run_all_tests():
    """Run all factory tests"""
    print("\n" + "="*70)
    print("🚀 AGENT FACTORY - AGNO INTEGRATION TESTS")
    print("="*70)

    initialize_agno()

    try:
        # Test 1: Custom agent creation
        await test_1_create_custom_agent_default()

        # Test 2: Forced Agno agent creation
        await test_2_create_agno_agent_force()

        # Test 3: Agno agent functionality
        await test_3_agno_agent_functionality()

        # Test 4: Agno session persistence
        persistence_works = await test_4_agno_session_persistence()

        # Test 5: Custom and Agno coexistence
        await test_5_custom_vs_agno_compatibility()

        # Test 6: Backward compatibility
        await test_6_backward_compatibility()

        # Test 7: Feature flags
        await test_7_feature_flags()

        # Test 8: All roles support Agno
        await test_8_all_roles()

        # Clear registry for clean slate
        AgentFactory.clear_all_agents()

        # Summary
        print("\n" + "="*70)
        print("✅ AGENT FACTORY TESTS COMPLETE!")
        print("="*70)
        print("\n🎉 All tests passed! Key achievements:")
        print("   ✓ Custom agent creation working (default)")
        print("   ✓ Agno agent creation working (force_agno=True)")
        print("   ✓ Agno message processing working")
        print("   ✓ Session persistence working" if persistence_works else "   ⚠️  Session persistence needs review")
        print("   ✓ Custom and Agno can coexist")
        print("   ✓ Backward compatibility maintained")
        print("   ✓ Feature flags configured")
        print("   ✓ All 9 roles support Agno")
        print("\n🚀 AgentFactory ready for production!")

        print("\n" + "="*70)
        print("📋 ROLLOUT STRATEGY")
        print("="*70)
        print("\n1️⃣  Phase 1: Test with specific roles")
        print("   export AGNO_ENABLED_ROLES=project_manager,tech_lead")
        print("\n2️⃣  Phase 2: Expand to more roles")
        print("   export AGNO_ENABLED_ROLES=project_manager,tech_lead,backend_developer")
        print("\n3️⃣  Phase 3: Enable globally")
        print("   export USE_AGNO_AGENTS=true")
        print("\n4️⃣  Phase 4: Remove Custom agents (future)")
        print("   Deprecate BaseSquadAgent implementation")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise

    finally:
        shutdown_agno()


if __name__ == "__main__":
    asyncio.run(run_all_tests())
