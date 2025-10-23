#!/usr/bin/env python3
"""
Phase 2 Context Enhancement Test

Tests the improved context handling in AgnoSquadAgent:
- Role-specific prompts
- Question type awareness
- Escalation handling
- Better context formatting

Run:
    PYTHONPATH=/Users/anderson/Documents/anderson-0/agent-squad python test_phase2_context.py
"""
from uuid import uuid4

from backend.agents.agno_base import AgentConfig, AgnoSquadAgent


class TestAgent(AgnoSquadAgent):
    """Simple test agent for demonstration"""
    def get_capabilities(self):
        return ["test_capability"]


def print_header(title: str, emoji: str = "🔍"):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f"  {emoji} {title}")
    print("=" * 80 + "\n")


def test_contextual_prompts():
    """
    Test the _build_contextual_prompt() method.

    This verifies that:
    1. Role information is added to prompts
    2. Question type guidance is included
    3. Escalation context is handled
    4. Context is formatted naturally
    """
    print("\n" + "🧠" * 40)
    print("  PHASE 2: CONTEXT ENHANCEMENT TEST".center(80))
    print("  Testing Intelligent Context Handling".center(80))
    print("🧠" * 40)

    # Create test agent
    config = AgentConfig(
        role="tech_lead",
        specialization="backend",
        llm_provider="openai",
        llm_model="gpt-4",
        system_prompt="You are a helpful technical lead."
    )

    agent = TestAgent(config=config, agent_id=uuid4())

    # ================================================================
    # Test 1: Basic Prompt (No Context)
    # ================================================================
    print_header("Test 1: Basic Prompt (No Context)", "📝")

    basic_prompt = agent._build_contextual_prompt(None)
    print("Basic prompt:")
    print("─" * 80)
    print(basic_prompt)
    print("─" * 80)

    assert basic_prompt == config.system_prompt
    print("✅ Basic prompt unchanged when no context provided")

    # ================================================================
    # Test 2: Role-Specific Context
    # ================================================================
    print_header("Test 2: Role-Specific Context", "👤")

    role_context = {
        "agent_role": "tech_lead",
        "agent_specialization": "backend"
    }

    role_prompt = agent._build_contextual_prompt(role_context)
    print("Prompt with role context:")
    print("─" * 80)
    print(role_prompt)
    print("─" * 80)

    assert "Your Role" in role_prompt
    assert "Tech Lead" in role_prompt
    assert "backend" in role_prompt
    print("✅ Role information correctly added to prompt")

    # ================================================================
    # Test 3: Question Type Awareness
    # ================================================================
    print_header("Test 3: Question Type Awareness", "❓")

    # Test implementation question
    impl_context = {
        "agent_role": "backend_developer",
        "question_type": "implementation"
    }

    impl_prompt = agent._build_contextual_prompt(impl_context)
    print("Implementation question context:")
    print("─" * 80)
    print(impl_prompt)
    print("─" * 80)

    assert "Question Type: Implementation" in impl_prompt
    assert "practical implementation details" in impl_prompt
    print("✅ Implementation guidance correctly added")

    # Test architecture question
    arch_context = {
        "agent_role": "solution_architect",
        "question_type": "architecture"
    }

    arch_prompt = agent._build_contextual_prompt(arch_context)
    print("\nArchitecture question context:")
    print("─" * 80)
    print(arch_prompt)
    print("─" * 80)

    assert "Question Type: Architecture" in arch_prompt
    assert "system design" in arch_prompt or "scalability" in arch_prompt
    print("✅ Architecture guidance correctly added")

    # ================================================================
    # Test 4: Escalation Context
    # ================================================================
    print_header("Test 4: Escalation Context", "🚨")

    escalated_context = {
        "agent_role": "tech_lead",
        "question_type": "implementation",
        "escalation_level": 2
    }

    escalated_prompt = agent._build_contextual_prompt(escalated_context)
    print("Escalated question context:")
    print("─" * 80)
    print(escalated_prompt)
    print("─" * 80)

    assert "Escalated Question" in escalated_prompt
    assert "Level 2" in escalated_prompt
    assert "expert-level guidance" in escalated_prompt
    print("✅ Escalation warning correctly added")

    # ================================================================
    # Test 5: Conversation State
    # ================================================================
    print_header("Test 5: Conversation State", "💬")

    conversation_context = {
        "agent_role": "tech_lead",
        "question_type": "implementation",
        "conversation_state": "waiting",
        "conversation_events": [
            {"event_type": "initiated", "content": "Previous question"},
            {"event_type": "acknowledged", "content": "Acknowledged"}
        ]
    }

    conv_prompt = agent._build_contextual_prompt(conversation_context)
    print("Conversation context:")
    print("─" * 80)
    print(conv_prompt)
    print("─" * 80)

    assert "Conversation State: waiting" in conv_prompt
    assert "Conversation History" in conv_prompt
    assert "2 previous event(s)" in conv_prompt
    print("✅ Conversation context correctly added")

    # ================================================================
    # Test 6: Full Context (All Fields)
    # ================================================================
    print_header("Test 6: Full Context (All Fields)", "🎯")

    full_context = {
        "agent_role": "tech_lead",
        "agent_specialization": "backend",
        "question_type": "implementation",
        "escalation_level": 1,
        "conversation_state": "waiting",
        "conversation_events": [
            {"event_type": "initiated"}
        ],
        "conversation_metadata": {
            "task_id": "TASK-123",
            "priority": "high"
        }
    }

    full_prompt = agent._build_contextual_prompt(full_context)
    print("Full context prompt:")
    print("─" * 80)
    print(full_prompt)
    print("─" * 80)

    # Verify all sections are present
    assert "Your Role" in full_prompt
    assert "Tech Lead" in full_prompt
    assert "Question Type" in full_prompt
    assert "Escalated Question" in full_prompt
    assert "Conversation State" in full_prompt
    assert "Conversation History" in full_prompt
    assert "Additional Context" in full_prompt
    print("✅ All context sections correctly added")

    # ================================================================
    # Test 7: Verify _build_messages() Integration
    # ================================================================
    print_header("Test 7: Integration with _build_messages()", "🔗")

    test_message = "How should I implement caching?"
    messages = agent._build_messages(
        message=test_message,
        context=full_context,
        history=[]
    )

    print(f"Generated {len(messages)} messages:")
    for i, msg in enumerate(messages):
        print(f"  {i+1}. Role: {msg['role']}, Content length: {len(msg['content'])} chars")

    # Verify structure
    assert len(messages) == 2  # system + user
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == test_message

    # Verify system message has enhanced context
    system_content = messages[0]["content"]
    assert "Your Role" in system_content
    assert "Question Type" in system_content
    print("✅ Context correctly integrated into messages")

    # ================================================================
    # Summary
    # ================================================================
    print_header("Test Summary", "🎉")

    print("✅ All tests passed!")
    print("✅ Role-specific prompts working")
    print("✅ Question type awareness working")
    print("✅ Escalation handling working")
    print("✅ Conversation context working")
    print("✅ Integration with _build_messages() working")
    print()
    print("Phase 2 enhancements verified!")

    print("\n" + "=" * 80)
    print("  PHASE 2 CONTEXT ENHANCEMENT TEST COMPLETE".center(80))
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        test_contextual_prompts()
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
