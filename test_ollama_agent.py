"""
Ollama Integration Test

Tests agent creation and message processing with local Ollama LLM.

Prerequisites:
1. Ollama installed: brew install ollama
2. Model pulled: ollama pull llama3.2
3. Ollama service running: curl http://localhost:11434/api/tags

Run:
    PYTHONPATH=$PWD backend/.venv/bin/python test_ollama_agent.py
"""
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.agents.factory import AgentFactory
from backend.core.config import settings


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_section(title: str, content: str):
    """Print a formatted section"""
    print(f"\n{title}:")
    print("-" * 70)
    print(content)


async def test_ollama_health():
    """Test if Ollama is running and accessible"""
    print_header("TEST 1: Ollama Health Check")

    import httpx

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")

            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])

                print(f"✅ Ollama is running at {settings.OLLAMA_BASE_URL}")
                print(f"✅ Available models: {len(models)}")

                if models:
                    print("\nInstalled models:")
                    for model in models:
                        print(f"  - {model['name']}")

                # Check if default model is available
                model_names = [m['name'] for m in models]
                if settings.OLLAMA_MODEL in model_names or any(settings.OLLAMA_MODEL in name for name in model_names):
                    print(f"\n✅ Default model '{settings.OLLAMA_MODEL}' is available")
                    return True
                else:
                    print(f"\n⚠️  Default model '{settings.OLLAMA_MODEL}' not found")
                    print(f"   Run: ollama pull {settings.OLLAMA_MODEL}")
                    return False
            else:
                print(f"❌ Ollama returned status {response.status_code}")
                return False

    except httpx.ConnectError:
        print(f"❌ Cannot connect to Ollama at {settings.OLLAMA_BASE_URL}")
        print("   Make sure Ollama is running: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False


async def test_agent_creation():
    """Test creating an agent with Ollama provider"""
    print_header("TEST 2: Agent Creation with Ollama")

    try:
        agent_id = uuid4()
        print(f"Creating agent with ID: {agent_id}")
        print(f"Provider: ollama")
        print(f"Model: {settings.OLLAMA_MODEL}")

        agent = AgentFactory.create_agent(
            agent_id=agent_id,
            role="project_manager",
            llm_provider="ollama",
            llm_model=settings.OLLAMA_MODEL,
            temperature=0.7
        )

        print(f"\n✅ Agent created successfully")
        print(f"   Role: {agent.config.role}")
        print(f"   Agent ID: {agent.agent_id}")
        print(f"   LLM Provider: {agent.config.llm_provider}")
        print(f"   LLM Model: {agent.config.llm_model}")

        return agent
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_message_processing(agent):
    """Test processing a simple message"""
    print_header("TEST 3: Message Processing")

    if not agent:
        print("❌ No agent available (skipping test)")
        return False

    try:
        message = "Hello! Can you briefly introduce yourself and tell me what you can help with? Keep it short (2-3 sentences)."

        print(f"Sending message: \"{message}\"")
        print("Processing with Ollama (this may take a few seconds)...")

        response = await agent.process_message(
            message=message,
            context={}
        )

        print_section("✅ Response received", response.content)

        if response.thinking:
            print_section("Agent Thinking", response.thinking)

        if response.metadata:
            print_section("Metadata", str(response.metadata))

        print(f"\n✅ Message processed successfully")
        print(f"   Session ID: {agent.session_id}")
        return True

    except Exception as e:
        print(f"❌ Failed to process message: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_task_planning(agent):
    """Test agent's ability to create a plan"""
    print_header("TEST 4: Task Planning")

    if not agent:
        print("❌ No agent available (skipping test)")
        return False

    try:
        message = "Create a simple 3-step plan for implementing user authentication in a web app."

        print(f"Sending message: \"{message}\"")
        print("Processing...")

        response = await agent.process_message(
            message=message,
            context={}
        )

        print_section("✅ Response received", response.content)

        if response.action_items:
            print_section("Action Items", "\n".join([f"  - {item}" for item in response.action_items]))

        print(f"\n✅ Task planning successful")
        return True

    except Exception as e:
        print(f"❌ Failed task planning: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_code_model():
    """Test with a code-focused model (if available)"""
    print_header("TEST 5: Code Model Test (Optional)")

    try:
        # Check if codellama is available
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            models = response.json().get("models", [])
            model_names = [m['name'] for m in models]

            if not any("codellama" in name for name in model_names):
                print("⏭️  CodeLlama not installed (skipping)")
                print("   To install: ollama pull codellama")
                return True

        # Create agent with codellama
        agent_id = uuid4()
        agent = AgentFactory.create_agent(
            agent_id=agent_id,
            role="backend_developer",
            llm_provider="ollama",
            llm_model="codellama",
            temperature=0.5
        )

        print("✅ CodeLlama agent created")

        # Test code generation
        message = "Write a simple Python function that checks if a number is prime. Just the function, no explanation."

        print(f"\nSending message: \"{message}\"")
        print("Processing...")

        response = await agent.process_message(
            message=message,
            context={}
        )

        print_section("✅ Response received", response.content)

        return True

    except Exception as e:
        print(f"⚠️  Code model test failed: {e}")
        return True  # Don't fail the whole test suite


async def run_all_tests():
    """Run all tests"""
    print("\n" + "🔬" * 35)
    print(" " * 10 + "OLLAMA INTEGRATION TEST SUITE")
    print("🔬" * 35)

    print(f"\nConfiguration:")
    print(f"  Ollama URL: {settings.OLLAMA_BASE_URL}")
    print(f"  Default Model: {settings.OLLAMA_MODEL}")

    # Test 1: Health check
    health_ok = await test_ollama_health()
    if not health_ok:
        print("\n" + "=" * 70)
        print("❌ Ollama health check failed. Please fix before continuing.")
        print("=" * 70)
        return False

    # Test 2: Agent creation
    agent = await test_agent_creation()
    if not agent:
        print("\n" + "=" * 70)
        print("❌ Agent creation failed. Cannot continue.")
        print("=" * 70)
        return False

    # Test 3: Message processing
    msg_ok = await test_message_processing(agent)

    # Test 4: Task planning
    plan_ok = await test_task_planning(agent)

    # Test 5: Code model (optional)
    await test_code_model()

    # Summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)

    results = {
        "Ollama Health Check": "✅" if health_ok else "❌",
        "Agent Creation": "✅" if agent else "❌",
        "Message Processing": "✅" if msg_ok else "❌",
        "Task Planning": "✅" if plan_ok else "❌",
    }

    for test, status in results.items():
        print(f"  {status} {test}")

    all_passed = all([health_ok, agent is not None, msg_ok, plan_ok])

    if all_passed:
        print("\n🎉 All tests passed! Ollama integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")

    print("=" * 70 + "\n")

    return all_passed


async def main():
    """Main entry point"""
    try:
        success = await run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
