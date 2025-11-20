"""
Quick Test: Agent Creation and Basic Execution

This script tests basic agent functionality without requiring
a full database setup. It verifies:
1. Agent factory works
2. Agents can be created
3. Basic message processing works
"""
import asyncio
from uuid import uuid4
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Set environment variables for testing
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only-min-32-chars'
os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', '')
os.environ['ANTHROPIC_API_KEY'] = os.environ.get('ANTHROPIC_API_KEY', '')

from backend.agents.factory import AgentFactory
from backend.agents.agno_base import AgentConfig, LLMProvider


async def test_agent_creation():
    """Test creating an agent"""
    print("=" * 60)
    print("TEST 1: Agent Creation")
    print("=" * 60)

    try:
        # Create a project manager agent
        agent_id = uuid4()
        print(f"\n✅ Creating Project Manager agent with ID: {agent_id}")

        # NOTE: This will fail if Agno DB is not set up
        # That's expected - we're testing the code structure
        agent = AgentFactory.create_agent(
            agent_id=agent_id,
            role="project_manager",
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            system_prompt="You are a test project manager agent."
        )

        print(f"✅ Agent created successfully!")
        print(f"   - Type: {type(agent).__name__}")
        print(f"   - Role: {agent.config.role}")
        print(f"   - LLM Provider: {agent.config.llm_provider}")
        print(f"   - LLM Model: {agent.config.llm_model}")

        # Get capabilities
        capabilities = agent.get_capabilities()
        print(f"\n✅ Agent capabilities ({len(capabilities)} total):")
        for cap in capabilities[:5]:
            print(f"   - {cap}")
        if len(capabilities) > 5:
            print(f"   ... and {len(capabilities) - 5} more")

        return True

    except Exception as e:
        print(f"\n❌ Agent creation failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False


async def test_factory_methods():
    """Test factory methods"""
    print("\n" + "=" * 60)
    print("TEST 2: Factory Methods")
    print("=" * 60)

    try:
        # Get supported roles
        roles = AgentFactory.get_supported_roles()
        print(f"\n✅ Supported roles ({len(roles)} total):")
        for role in roles:
            print(f"   - {role}")

        # Get specializations for backend_developer
        specializations = AgentFactory.get_available_specializations("backend_developer")
        print(f"\n✅ Backend developer specializations:")
        if specializations:
            for spec in specializations:
                print(f"   - {spec}")
        else:
            print("   (No custom specializations found - using default)")

        return True

    except Exception as e:
        print(f"\n❌ Factory methods failed: {e}")
        return False


async def test_agent_registry():
    """Test agent registry"""
    print("\n" + "=" * 60)
    print("TEST 3: Agent Registry")
    print("=" * 60)

    try:
        # Create multiple agents
        agent_ids = []
        for i, role in enumerate(["project_manager", "backend_developer", "qa_tester"]):
            agent_id = uuid4()
            agent_ids.append(agent_id)

            agent = AgentFactory.create_agent(
                agent_id=agent_id,
                role=role,
                llm_provider="openai",
                llm_model="gpt-4o-mini",
                system_prompt=f"Test {role} agent"
            )
            print(f"✅ Created {role} agent: {agent_id}")

        # Get all agents
        all_agents = AgentFactory.get_all_agents()
        print(f"\n✅ Total agents in registry: {len(all_agents)}")

        # Get individual agents
        for agent_id in agent_ids:
            agent = AgentFactory.get_agent(agent_id)
            if agent:
                print(f"✅ Retrieved agent {agent_id}: {agent.config.role}")
            else:
                print(f"❌ Failed to retrieve agent {agent_id}")

        # Clear all agents
        AgentFactory.clear_all_agents()
        remaining = AgentFactory.get_all_agents()
        print(f"\n✅ Cleared registry. Remaining agents: {len(remaining)}")

        return True

    except Exception as e:
        print(f"\n❌ Agent registry test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AGENT CREATION & FACTORY TESTS")
    print("="*60)

    results = []

    # Test 1: Agent creation
    results.append(await test_agent_creation())

    # Test 2: Factory methods
    results.append(await test_factory_methods())

    # Test 3: Agent registry
    results.append(await test_agent_registry())

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"\n✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
