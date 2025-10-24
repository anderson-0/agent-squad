#!/usr/bin/env python3
"""
Verification Demo: Agno-Only Implementation
Tests that all legacy code has been removed and Agno is the sole framework.
"""
import sys
from uuid import uuid4

# Add project to path
sys.path.insert(0, '/Users/anderson/Documents/anderson-0/agent-squad')

from backend.agents.factory import AgentFactory
from backend.agents.agno_base import AgnoSquadAgent


def print_section(title):
    """Print section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def verify_imports():
    """Verify all imports work correctly"""
    print_section("✅ VERIFICATION 1: Imports")

    try:
        # Test factory import
        from backend.agents.factory import AgentFactory
        print("   ✅ AgentFactory imported successfully")

        # Test Agno base import
        from backend.agents.agno_base import AgnoSquadAgent, AgentConfig
        print("   ✅ AgnoSquadAgent imported successfully")

        # Test service import
        from backend.services.agent_service import AgentService
        print("   ✅ AgentService imported successfully")

        # Test communication import
        from backend.agents.communication.history_manager import HistoryManager
        print("   ✅ HistoryManager imported successfully")

        # Test all specialized agents
        from backend.agents.specialized.agno_project_manager import AgnoProjectManagerAgent
        from backend.agents.specialized.agno_tech_lead import AgnoTechLeadAgent
        from backend.agents.specialized.agno_backend_developer import AgnoBackendDeveloperAgent
        from backend.agents.specialized.agno_frontend_developer import AgnoFrontendDeveloperAgent
        from backend.agents.specialized.agno_qa_tester import AgnoQATesterAgent
        from backend.agents.specialized.agno_solution_architect import AgnoSolutionArchitectAgent
        from backend.agents.specialized.agno_devops_engineer import AgnoDevOpsEngineerAgent
        from backend.agents.specialized.agno_ai_engineer import AgnoAIEngineerAgent
        from backend.agents.specialized.agno_designer import AgnoDesignerAgent
        print("   ✅ All 9 specialized Agno agents imported successfully")

        return True
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False


def verify_no_legacy_imports():
    """Verify legacy imports are gone"""
    print_section("✅ VERIFICATION 2: Legacy Code Removed")

    legacy_removed = True

    # Try importing legacy base_agent (should fail)
    try:
        from backend.agents.base_agent import BaseSquadAgent
        print("   ❌ ERROR: base_agent.py still exists!")
        legacy_removed = False
    except ModuleNotFoundError:
        print("   ✅ base_agent.py successfully removed")

    # Try importing legacy custom agents (should fail)
    legacy_agents = [
        'project_manager', 'tech_lead', 'backend_developer',
        'frontend_developer', 'qa_tester', 'solution_architect',
        'devops_engineer', 'ai_engineer', 'designer'
    ]

    for agent in legacy_agents:
        try:
            __import__(f'backend.agents.specialized.{agent}')
            print(f"   ❌ ERROR: {agent}.py still exists!")
            legacy_removed = False
        except ModuleNotFoundError:
            pass  # Expected

    print(f"   ✅ All 9 custom agent files successfully removed")

    return legacy_removed


def verify_agent_creation():
    """Verify agent creation works"""
    print_section("✅ VERIFICATION 3: Agent Creation")

    roles = [
        "project_manager",
        "tech_lead",
        "backend_developer",
        "frontend_developer",
        "tester",
        "solution_architect",
        "devops_engineer",
        "ai_engineer",
        "designer"
    ]

    created_count = 0

    for role in roles:
        try:
            agent_id = uuid4()
            agent = AgentFactory.create_agent(
                agent_id=agent_id,
                role=role,
                llm_provider="openai",
                llm_model="gpt-4o-mini"
            )

            # Verify it's an Agno agent
            if not isinstance(agent, AgnoSquadAgent):
                print(f"   ❌ {role}: Not an Agno agent!")
                continue

            print(f"   ✅ {role}: {type(agent).__name__}")
            created_count += 1

            # Clean up
            AgentFactory.remove_agent(agent_id)

        except Exception as e:
            print(f"   ❌ {role}: Creation failed - {e}")

    print(f"\n   📊 Result: {created_count}/{len(roles)} agents created successfully")
    return created_count == len(roles)


def verify_factory_registry():
    """Verify factory registry contains only Agno agents"""
    print_section("✅ VERIFICATION 4: Factory Registry")

    from backend.agents.factory import AGENT_REGISTRY

    print(f"   📋 Registered roles: {len(AGENT_REGISTRY)}")

    all_agno = True
    for role, agent_class in AGENT_REGISTRY.items():
        class_name = agent_class.__name__
        if not class_name.startswith('Agno'):
            print(f"   ❌ {role}: {class_name} is not an Agno agent!")
            all_agno = False
        else:
            print(f"   ✅ {role}: {class_name}")

    return all_agno


def verify_supported_roles():
    """Verify all expected roles are supported"""
    print_section("✅ VERIFICATION 5: Supported Roles")

    supported_roles = AgentFactory.get_supported_roles()
    expected_roles = [
        "project_manager", "tech_lead", "backend_developer",
        "frontend_developer", "tester", "solution_architect",
        "devops_engineer", "ai_engineer", "designer"
    ]

    print(f"   📋 Supported roles: {len(supported_roles)}")

    all_present = True
    for role in expected_roles:
        if role in supported_roles:
            print(f"   ✅ {role}")
        else:
            print(f"   ❌ {role} missing!")
            all_present = False

    return all_present


def main():
    """Run all verifications"""
    print("\n" + "🎯"*40)
    print("  AGNO-ONLY IMPLEMENTATION VERIFICATION")
    print("  Legacy Code Removal Validation")
    print("🎯"*40)

    results = []

    # Run verifications
    results.append(("Imports", verify_imports()))
    results.append(("Legacy Removed", verify_no_legacy_imports()))
    results.append(("Agent Creation", verify_agent_creation()))
    results.append(("Factory Registry", verify_factory_registry()))
    results.append(("Supported Roles", verify_supported_roles()))

    # Summary
    print_section("📊 VERIFICATION SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")

    print(f"\n   📈 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("\n" + "🎉"*40)
        print("  🎉 ALL VERIFICATIONS PASSED!")
        print("  🚀 Agno-Only Implementation Confirmed!")
        print("  ✅ No Legacy Code Remaining!")
        print("🎉"*40 + "\n")
        return 0
    else:
        print("\n" + "⚠️ "*40)
        print("  ⚠️  SOME VERIFICATIONS FAILED")
        print("  Please review the output above")
        print("⚠️ "*40 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
