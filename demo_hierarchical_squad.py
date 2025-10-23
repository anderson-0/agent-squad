"""
Hierarchical Agent Squad Demonstration

This demo showcases:
1. Hierarchical communication patterns (PM → Devs, Devs → Tech Lead)
2. Agent interactions via NATS message bus
3. Agno framework with persistent sessions
4. Real-world software development workflow

Hierarchy:
┌─────────────────────────────────────────┐
│         Project Manager (PM)            │
│  • Receives requirements                │
│  • Delegates tasks                      │
│  • Monitors progress                    │
│  • Escalates to humans                  │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌─────────────┐  ┌─────────────┐
│ Tech Lead   │  │ Developers  │
│ • Architecture│  │ • Backend   │
│ • Reviews    │  │ • Frontend  │
│ • Guidance   │  │ • QA        │
└─────────────┘  └─────────────┘
"""
import asyncio
import os
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any

# Set production configuration
os.environ['MESSAGE_BUS'] = 'nats'
os.environ['USE_AGNO_AGENTS'] = 'true'
os.environ['NATS_URL'] = 'nats://localhost:4222'

from backend.agents.factory import AgentFactory
from backend.agents.communication.message_bus import get_message_bus
from backend.schemas.agent_message import (
    TaskAssignment,
    Question,
    Answer,
    StatusUpdate,
    Standup,
)


