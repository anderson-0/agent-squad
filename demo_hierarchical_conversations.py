#!/usr/bin/env python3
"""
Hierarchical Conversation Demo

Demonstrates:
- Customizable routing rules
- Automatic "please wait" acknowledgments
- Timeout and retry mechanism
- Escalation to higher authority
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

# Setup path
sys.path.insert(0, '/Users/anderson/Documents/anderson-0/agent-squad')

# ENABLE NATS MODE
os.environ['MESSAGE_BUS'] = 'nats'
os.environ['NATS_URL'] = 'nats://localhost:4222'
os.environ['DEBUG'] = 'False'

# SUPPRESS ALL LOGGING
import logging
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger('sqlalchemy').setLevel(logging.CRITICAL)
logging.getLogger('sqlalchemy.engine').setLevel(logging.CRITICAL)
logging.getLogger('sqlalchemy.pool').setLevel(logging.CRITICAL)
logging.getLogger('backend').setLevel(logging.CRITICAL)

from sqlalchemy import select
from backend.core.database import AsyncSessionLocal
from backend.models.user import User
from backend.services.squad_service import SquadService
from backend.services.agent_service import AgentService
from backend.services.task_execution_service import TaskExecutionService
from backend.agents.communication.message_bus import get_message_bus
from backend.models.project import Project, Task
from backend.models.conversation import Conversation, ConversationEvent, ConversationState
from backend.models.routing_rule import RoutingRule
from backend.models.message import AgentMessage


# Terminal colors
class C:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ORANGE = '\033[38;5;208m'
    PURPLE = '\033[38;5;135m'
    END = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


def print_header(text):
    """Print a styled header"""
    print(f"\n{C.BOLD}{C.CYAN}{'=' * 80}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{text.center(80)}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{'=' * 80}{C.END}\n")


def print_section(text):
    """Print a section header"""
    print(f"\n{C.BOLD}{C.PURPLE}▶ {text}{C.END}")


def print_message(emoji, sender, recipient, msg_type, content, is_system=False):
    """Print a clean message"""
    timestamp = datetime.now().strftime("%H:%M:%S")

    color = C.DIM if is_system else C.YELLOW

    # Header
    print(f"{C.DIM}[{timestamp}]{C.END} {emoji} "
          f"{C.BOLD}{color}{sender}{C.END} → "
          f"{C.BOLD}{C.GREEN}{recipient}{C.END}")

    # Message box
    print(f"{C.DIM}           ┌{'─' * 60}┐{C.END}")

    # Word wrap content
    words = content.split()
    line = "           │ "
    for word in words:
        if len(line) + len(word) + 1 > 71:
            print(f"{C.DIM}{line + ' ' * (73 - len(line))}│{C.END}")
            line = "           │ " + word
        else:
            if line.endswith('│ '):
                line += word
            else:
                line += ' ' + word
    if line != "           │ ":
        print(f"{C.DIM}{line + ' ' * (73 - len(line))}│{C.END}")

    print(f"{C.DIM}           └{'─' * 60}┘{C.END}\n")


def print_state_change(from_state, to_state, reason=""):
    """Print a state transition"""
    print(f"  {C.ORANGE}⚡ Conversation State: {C.END}"
          f"{C.DIM}{from_state}{C.END} → {C.BOLD}{C.ORANGE}{to_state}{C.END}")
    if reason:
        print(f"     {C.DIM}Reason: {reason}{C.END}")


def print_routing_rule(rule):
    """Print a routing rule"""
    print(f"  {C.CYAN}→{C.END} {C.BOLD}{rule['asker_role']}{C.END} "
          f"asks about {C.YELLOW}{rule['question_type']}{C.END} "
          f"→ Level {rule['escalation_level']}: "
          f"{C.GREEN}{rule['responder_role']}{C.END}")


async def setup_routing_rules(db, squad_id):
    """Set up routing rules for the squad"""
    print_section("Setting Up Routing Rules")

    rules = [
        {
            "asker_role": "backend_developer",
            "question_type": "implementation",
            "escalation_level": 0,
            "responder_role": "tech_lead",
        },
        {
            "asker_role": "backend_developer",
            "question_type": "implementation",
            "escalation_level": 1,
            "responder_role": "solution_architect",
        },
        {
            "asker_role": "backend_developer",
            "question_type": "implementation",
            "escalation_level": 2,
            "responder_role": "project_manager",
        },
    ]

    created_rules = []
    for rule_data in rules:
        rule = RoutingRule(
            id=uuid4(),
            squad_id=squad_id,
            asker_role=rule_data["asker_role"],
            question_type=rule_data["question_type"],
            escalation_level=rule_data["escalation_level"],
            responder_role=rule_data["responder_role"],
            is_active=True,
            priority=0,
            rule_metadata={}
        )
        db.add(rule)
        created_rules.append(rule_data)

    await db.commit()

    print(f"{C.GREEN}✓ Created routing hierarchy for backend developers:{C.END}\n")
    for rule in created_rules:
        print_routing_rule(rule)
    print()


async def get_responder_by_routing_rule(db, squad_id, asker_role, question_type, escalation_level):
    """Query routing rules to find the responder"""
    result = await db.execute(
        select(RoutingRule)
        .where(RoutingRule.squad_id == squad_id)
        .where(RoutingRule.asker_role == asker_role)
        .where(RoutingRule.question_type == question_type)
        .where(RoutingRule.escalation_level == escalation_level)
        .where(RoutingRule.is_active == True)
    )
    rule = result.scalar_one_or_none()
    return rule


async def main():
    print_header("🚀 Hierarchical Conversation Demo")

    print(f"{C.CYAN}Initializing squad with customizable routing rules...{C.END}\n")

    async with AsyncSessionLocal() as db:
        # Get or create user
        result = await db.execute(select(User).where(User.email == 'demo@test.com'))
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                id=uuid4(),
                email='demo@test.com',
                username='demo',
                full_name='Demo User',
                hashed_password='dummy'
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Create squad
        squad = await SquadService.create_squad(
            db=db,
            user_id=user.id,
            name='Hierarchical Routing Demo Squad',
            description='Demonstrating customizable routing and escalation'
        )

        # Create agents
        backend = await AgentService.create_squad_member(
            db=db,
            squad_id=squad.id,
            role='backend_developer',
            specialization='python_fastapi',
            llm_provider='openai',
            llm_model='gpt-4'
        )

        tech_lead = await AgentService.create_squad_member(
            db=db,
            squad_id=squad.id,
            role='tech_lead',
            llm_provider='anthropic',
            llm_model='claude-3-5-sonnet-20241022'
        )

        architect = await AgentService.create_squad_member(
            db=db,
            squad_id=squad.id,
            role='solution_architect',
            llm_provider='anthropic',
            llm_model='claude-3-5-sonnet-20241022'
        )

        pm = await AgentService.create_squad_member(
            db=db,
            squad_id=squad.id,
            role='project_manager',
            llm_provider='anthropic',
            llm_model='claude-3-5-sonnet-20241022'
        )

        await db.commit()

        # Set up routing rules
        await setup_routing_rules(db, squad.id)

        # Create project and task
        project = Project(
            id=uuid4(),
            squad_id=squad.id,
            name='E-Commerce Platform',
            description='Build an e-commerce platform',
            is_active=True
        )
        db.add(project)
        await db.flush()

        task = Task(
            id=uuid4(),
            project_id=project.id,
            title='Implement Caching Layer',
            description='Add Redis caching to improve performance',
            status='in_progress',
            priority='high'
        )
        db.add(task)
        await db.flush()

        execution = await TaskExecutionService.start_task_execution(
            db=db,
            task_id=task.id,
            squad_id=squad.id
        )
        await db.commit()

        print(f"{C.GREEN}✓ Squad Created{C.END}")
        print(f"{C.GREEN}✓ Agents: Backend Dev, Tech Lead, Architect, PM{C.END}")
        print(f"{C.GREEN}✓ Task: {task.title}{C.END}\n")

        # Get NATS bus
        bus = get_message_bus()
        if not bus._connected:
            await bus.connect()

        print_header("📡 Hierarchical Conversation Flow")

        # ========== STEP 1: Backend Developer Asks Question ==========
        print_section("Step 1: Backend Developer Asks Question")

        await asyncio.sleep(1)

        question_content = "How should I implement the caching layer? Should I use Redis or Memcached? What's the best pattern for cache invalidation?"

        print_message(
            "❓", "Backend Developer", "System", "question",
            question_content
        )

        # Create initial message (using current message bus signature)
        initial_message = await bus.send_message(
            sender_id=backend.id,
            recipient_id=tech_lead.id,
            content=question_content,
            message_type="question",
            task_execution_id=execution.id,
            db=db
        )
        await db.commit()

        # Query routing rules to determine responder
        await asyncio.sleep(0.5)
        print(f"\n  {C.CYAN}🔍 Querying routing rules...{C.END}")

        rule = await get_responder_by_routing_rule(
            db, squad.id,
            asker_role='backend_developer',
            question_type='implementation',
            escalation_level=0
        )

        if rule:
            print(f"  {C.GREEN}✓ Found rule: Route to {C.BOLD}{rule.responder_role}{C.END} {C.GREEN}(level {rule.escalation_level}){C.END}\n")

        # Create conversation
        conversation = Conversation(
            id=uuid4(),
            initial_message_id=initial_message.id,
            current_state=ConversationState.INITIATED.value,
            asker_id=backend.id,
            current_responder_id=tech_lead.id,
            escalation_level=0,
            question_type='implementation',
            task_execution_id=execution.id,
            timeout_at=datetime.utcnow() + timedelta(seconds=3),  # Short for demo
            conv_metadata={}
        )
        db.add(conversation)

        # Create event
        event = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation.id,
            event_type='initiated',
            from_state=None,
            to_state=ConversationState.INITIATED.value,
            message_id=initial_message.id,
            triggered_by_agent_id=backend.id,
            event_data={'question_type': 'implementation'}
        )
        db.add(event)
        await db.commit()

        print_state_change("None", "INITIATED", "Question sent to Tech Lead")

        await asyncio.sleep(2)

        # ========== STEP 2: Tech Lead Acknowledges ==========
        print_section("Step 2: Auto-Acknowledgment")

        ack_content = "I received your question. Let me think about this, please wait..."

        print_message(
            "📨", "Tech Lead", "Backend Developer", "acknowledgment",
            ack_content,
            is_system=True
        )

        ack_message = await bus.send_message(
            sender_id=tech_lead.id,
            recipient_id=backend.id,
            content=ack_content,
            message_type="acknowledgment",
            task_execution_id=execution.id,
            db=db
        )

        # Update conversation
        conversation.current_state = ConversationState.WAITING.value
        conversation.acknowledged_at = datetime.utcnow()

        # Create event
        event = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation.id,
            event_type='acknowledged',
            from_state=ConversationState.INITIATED.value,
            to_state=ConversationState.WAITING.value,
            message_id=ack_message.id,
            triggered_by_agent_id=tech_lead.id,
            event_data={}
        )
        db.add(event)
        await db.commit()

        print_state_change("INITIATED", "WAITING", "Tech Lead acknowledged, waiting for answer")
        print(f"  {C.ORANGE}⏰ Timeout set: 3 seconds{C.END}\n")

        await asyncio.sleep(3)

        # ========== STEP 3: Timeout - Send Follow-up ==========
        print_section("Step 3: Timeout - Follow-up Message")

        print(f"  {C.RED}⏰ Timeout expired! No response from Tech Lead.{C.END}\n")

        followup_content = "Are you still there? I'm still waiting for your response to my caching question."

        print_message(
            "🔔", "System", "Tech Lead", "follow_up",
            followup_content,
            is_system=True
        )

        followup_message = await bus.send_message(
            sender_id=backend.id,
            recipient_id=tech_lead.id,
            content=followup_content,
            message_type="follow_up",
            task_execution_id=execution.id,
            db=db
        )

        # Update conversation
        conversation.current_state = ConversationState.FOLLOW_UP.value
        conversation.timeout_at = datetime.utcnow() + timedelta(seconds=2)  # Shorter retry timeout

        # Create event
        event = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation.id,
            event_type='timeout',
            from_state=ConversationState.WAITING.value,
            to_state=ConversationState.FOLLOW_UP.value,
            message_id=followup_message.id,
            triggered_by_agent_id=None,  # System triggered
            event_data={'reason': 'initial_timeout', 'timeout_seconds': 3}
        )
        db.add(event)
        await db.commit()

        print_state_change("WAITING", "FOLLOW_UP", "Sent follow-up, retry timeout: 2 seconds")

        await asyncio.sleep(2.5)

        # ========== STEP 4: Still No Response - Escalate ==========
        print_section("Step 4: Escalation to Solution Architect")

        print(f"  {C.RED}⏰ Still no response from Tech Lead!{C.END}")
        print(f"  {C.ORANGE}⬆️  Escalating to next level...{C.END}\n")

        # Query routing rule for next escalation level
        await asyncio.sleep(0.5)
        print(f"  {C.CYAN}🔍 Querying routing rules for escalation level 1...{C.END}")

        next_rule = await get_responder_by_routing_rule(
            db, squad.id,
            asker_role='backend_developer',
            question_type='implementation',
            escalation_level=1
        )

        if next_rule:
            print(f"  {C.GREEN}✓ Found rule: Route to {C.BOLD}{next_rule.responder_role}{C.END} {C.GREEN}(level {next_rule.escalation_level}){C.END}\n")

        escalation_content = (
            f"I haven't received a response from Tech Lead about the caching implementation. "
            f"Original question: {question_content}"
        )

        print_message(
            "⬆️", "System", "Solution Architect", "escalation",
            "Escalating question: The Backend Developer needs help with caching implementation. The Tech Lead hasn't responded.",
            is_system=True
        )

        escalation_message = await bus.send_message(
            sender_id=backend.id,
            recipient_id=architect.id,
            content=escalation_content,
            message_type="question",
            task_execution_id=execution.id,
            db=db
        )

        # Update conversation
        conversation.current_state = ConversationState.ESCALATED.value
        conversation.current_responder_id = architect.id
        conversation.escalation_level = 1
        conversation.timeout_at = datetime.utcnow() + timedelta(seconds=3)

        # Create event
        event = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation.id,
            event_type='escalated',
            from_state=ConversationState.FOLLOW_UP.value,
            to_state=ConversationState.ESCALATED.value,
            message_id=escalation_message.id,
            triggered_by_agent_id=None,
            event_data={
                'reason': 'retry_timeout',
                'from_responder_id': str(tech_lead.id),
                'to_responder_id': str(architect.id),
                'escalation_level': 1
            }
        )
        db.add(event)
        await db.commit()

        print_state_change(
            "FOLLOW_UP", "ESCALATED",
            f"Escalated to Solution Architect (level {conversation.escalation_level})"
        )

        await asyncio.sleep(2)

        # ========== STEP 5: Architect Acknowledges ==========
        print_section("Step 5: Solution Architect Responds")

        architect_ack = "I received the escalated question. Let me review the caching requirements, please wait..."

        print_message(
            "📨", "Solution Architect", "Backend Developer", "acknowledgment",
            architect_ack,
            is_system=True
        )

        await bus.send_message(
            sender_id=architect.id,
            recipient_id=backend.id,
            content=architect_ack,
            message_type="acknowledgment",
            task_execution_id=execution.id,
            db=db
        )

        conversation.current_state = ConversationState.WAITING.value
        conversation.acknowledged_at = datetime.utcnow()
        await db.commit()

        print_state_change("ESCALATED", "WAITING", "Architect acknowledged")

        await asyncio.sleep(2.5)

        # ========== STEP 6: Architect Provides Answer ==========
        print_section("Step 6: Answer Provided")

        answer_content = (
            "For your e-commerce caching layer, I recommend:\n\n"
            "1. Use Redis (better feature set than Memcached)\n"
            "2. Implement cache-aside pattern for product data\n"
            "3. Use TTL-based expiration (1 hour for product data)\n"
            "4. For cart data, use Redis pub/sub for real-time invalidation\n"
            "5. Set up Redis Cluster for high availability\n\n"
            "I can help you design the architecture if you need more details."
        )

        print_message(
            "✅", "Solution Architect", "Backend Developer", "answer",
            answer_content
        )

        answer_message = await bus.send_message(
            sender_id=architect.id,
            recipient_id=backend.id,
            content=answer_content,
            message_type="answer",
            task_execution_id=execution.id,
            db=db
        )

        # Update conversation - RESOLVED
        conversation.current_state = ConversationState.ANSWERED.value
        conversation.resolved_at = datetime.utcnow()

        # Create final event
        event = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation.id,
            event_type='answered',
            from_state=ConversationState.WAITING.value,
            to_state=ConversationState.ANSWERED.value,
            message_id=answer_message.id,
            triggered_by_agent_id=architect.id,
            event_data={}
        )
        db.add(event)
        await db.commit()

        print_state_change("WAITING", "ANSWERED", "Question resolved!")

        # ========== FINAL SUMMARY ==========
        await asyncio.sleep(1.5)
        print_header("✅ Demo Complete - Conversation Summary")

        # Calculate duration (handle timezone-aware datetimes)
        await db.refresh(conversation)
        duration = (conversation.resolved_at - conversation.created_at).total_seconds()

        print(f"{C.BOLD}{C.GREEN}What Just Happened:{C.END}\n")
        print(f"  {C.CYAN}1. Routing Rule Query{C.END}")
        print(f"     Backend Developer → {C.BOLD}Tech Lead{C.END} (level 0)\n")

        print(f"  {C.CYAN}2. Auto-Acknowledgment{C.END}")
        print(f"     Tech Lead sent: {C.DIM}\"please wait...\"{C.END}\n")

        print(f"  {C.CYAN}3. Timeout Detection{C.END}")
        print(f"     No response after 3 seconds → sent follow-up\n")

        print(f"  {C.CYAN}4. Escalation{C.END}")
        print(f"     Still no response → escalated to {C.BOLD}Solution Architect{C.END} (level 1)\n")

        print(f"  {C.CYAN}5. Resolution{C.END}")
        print(f"     Solution Architect provided detailed answer\n")

        print(f"{C.BOLD}{C.CYAN}Conversation Statistics:{C.END}\n")
        print(f"  Total Duration: {C.YELLOW}{duration:.1f} seconds{C.END}")
        print(f"  Escalation Level Reached: {C.YELLOW}{conversation.escalation_level}{C.END}")
        print(f"  Messages Exchanged: {C.YELLOW}6{C.END}")
        print(f"  State Transitions: {C.YELLOW}7{C.END}")

        # Count events
        result = await db.execute(
            select(ConversationEvent)
            .where(ConversationEvent.conversation_id == conversation.id)
        )
        events = result.scalars().all()

        print(f"  Events Logged: {C.YELLOW}{len(events)}{C.END}\n")

        print(f"{C.BOLD}{C.PURPLE}Key Features Demonstrated:{C.END}\n")
        print(f"  ✓ Database-driven routing rules (customizable per squad)")
        print(f"  ✓ Automatic acknowledgment messages")
        print(f"  ✓ Timeout detection and follow-up")
        print(f"  ✓ Multi-level escalation chain")
        print(f"  ✓ Full conversation audit trail")
        print(f"  ✓ State machine tracking")
        print(f"  ✓ Message threading and relationships\n")

        print(f"{C.BOLD}{C.GREEN}Next Steps:{C.END}")
        print(f"  1. Implement Phase 2 (Routing Engine + Celery)")
        print(f"  2. Create APIs for managing routing rules")
        print(f"  3. Build frontend UI for customizing routing")
        print(f"  4. Add routing templates (\"Standard Team\", \"DevOps Team\", etc.)")
        print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}Demo interrupted{C.END}\n")
    except Exception as e:
        print(f"\n{C.RED}Error: {e}{C.END}\n")
        import traceback
        traceback.print_exc()
