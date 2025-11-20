#!/usr/bin/env python3
"""
Diagnostic Test - Identify where test is hanging
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent))

from backend.agents.factory import AgentFactory

async def test_agent_creation():
    """Test just the agent creation"""

    print("\n🔍 Diagnostic Test: Agent Creation")
    print("=" * 60)

    # Test 1: Create PM agent
    print("\n1. Creating PM agent...")
    try:
        pm_agent = AgentFactory.create_agent(
            agent_id=uuid4(),
            role="project_manager",
            llm_provider="ollama",
            llm_model="llama3.2",
            temperature=0.7
        )
        print(f"   ✅ PM agent created: {pm_agent}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 2: Create Backend Dev agent
    print("\n2. Creating Backend Dev agent...")
    try:
        backend_agent = AgentFactory.create_agent(
            agent_id=uuid4(),
            role="backend_developer",
            llm_provider="ollama",
            llm_model="llama3.2",
            temperature=0.7
        )
        print(f"   ✅ Backend Dev agent created: {backend_agent}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 3: Process simple message with PM
    print("\n3. Testing PM agent message processing...")
    try:
        print("   ⏳ Sending message to PM agent...")
        response = await pm_agent.process_message(
            message="Hello, just say hi back in one word."
        )
        print(f"   ✅ PM response: {response.content[:100]}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("✅ All diagnostic tests passed!")
    return True

if __name__ == "__main__":
    print("\n🚀 Starting Diagnostic Test...\n")

    try:
        result = asyncio.run(test_agent_creation())
        if result:
            print("\n✅ Diagnostic complete - agents working!\n")
            sys.exit(0)
        else:
            print("\n❌ Diagnostic failed\n")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