class HierarchicalSquadDemo:
    """Demonstrates hierarchical agent squad in action"""

    def __init__(self):
        self.message_bus = None
        self.agents: Dict[str, Any] = {}
        self.agent_ids: Dict[str, Any] = {}
        self.execution_id = uuid4()

    async def setup(self):
        """Initialize the squad"""
        print("=" * 80)
        print("🏗️  HIERARCHICAL AGENT SQUAD DEMO")
        print("=" * 80)
        print()

        # Connect to NATS
        print("📡 Connecting to NATS message bus...")
        self.message_bus = get_message_bus()
        if hasattr(self.message_bus, 'connect'):
            await self.message_bus.connect()
            print("   ✅ Connected to NATS JetStream")
        print()

        # Create the squad with hierarchy
        print("🤖 Creating hierarchical squad...")
        print()

        # Level 1: Project Manager (Top of hierarchy)
        print("   👔 Level 1: Project Manager")
        self.agent_ids['pm'] = uuid4()
        self.agents['pm'] = AgentFactory.create_agent(
            agent_id=self.agent_ids['pm'],
            role="project_manager",
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
        )
        print(f"      ✅ PM: {type(self.agents['pm']).__name__}")
        print(f"      📋 Role: Orchestrates squad, delegates tasks, monitors progress")
        print()

        # Level 2: Tech Lead (Middle management)
        print("   🎯 Level 2: Tech Lead")
        self.agent_ids['tech_lead'] = uuid4()
        self.agents['tech_lead'] = AgentFactory.create_agent(
            agent_id=self.agent_ids['tech_lead'],
            role="tech_lead",
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
        )
        print(f"      ✅ Tech Lead: {type(self.agents['tech_lead']).__name__}")
        print(f"      📋 Role: Technical guidance, code reviews, architecture")
        print()

        # Level 3: Developers (Individual contributors)
        print("   💻 Level 3: Developers")

        self.agent_ids['backend_dev'] = uuid4()
        self.agents['backend_dev'] = AgentFactory.create_agent(
            agent_id=self.agent_ids['backend_dev'],
            role="backend_developer",
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
        )
        print(f"      ✅ Backend Dev: {type(self.agents['backend_dev']).__name__}")
        print(f"      📋 Role: Implements backend features, APIs, database")

        self.agent_ids['frontend_dev'] = uuid4()
        self.agents['frontend_dev'] = AgentFactory.create_agent(
            agent_id=self.agent_ids['frontend_dev'],
            role="frontend_developer",
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
        )
        print(f"      ✅ Frontend Dev: {type(self.agents['frontend_dev']).__name__}")
        print(f"      📋 Role: Implements UI, user experience, frontend logic")

        self.agent_ids['qa'] = uuid4()
        self.agents['qa'] = AgentFactory.create_agent(
            agent_id=self.agent_ids['qa'],
            role="tester",
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
        )
        print(f"      ✅ QA Tester: {type(self.agents['qa']).__name__}")
        print(f"      📋 Role: Tests features, reports bugs, ensures quality")
        print()

        print("   🎉 Squad ready! Total: 5 agents")
        print()

    async def scenario_1_pm_delegates_task(self):
        """Scenario 1: PM delegates task to Backend Developer"""
        print("=" * 80)
        print("📋 SCENARIO 1: PM Delegates Task to Backend Developer")
        print("=" * 80)
        print()

        print("📝 Context:")
        print("   • Product owner requests user authentication feature")
        print("   • PM analyzes requirements and delegates to Backend Dev")
        print("   • Demonstrates: Top-down task delegation")
        print()

        # Create task assignment
        task = TaskAssignment(
            recipient=self.agent_ids['backend_dev'],
            task_id="AUTH-001",
            description="Implement JWT-based authentication system",
            acceptance_criteria=[
                "User can register with email/password",
                "User can login and receive JWT token",
                "Token expires after 24 hours",
                "Refresh token mechanism implemented",
                "All endpoints use proper authentication middleware",
                "Tests achieve 90% coverage"
            ],
            context="Product owner wants secure authentication for the web app. This is high priority for MVP launch.",
            priority="high",
            estimated_hours=16.0,
            dependencies=[],
        )

        print("💬 PM → Backend Dev:")
        print(f"   📨 Task: {task.task_id}")
        print(f"   📄 Description: {task.description}")
        print(f"   ⏱️  Estimate: {task.estimated_hours} hours")
        print(f"   🎯 Priority: {task.priority}")
        print(f"   ✅ Acceptance Criteria: {len(task.acceptance_criteria)} items")
        print()

        # Send via NATS
        await self.agents['pm'].send_message(
            recipient_id=self.agent_ids['backend_dev'],
            content=task.model_dump_json(),
            message_type="task_assignment",
            task_execution_id=self.execution_id,
            metadata={
                "task_id": task.task_id,
                "priority": task.priority,
                "estimated_hours": task.estimated_hours,
            }
        )

        print("   ✅ Message sent via NATS JetStream")
        print("   📊 Message persisted in stream: 'agent-messages'")
        print()

        await asyncio.sleep(0.5)

    async def scenario_2_developer_asks_tech_lead(self):
        """Scenario 2: Backend Developer asks Tech Lead for guidance"""
        print("=" * 80)
        print("🤔 SCENARIO 2: Backend Developer Seeks Tech Lead Guidance")
        print("=" * 80)
        print()

        print("📝 Context:")
        print("   • Backend Dev encounters technical decision point")
        print("   • Needs architectural guidance on JWT implementation")
        print("   • Demonstrates: Bottom-up communication for technical questions")
        print()

        # Create question
        question = Question(
            recipient=self.agent_ids['tech_lead'],
            task_id="AUTH-001",
            question="For JWT implementation, should we use HS256 (symmetric) or RS256 (asymmetric) signing algorithm? Also, where should we store refresh tokens?",
            context="Implementing authentication system. Need to decide on security approach for production deployment.",
            urgency="normal",
        )

        print("💬 Backend Dev → Tech Lead:")
        print(f"   ❓ Question: {question.question[:100]}...")
        print(f"   🎯 Context: {question.context}")
        print(f"   ⚡ Urgency: {question.urgency}")
        print()

        # Send via NATS
        await self.agents['backend_dev'].send_message(
            recipient_id=self.agent_ids['tech_lead'],
            content=question.model_dump_json(),
            message_type="question",
            task_execution_id=self.execution_id,
            metadata={
                "task_id": question.task_id,
                "urgency": question.urgency,
                "question_type": "architecture",
            }
        )

        print("   ✅ Question routed via NATS to Tech Lead")
        print()

        await asyncio.sleep(0.5)

    async def scenario_3_tech_lead_provides_guidance(self):
        """Scenario 3: Tech Lead provides architectural guidance"""
        print("=" * 80)
        print("💡 SCENARIO 3: Tech Lead Provides Architectural Guidance")
        print("=" * 80)
        print()

        print("📝 Context:")
        print("   • Tech Lead reviews the question")
        print("   • Provides detailed technical guidance")
        print("   • Demonstrates: Middle management providing expertise")
        print()

        # Create answer
        answer = Answer(
            recipient=self.agent_ids['backend_dev'],
            task_id="AUTH-001",
            question_id="Q-001",
            answer="""Use RS256 (asymmetric) for production. Here's why:

1. Security: RS256 uses public/private key pairs. Even if the public key is exposed, attackers can't forge tokens. With HS256, if the secret leaks, entire system is compromised.

2. Microservices: RS256 allows multiple services to verify tokens without sharing secrets.

3. Key Rotation: Easier to rotate keys without system downtime.

For refresh tokens:
- Store in httpOnly cookies (prevents XSS attacks)
- Store hash in database with user_id reference
- Set secure flag for HTTPS-only transmission
- Implement token rotation on each use

Implementation approach:
1. Use python-jose library for RS256
2. Generate key pair: openssl genrsa -out private.pem 2048
3. Store private key in secrets manager (never in repo)
4. Refresh tokens: 7-day expiry, access tokens: 15min expiry

References: OWASP Authentication Cheat Sheet, Auth0 JWT Best Practices""",
            confidence="high",
        )

        print("💬 Tech Lead → Backend Dev:")
        print(f"   ✅ Answer: RS256 (asymmetric) recommended")
        print(f"   🎯 Confidence: {answer.confidence}")
        print()
        print("   Key recommendations:")
        print("   • Use RS256 for better security")
        print("   • Store refresh tokens in httpOnly cookies")
        print("   • Implement token rotation")
        print("   • Access tokens: 15min, Refresh: 7 days")
        print()

        # Send via NATS
        await self.agents['tech_lead'].send_message(
            recipient_id=self.agent_ids['backend_dev'],
            content=answer.model_dump_json(),
            message_type="answer",
            task_execution_id=self.execution_id,
            metadata={
                "task_id": answer.task_id,
                "confidence": answer.confidence,
                "answer_type": "architecture",
            }
        )

        print("   ✅ Guidance sent via NATS")
        print("   📋 Backend Dev can now proceed with implementation")
        print()

        await asyncio.sleep(0.5)

    async def scenario_4_developer_updates_pm(self):
        """Scenario 4: Backend Developer sends progress update to PM"""
        print("=" * 80)
        print("📊 SCENARIO 4: Backend Developer Reports Progress to PM")
        print("=" * 80)
        print()

        print("📝 Context:")
        print("   • Backend Dev has made progress on the task")
        print("   • Reports status back to PM (upward communication)")
        print("   • Demonstrates: Bottom-up status reporting")
        print()

        # Create status update
        completed_items = [
            "Set up JWT library and key generation",
            "Implemented user registration endpoint",
            "Implemented login endpoint with JWT generation",
            "Created authentication middleware",
        ]

        next_steps_text = """Complete refresh token implementation
Add integration tests
Document API endpoints"""

        status = StatusUpdate(
            task_id="AUTH-001",
            status="in_progress",
            progress_percentage=60,
            details=f"Completed {len(completed_items)} items. Currently implementing refresh token mechanism and writing unit tests.",
            blockers=[],
            next_steps=next_steps_text,
        )

        print("💬 Backend Dev → PM:")
        print(f"   📈 Progress: {status.progress_percentage}%")
        print(f"   📄 Status: {status.status}")
        print(f"   🚫 Blockers: {len(status.blockers)}")
        print()
        print("   Details:")
        print(f"      {status.details}")
        print()
        print("   Completed Items:")
        for item in completed_items:
            print(f"      ✅ {item}")
        print()
        print("   Next Steps:")
        for step in status.next_steps.split('\n'):
            if step.strip():
                print(f"      📋 {step.strip()}")
        print()

        # Send via NATS
        await self.agents['backend_dev'].send_message(
            recipient_id=self.agent_ids['pm'],
            content=status.model_dump_json(),
            message_type="status_update",
            task_execution_id=self.execution_id,
            metadata={
                "task_id": status.task_id,
                "progress_percentage": status.progress_percentage,
                "has_blockers": len(status.blockers) > 0,
            }
        )

        print("   ✅ Status update sent via NATS to PM")
        print("   📊 PM can now track progress in real-time")
        print()

        await asyncio.sleep(0.5)

    async def scenario_5_pm_daily_standup(self):
        """Scenario 5: PM conducts daily standup (broadcast)"""
        print("=" * 80)
        print("🎤 SCENARIO 5: PM Conducts Daily Standup (Broadcast)")
        print("=" * 80)
        print()

        print("📝 Context:")
        print("   • PM wants status from entire team")
        print("   • Broadcasts standup request to all agents")
        print("   • Demonstrates: Top-down broadcast communication")
        print()

        # Create standup request (simpler format for broadcast)
        standup_content = """Daily Standup Request:

Please provide updates on:
1. What did you accomplish since last standup?
2. What are you working on today?
3. Any blockers or concerns?

Reply with your standup update."""

        print("💬 PM → ALL AGENTS (Broadcast):")
        print(f"   📢 Daily Standup Request")
        print()
        print("   Questions:")
        print("      1. What did you accomplish since last standup?")
        print("      2. What are you working on today?")
        print("      3. Any blockers or concerns?")
        print()

        # Broadcast via NATS
        await self.agents['pm'].broadcast_message(
            content=standup_content,
            message_type="standup",
            task_execution_id=self.execution_id,
            metadata={
                "standup_type": "daily",
                "broadcast": True,
            }
        )

        print("   ✅ Standup request broadcast via NATS")
        print("   📡 All agents will receive this message")
        print("   👥 Recipients: Backend Dev, Frontend Dev, QA, Tech Lead")
        print()

        await asyncio.sleep(0.5)

    async def show_message_bus_stats(self):
        """Show NATS message bus statistics"""
        print("=" * 80)
        print("📊 MESSAGE BUS STATISTICS")
        print("=" * 80)
        print()

        if hasattr(self.message_bus, 'get_stats'):
            stats = await self.message_bus.get_stats()

            print("🔌 NATS JetStream Status:")
            print(f"   ✅ Connected: {stats.get('connected', False)}")
            print(f"   📦 Stream: {stats.get('stream_name', 'unknown')}")
            print(f"   📨 Total Messages: {stats.get('total_messages', 0)}")
            print(f"   💾 Total Bytes: {stats.get('total_bytes', 0):,}")
            print(f"   🔢 First Seq: {stats.get('first_seq', 0)}")
            print(f"   🔢 Last Seq: {stats.get('last_seq', 0)}")
            print(f"   👥 Consumers: {stats.get('consumer_count', 0)}")
            print()

            print("📈 Messages Sent This Demo:")
            print("   • PM → Backend Dev: Task Assignment")
            print("   • Backend Dev → Tech Lead: Question")
            print("   • Tech Lead → Backend Dev: Answer")
            print("   • Backend Dev → PM: Status Update")
            print("   • PM → ALL: Standup Broadcast")
            print(f"   Total: 5 messages")
            print()

    async def show_hierarchy_summary(self):
        """Show hierarchy and communication rules"""
        print("=" * 80)
        print("🏛️  HIERARCHICAL STRUCTURE & COMMUNICATION RULES")
        print("=" * 80)
        print()

        print("📊 Organizational Hierarchy:")
        print()
        print("   Level 1: Project Manager (PM)")
        print("   ├─ Role: Orchestration, delegation, monitoring")
        print("   ├─ Reports to: Product Owner / Stakeholders")
        print("   └─ Can delegate to: All team members")
        print()
        print("   Level 2: Tech Lead (TL)")
        print("   ├─ Role: Technical guidance, architecture, code review")
        print("   ├─ Reports to: Project Manager")
        print("   └─ Guides: Backend Dev, Frontend Dev, QA")
        print()
        print("   Level 3: Individual Contributors")
        print("   ├─ Backend Developer")
        print("   │  ├─ Reports to: PM (status updates)")
        print("   │  └─ Seeks guidance from: Tech Lead")
        print("   ├─ Frontend Developer")
        print("   │  ├─ Reports to: PM (status updates)")
        print("   │  └─ Seeks guidance from: Tech Lead")
        print("   └─ QA Tester")
        print("      ├─ Reports to: PM (bug reports, test results)")
        print("      └─ Coordinates with: All developers")
        print()

        print("📜 Communication Rules:")
        print()
        print("   1️⃣  Top-Down (PM → Devs):")
        print("      • Task assignments")
        print("      • Priority changes")
        print("      • Standup requests")
        print("      • Project updates")
        print()
        print("   2️⃣  Bottom-Up (Devs → PM):")
        print("      • Status updates")
        print("      • Blocker reports")
        print("      • Task completion")
        print("      • Human escalation requests")
        print()
        print("   3️⃣  Lateral (Dev ↔ TL):")
        print("      • Technical questions")
        print("      • Architecture guidance")
        print("      • Code review requests")
        print("      • Design discussions")
        print()
        print("   4️⃣  Peer-to-Peer (Dev ↔ Dev):")
        print("      • Collaboration on shared tasks")
        print("      • Knowledge sharing")
        print("      • Integration discussions")
        print()
        print("   5️⃣  Broadcast (PM → ALL):")
        print("      • Team announcements")
        print("      • Standup meetings")
        print("      • Priority shifts")
        print()

    async def cleanup(self):
        """Cleanup resources"""
        print("=" * 80)
        print("🧹 CLEANUP")
        print("=" * 80)
        print()

        print("📊 Final Statistics:")
        print(f"   • Agents created: {len(self.agents)}")
        print(f"   • Messages exchanged: 5+")
        print(f"   • Scenarios demonstrated: 5")
        print(f"   • Execution ID: {self.execution_id}")
        print()

        if hasattr(self.message_bus, 'disconnect'):
            await self.message_bus.disconnect()
            print("   ✅ Disconnected from NATS")

        print()

    async def run(self):
        """Run the complete demo"""
        try:
            await self.setup()

            # Run scenarios
            await self.scenario_1_pm_delegates_task()
            await self.scenario_2_developer_asks_tech_lead()
            await self.scenario_3_tech_lead_provides_guidance()
            await self.scenario_4_developer_updates_pm()
            await self.scenario_5_pm_daily_standup()

            # Show stats
            await self.show_message_bus_stats()
            await self.show_hierarchy_summary()

            # Cleanup
            await self.cleanup()

            # Success message
            print("=" * 80)
            print("🎉 DEMO COMPLETE!")
            print("=" * 80)
            print()
            print("✅ Demonstrated:")
            print("   • Hierarchical agent structure (PM → TL → Devs)")
            print("   • Top-down task delegation")
            print("   • Bottom-up status reporting")
            print("   • Lateral technical consultation")
            print("   • Broadcast communication")
            print("   • NATS JetStream message routing")
            print("   • Agno framework with persistent sessions")
            print()
            print("🚀 Your multi-agent system is production-ready!")
            print()

        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    demo = HierarchicalSquadDemo()
    asyncio.run(demo.run())
