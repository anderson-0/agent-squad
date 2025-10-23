"""
Agno Message Bus Integration Demo

This demo showcases the complete message bus integration with Agno agents:
1. Agno agents communicating via message bus
2. Task assignments, questions, answers
3. Real-time message subscriptions
4. Session persistence across agent instances
5. SSE-ready message broadcasting
"""
import asyncio
from uuid import uuid4, UUID
from datetime import datetime
import json

from backend.agents.factory import AgentFactory
from backend.core.agno_config import initialize_agno, shutdown_agno
from backend.agents.communication.message_bus import get_message_bus, reset_message_bus
from backend.schemas.agent_message import (
    TaskAssignment,
    Question,
    Answer,
    StatusUpdate,
)


async def demo():
    """Run message bus integration demo"""

    print("\n" + "="*80)
    print("🚀 AGNO MESSAGE BUS INTEGRATION DEMO")
    print("Real Inter-Agent Communication via Message Bus")
    print("="*80)

    # Initialize Agno framework
    initialize_agno()

    # Reset message bus for clean demo
    await reset_message_bus()

    try:
        # =====================================================================
        # SCENE 1: Create Squad Members with Agent IDs
        # =====================================================================
        print("\n" + "="*80)
        print("SCENE 1: Creating Squad with Message Bus Integration")
        print("="*80)

        # Create agent IDs (these would normally come from database)
        pm_id = uuid4()
        backend_dev_id = uuid4()
        tech_lead_id = uuid4()

        print(f"\n📋 Agent IDs:")
        print(f"   • Project Manager:   {str(pm_id)[:8]}...")
        print(f"   • Backend Developer: {str(backend_dev_id)[:8]}...")
        print(f"   • Tech Lead:         {str(tech_lead_id)[:8]}...")

        # Create Agno agents with agent_id for message bus
        print(f"\n🔧 Creating Agno agents with message bus integration...")

        pm = AgentFactory.create_agent(
            agent_id=pm_id,
            role="project_manager",
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            force_agno=True,
        )

        backend_dev = AgentFactory.create_agent(
            agent_id=backend_dev_id,
            role="backend_developer",
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            force_agno=True,
        )

        tech_lead = AgentFactory.create_agent(
            agent_id=tech_lead_id,
            role="tech_lead",
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            force_agno=True,
        )

        print(f"   ✅ All agents created with message bus integration")
        print(f"   ✅ Each agent can send/receive messages")

        # Verify agents have IDs
        assert pm.agent_id == pm_id
        assert backend_dev.agent_id == backend_dev_id
        assert tech_lead.agent_id == tech_lead_id

        # =====================================================================
        # SCENE 2: PM → Backend Dev (Task Assignment via Message Bus)
        # =====================================================================
        print("\n" + "="*80)
        print("SCENE 2: PM Assigns Task to Backend Dev via Message Bus")
        print("="*80)

        task_assignment = TaskAssignment(
            recipient=backend_dev_id,
            task_id="TASK-101",
            description="Implement user authentication API with JWT tokens",
            acceptance_criteria=[
                "POST /api/auth/login endpoint created",
                "JWT token generation working",
                "Token validation middleware implemented",
                "Unit tests passing"
            ],
            context="User story requires secure login system",
            priority="high",
            estimated_hours=8.0,
        )

        print(f"\n📤 PM sending TaskAssignment to Backend Dev...")
        print(f"   Task: {task_assignment.description[:60]}...")
        print(f"   Priority: {task_assignment.priority}")
        print(f"   Estimated hours: {task_assignment.estimated_hours}")

        # PM sends message via message bus
        execution_id = uuid4()
        message = await pm.send_message(
            recipient_id=backend_dev_id,
            content=task_assignment.model_dump_json(),
            message_type="task_assignment",
            task_execution_id=execution_id,
            metadata={
                "task_id": task_assignment.task_id,
                "priority": task_assignment.priority,
            }
        )

        print(f"   ✅ Message sent via message bus")
        print(f"   📨 Message ID: {str(message.id)[:8]}...")
        print(f"   🔖 Execution ID: {str(execution_id)[:8]}...")

        # Backend Dev receives message
        print(f"\n📥 Backend Dev checking messages...")
        messages = await backend_dev.receive_messages(limit=10)
        print(f"   ✅ Received {len(messages)} message(s)")

        if messages:
            latest_msg = messages[-1]
            print(f"   📨 Latest message type: {latest_msg.message_type}")
            print(f"   📨 From: {str(latest_msg.sender_id)[:8]}...")
            print(f"   📨 Content preview: {latest_msg.content[:80]}...")

        # =====================================================================
        # SCENE 3: Backend Dev → Tech Lead (Question via Message Bus)
        # =====================================================================
        print("\n" + "="*80)
        print("SCENE 3: Backend Dev Asks Tech Lead a Question")
        print("="*80)

        question = Question(
            recipient=tech_lead_id,
            task_id="TASK-101",
            question="Should we use RS256 or HS256 for JWT signing? What are the security implications?",
            context="Implementing JWT authentication, need to choose signing algorithm",
            urgency="normal",
        )

        print(f"\n📤 Backend Dev sending Question to Tech Lead...")
        print(f"   Question: {question.question[:70]}...")
        print(f"   Urgency: {question.urgency}")

        question_msg = await backend_dev.send_message(
            recipient_id=tech_lead_id,
            content=question.model_dump_json(),
            message_type="question",
            task_execution_id=execution_id,
            metadata={
                "task_id": question.task_id,
                "question_id": "Q1",
            }
        )

        print(f"   ✅ Question sent via message bus")
        print(f"   📨 Message ID: {str(question_msg.id)[:8]}...")

        # Tech Lead receives question
        print(f"\n📥 Tech Lead checking messages...")
        tl_messages = await tech_lead.receive_messages(message_type="question", limit=10)
        print(f"   ✅ Received {len(tl_messages)} question(s)")

        # =====================================================================
        # SCENE 4: Tech Lead → Backend Dev (Answer via Message Bus)
        # =====================================================================
        print("\n" + "="*80)
        print("SCENE 4: Tech Lead Answers Backend Dev's Question")
        print("="*80)

        answer = Answer(
            recipient=backend_dev_id,
            task_id="TASK-101",
            question_id="Q1",
            answer=(
                "Use RS256 (RSA with SHA-256) for production. Key advantages:\n"
                "1. Asymmetric encryption - public key for verification, private for signing\n"
                "2. Better key rotation - can distribute public keys without exposing private\n"
                "3. More secure for distributed systems\n\n"
                "HS256 is simpler but requires shared secret, which is harder to secure."
            ),
            confidence="high",
        )

        print(f"\n📤 Tech Lead sending Answer to Backend Dev...")
        print(f"   Answer preview: {answer.answer[:100]}...")
        print(f"   Confidence: {answer.confidence}")

        answer_msg = await tech_lead.send_message(
            recipient_id=backend_dev_id,
            content=answer.model_dump_json(),
            message_type="answer",
            task_execution_id=execution_id,
            metadata={
                "task_id": answer.task_id,
                "question_id": answer.question_id,
            }
        )

        print(f"   ✅ Answer sent via message bus")
        print(f"   📨 Message ID: {str(answer_msg.id)[:8]}...")

        # Backend Dev receives answer
        print(f"\n📥 Backend Dev checking for answers...")
        dev_messages = await backend_dev.receive_messages(message_type="answer", limit=10)
        print(f"   ✅ Received {len(dev_messages)} answer(s)")

        # =====================================================================
        # SCENE 5: Backend Dev → PM (Status Update via Message Bus)
        # =====================================================================
        print("\n" + "="*80)
        print("SCENE 5: Backend Dev Provides Status Update to PM")
        print("="*80)

        status = StatusUpdate(
            task_id="TASK-101",
            status="in_progress",
            progress_percentage=40,
            details=(
                "Good progress on authentication implementation:\n"
                "- Decided on RS256 signing after consulting Tech Lead\n"
                "- Implemented POST /api/auth/login endpoint\n"
                "- JWT token generation working\n"
                "- Currently working on validation middleware"
            ),
            blockers=[],
            next_steps="Complete validation middleware and write unit tests",
        )

        print(f"\n📤 Backend Dev sending StatusUpdate to PM...")
        print(f"   Status: {status.status}")
        print(f"   Progress: {status.progress_percentage}%")
        print(f"   Details: {status.details[:80]}...")

        status_msg = await backend_dev.send_message(
            recipient_id=pm_id,
            content=status.model_dump_json(),
            message_type="status_update",
            task_execution_id=execution_id,
            metadata={
                "task_id": status.task_id,
                "progress_percentage": status.progress_percentage,
            }
        )

        print(f"   ✅ Status update sent via message bus")
        print(f"   📨 Message ID: {str(status_msg.id)[:8]}...")

        # PM receives status update
        print(f"\n📥 PM checking status updates...")
        pm_messages = await pm.receive_messages(message_type="status_update", limit=10)
        print(f"   ✅ Received {len(pm_messages)} status update(s)")

        # =====================================================================
        # SCENE 6: PM Broadcasts Standup Request to All Agents
        # =====================================================================
        print("\n" + "="*80)
        print("SCENE 6: PM Broadcasts Standup Request to All Agents")
        print("="*80)

        print(f"\n📤 PM broadcasting standup request to all agents...")

        broadcast_msg = await pm.broadcast_message(
            content="Daily standup time! Please provide your updates.",
            message_type="standup",
            task_execution_id=execution_id,
        )

        print(f"   ✅ Broadcast message sent")
        print(f"   📨 Message ID: {str(broadcast_msg.id)[:8]}...")

        # All agents receive broadcast
        print(f"\n📥 Checking which agents received broadcast...")

        await asyncio.sleep(0.1)  # Brief delay for message propagation

        bd_broadcast = await backend_dev.receive_messages(message_type="standup", limit=1)
        tl_broadcast = await tech_lead.receive_messages(message_type="standup", limit=1)

        print(f"   • Backend Dev received broadcast: {'✅' if bd_broadcast else '❌'}")
        print(f"   • Tech Lead received broadcast: {'✅' if tl_broadcast else '❌'}")

        # =====================================================================
        # SCENE 7: Get Full Conversation for Task Execution
        # =====================================================================
        print("\n" + "="*80)
        print("SCENE 7: Retrieve Full Conversation Thread")
        print("="*80)

        message_bus = get_message_bus()

        print(f"\n📖 Retrieving full conversation for execution {str(execution_id)[:8]}...")
        conversation = await message_bus.get_conversation(
            task_execution_id=execution_id,
            limit=100
        )

        print(f"   ✅ Found {len(conversation)} messages in conversation")
        print(f"\n   📝 Conversation timeline:")

        for i, msg in enumerate(conversation, 1):
            sender_str = str(msg.sender_id)[:8]
            recipient_str = str(msg.recipient_id)[:8] if msg.recipient_id else "ALL"
            print(f"      {i}. [{msg.message_type}] {sender_str}... → {recipient_str}...")

        # =====================================================================
        # SCENE 8: Message Bus Statistics
        # =====================================================================
        print("\n" + "="*80)
        print("SCENE 8: Message Bus Statistics")
        print("="*80)

        stats = message_bus.get_stats()

        print(f"\n📊 Message Bus Stats:")
        print(f"   • Total messages: {stats['total_messages']}")
        print(f"   • Agents with messages: {stats['agents_with_messages']}")
        print(f"   • Total subscribers: {stats['total_subscribers']}")
        print(f"   • Broadcast messages: {stats['broadcast_messages']}")

        # =====================================================================
        # FINALE: Summary
        # =====================================================================
        print("\n" + "="*80)
        print("🎉 MESSAGE BUS INTEGRATION DEMO COMPLETE!")
        print("="*80)

        print(f"\n✨ What we demonstrated:")
        print(f"   ✅ Agno agents with message bus integration")
        print(f"   ✅ PM → Backend Dev: Task assignment")
        print(f"   ✅ Backend Dev → Tech Lead: Question")
        print(f"   ✅ Tech Lead → Backend Dev: Answer")
        print(f"   ✅ Backend Dev → PM: Status update")
        print(f"   ✅ PM → All: Broadcast standup request")
        print(f"   ✅ Full conversation thread retrieval")
        print(f"   ✅ Message bus statistics")

        print(f"\n🎯 Key Features:")
        print(f"   • Point-to-point messaging (agent → agent)")
        print(f"   • Broadcast messaging (agent → all)")
        print(f"   • Message type filtering (questions, answers, etc.)")
        print(f"   • Task execution context tracking")
        print(f"   • Session persistence (each agent maintains history)")
        print(f"   • SSE-ready (messages broadcast to frontend)")

        print(f"\n💡 Production Ready:")
        print(f"   • All messages persisted in memory (upgrade to Redis)")
        print(f"   • All messages can be persisted to database")
        print(f"   • SSE integration for real-time frontend updates")
        print(f"   • Full conversation history for each execution")
        print(f"   • Message metadata includes framework, session, role")

        print(f"\n🚀 Total messages sent: {stats['total_messages']}")
        print(f"📨 All messages tracked and auditable!")

        # Clean up
        AgentFactory.clear_all_agents()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        shutdown_agno()


if __name__ == "__main__":
    asyncio.run(demo())
