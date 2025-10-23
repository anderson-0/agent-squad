#!/usr/bin/env python3
"""
Test Celery Automatic Timeout Monitoring

This script creates a conversation and watches Celery automatically:
1. Detect the timeout
2. Send follow-up message
3. Escalate if still no response
"""
import asyncio
import sys
from datetime import datetime, timedelta
from uuid import uuid4

sys.path.insert(0, '/Users/anderson/Documents/anderson-0/agent-squad')

from sqlalchemy import select
from backend.core.database import AsyncSessionLocal
from backend.models.user import User
from backend.models.conversation import Conversation, ConversationState, ConversationEvent
from backend.models.routing_rule import RoutingRule
from backend.models.message import AgentMessage
from backend.services.squad_service import SquadService
from backend.services.agent_service import AgentService
from backend.agents.communication.message_bus import get_message_bus

# Terminal colors
class C:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ORANGE = '\033[38;5;208m'
    END = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


async def main():
    print(f"\n{C.BOLD}{C.CYAN}{'=' * 80}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{'🤖 Celery Automatic Timeout Monitoring Test'.center(80)}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{'=' * 80}{C.END}\n")

    async with AsyncSessionLocal() as db:
        # Get or create user
        result = await db.execute(select(User).where(User.email == 'celery@test.com'))
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                id=uuid4(),
                email='celery@test.com',
                name='Celery Test User',
                password_hash='dummy'
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Create squad
        print(f"{C.CYAN}📦 Setting up squad...{C.END}")
        squad = await SquadService.create_squad(
            db=db,
            user_id=user.id,
            name='Celery Timeout Test Squad',
            description='Testing automatic Celery timeout monitoring'
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

        await db.commit()

        # Set up routing rules
        print(f"{C.CYAN}⚙️  Creating routing rules...{C.END}")
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
        ]

        for rule_data in rules:
            rule = RoutingRule(
                id=uuid4(),
                squad_id=squad.id,
                asker_role=rule_data["asker_role"],
                question_type=rule_data["question_type"],
                escalation_level=rule_data["escalation_level"],
                responder_role=rule_data["responder_role"],
                is_active=True,
                priority=0,
                rule_metadata={}
            )
            db.add(rule)

        await db.commit()

        # Get message bus
        bus = get_message_bus()
        if not bus._connected:
            await bus.connect()

        print(f"{C.GREEN}✓ Setup complete!{C.END}\n")

        # Create a conversation with a SHORT timeout for demo
        print(f"{C.BOLD}{C.YELLOW}Step 1: Creating conversation with 30-second timeout{C.END}")
        print(f"{C.DIM}       (Celery checks timeouts every 60 seconds){C.END}\n")

        question_content = "How should I implement authentication? This will timeout automatically."

        # Send initial message
        initial_message_response = await bus.send_message(
            sender_id=backend.id,
            recipient_id=tech_lead.id,
            content=question_content,
            message_type="question",
            task_execution_id=None,
            db=db
        )
        await db.commit()  # Commit message first

        # Get the message ID
        message_id = initial_message_response.id

        # Create conversation with short timeout
        timeout_at = datetime.utcnow() + timedelta(seconds=30)  # 30 seconds from now

        conversation = Conversation(
            id=uuid4(),
            initial_message_id=message_id,
            current_state=ConversationState.WAITING.value,  # Set to WAITING (acknowledged)
            asker_id=backend.id,
            current_responder_id=tech_lead.id,
            escalation_level=0,
            question_type='implementation',
            task_execution_id=None,
            timeout_at=timeout_at,
            acknowledged_at=datetime.utcnow(),
            conv_metadata={}
        )
        db.add(conversation)

        # Create initial events
        init_event = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation.id,
            event_type='initiated',
            from_state=None,
            to_state=ConversationState.INITIATED.value,
            message_id=message_id,
            triggered_by_agent_id=backend.id,
            event_data={}
        )
        db.add(init_event)

        ack_event = ConversationEvent(
            id=uuid4(),
            conversation_id=conversation.id,
            event_type='acknowledged',
            from_state=ConversationState.INITIATED.value,
            to_state=ConversationState.WAITING.value,
            message_id=message_id,
            triggered_by_agent_id=tech_lead.id,
            event_data={}
        )
        db.add(ack_event)

        await db.commit()

        print(f"{C.GREEN}✓ Conversation created{C.END}")
        print(f"  ID: {C.DIM}{conversation.id}{C.END}")
        print(f"  Timeout at: {C.YELLOW}{timeout_at.strftime('%H:%M:%S')}{C.END}")
        print(f"  Current state: {C.ORANGE}{conversation.current_state}{C.END}\n")

        print(f"{C.BOLD}{C.CYAN}{'=' * 80}{C.END}")
        print(f"{C.BOLD}{C.CYAN}{'Watching for Celery automatic timeout handling...'.center(80)}{C.END}")
        print(f"{C.BOLD}{C.CYAN}{'=' * 80}{C.END}\n")

        print(f"{C.YELLOW}⏰ Waiting for Celery to detect timeout (check every 60s)...{C.END}")
        print(f"{C.DIM}   Celery Beat will trigger check_timeouts_task automatically{C.END}\n")

        # Monitor the conversation for changes
        last_state = conversation.current_state
        last_event_count = 2  # We created 2 events initially

        for i in range(12):  # Check for 2 minutes
            await asyncio.sleep(10)

            # Refresh conversation from DB
            await db.refresh(conversation)

            # Count events
            result = await db.execute(
                select(ConversationEvent)
                .where(ConversationEvent.conversation_id == conversation.id)
            )
            events = result.scalars().all()
            event_count = len(events)

            # Check if state changed
            if conversation.current_state != last_state:
                print(f"\n{C.ORANGE}🔔 STATE CHANGE DETECTED!{C.END}")
                print(f"   {C.DIM}{last_state}{C.END} → {C.BOLD}{C.ORANGE}{conversation.current_state}{C.END}")
                last_state = conversation.current_state

                # Show latest event
                latest_event = events[-1]
                print(f"   Event: {C.CYAN}{latest_event.event_type}{C.END}")
                print(f"   Time: {C.YELLOW}{latest_event.created_at.strftime('%H:%M:%S')}{C.END}\n")

            # Check if new events were created
            if event_count > last_event_count:
                new_events = event_count - last_event_count
                print(f"{C.GREEN}📝 {new_events} new event(s) logged by Celery!{C.END}")
                last_event_count = event_count

            # Check if conversation was escalated or resolved
            if conversation.current_state in ['escalated', 'answered', 'follow_up']:
                break

            # Print progress dots
            if i % 6 == 0 and i > 0:
                print(f"{C.DIM}   Still watching... ({i * 10}s elapsed){C.END}")

        # Final status
        await db.refresh(conversation)
        result = await db.execute(
            select(ConversationEvent)
            .where(ConversationEvent.conversation_id == conversation.id)
            .order_by(ConversationEvent.created_at)
        )
        all_events = result.scalars().all()

        print(f"\n{C.BOLD}{C.CYAN}{'=' * 80}{C.END}")
        print(f"{C.BOLD}{C.CYAN}{'Final Status'.center(80)}{C.END}")
        print(f"{C.BOLD}{C.CYAN}{'=' * 80}{C.END}\n")

        print(f"{C.BOLD}Conversation State:{C.END} {C.ORANGE}{conversation.current_state}{C.END}")
        print(f"{C.BOLD}Escalation Level:{C.END} {C.YELLOW}{conversation.escalation_level}{C.END}")
        print(f"{C.BOLD}Total Events:{C.END} {C.YELLOW}{len(all_events)}{C.END}\n")

        print(f"{C.BOLD}Event Timeline:{C.END}")
        for event in all_events:
            time_str = event.created_at.strftime('%H:%M:%S')
            print(f"  {C.DIM}[{time_str}]{C.END} {C.CYAN}{event.event_type:15}{C.END} "
                  f"{C.DIM}{event.from_state or 'None':12} → {event.to_state:12}{C.END}")

        if conversation.current_state == 'follow_up':
            print(f"\n{C.GREEN}✅ Success! Celery automatically sent follow-up message!{C.END}")
        elif conversation.current_state == 'escalated':
            print(f"\n{C.GREEN}✅ Success! Celery automatically escalated the conversation!{C.END}")
        else:
            print(f"\n{C.YELLOW}⏳ Still in progress. Check may have completed after script ended.{C.END}")

        print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}Test interrupted{C.END}\n")
    except Exception as e:
        print(f"\n{C.RED}Error: {e}{C.END}\n")
        import traceback
        traceback.print_exc()
