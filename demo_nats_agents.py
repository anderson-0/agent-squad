#!/usr/bin/env python3
"""
NATS Agent Communication Demo

Shows clean agent-to-agent communication via NATS JetStream.
"""
import asyncio
import sys
import os
from datetime import datetime
from uuid import uuid4

# Setup path
sys.path.insert(0, '/Users/anderson/Documents/anderson-0/agent-squad')

# ENABLE NATS MODE
os.environ['MESSAGE_BUS'] = 'nats'
os.environ['NATS_URL'] = 'nats://localhost:4222'
os.environ['DEBUG'] = 'False'

# SUPPRESS ALL LOGGING except our custom output
import logging
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger('sqlalchemy').setLevel(logging.CRITICAL)
logging.getLogger('sqlalchemy.engine').setLevel(logging.CRITICAL)
logging.getLogger('sqlalchemy.pool').setLevel(logging.CRITICAL)
logging.getLogger('backend').setLevel(logging.CRITICAL)

import structlog
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.CRITICAL),
)

from sqlalchemy import select
from backend.core.database import AsyncSessionLocal
from backend.models.user import User
from backend.services.squad_service import SquadService
from backend.services.agent_service import AgentService
from backend.services.task_execution_service import TaskExecutionService
from backend.agents.communication.message_bus import get_message_bus
from backend.models.project import Project, Task


# Terminal colors
class C:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


def print_header(text):
    """Print a styled header"""
    print(f"\n{C.BOLD}{C.CYAN}{'=' * 80}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{text.center(80)}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{'=' * 80}{C.END}\n")


def print_message(emoji, sender, recipient, msg_type, content):
    """Print a clean message"""
    timestamp = datetime.now().strftime("%H:%M:%S")

    # Header
    print(f"{C.DIM}[{timestamp}]{C.END} {emoji} "
          f"{C.BOLD}{C.YELLOW}{sender}{C.END} → "
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


async def main():
    print_header("🚀 NATS Agent Communication Demo")

    print(f"{C.CYAN}Initializing agents and NATS message bus...{C.END}\n")

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
            name='NATS Demo Squad',
            description='Demonstrating NATS message bus'
        )

        # Create agents
        pm = await AgentService.create_squad_member(
            db=db,
            squad_id=squad.id,
            role='project_manager',
            llm_provider='anthropic',
            llm_model='claude-3-5-sonnet-20241022'
        )

        backend = await AgentService.create_squad_member(
            db=db,
            squad_id=squad.id,
            role='backend_developer',
            specialization='python_fastapi',
            llm_provider='openai',
            llm_model='gpt-4'
        )

        frontend = await AgentService.create_squad_member(
            db=db,
            squad_id=squad.id,
            role='frontend_developer',
            specialization='react_nextjs',
            llm_provider='openai',
            llm_model='gpt-4'
        )

        qa = await AgentService.create_squad_member(
            db=db,
            squad_id=squad.id,
            role='qa_tester',
            llm_provider='openai',
            llm_model='gpt-4'
        )

        await db.commit()

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
            title='Implement Shopping Cart',
            description='Real-time shopping cart with persistence',
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
        print(f"{C.GREEN}✓ Agents: PM, Backend, Frontend, QA{C.END}")
        print(f"{C.GREEN}✓ Task: {task.title}{C.END}")
        print(f"{C.GREEN}✓ Using NATS Message Bus{C.END}\n")

        print_header("📡 Agent Communication via NATS JetStream")

        # Get NATS bus and connect
        bus = get_message_bus()
        if not bus._connected:
            await bus.connect()

        # Simulate realistic workflow
        await asyncio.sleep(1)

        # Message 1: PM kicks off
        print_message(
            "📢", "Project Manager", "All Agents", "standup",
            "Good morning team! Today we're implementing the shopping cart feature. Let's coordinate our approach."
        )
        await bus.send_message(
            sender_id=pm.id,
            recipient_id=None,
            content="Good morning team! Today we're implementing the shopping cart feature. Let's coordinate our approach.",
            message_type="standup",
            task_execution_id=execution.id,
            db=db
        )
        await db.commit()
        await asyncio.sleep(2)

        # Message 2: PM → Backend
        print_message(
            "📝", "Project Manager", "Backend Developer", "task_assignment",
            "Please implement the cart API with add/remove items, quantity updates, and persistence using Redis."
        )
        await bus.send_message(
            sender_id=pm.id,
            recipient_id=backend.id,
            content="Please implement the cart API with add/remove items, quantity updates, and persistence using Redis.",
            message_type="task_assignment",
            task_execution_id=execution.id,
            metadata={"priority": "high"},
            db=db
        )
        await db.commit()
        await asyncio.sleep(2)

        # Message 3: Backend acknowledges
        print_message(
            "✅", "Backend Developer", "Project Manager", "acknowledgment",
            "On it! I'll use FastAPI with Redis for cart state. ETA: 4 hours."
        )
        await bus.send_message(
            sender_id=backend.id,
            recipient_id=pm.id,
            content="On it! I'll use FastAPI with Redis for cart state. ETA: 4 hours.",
            message_type="acknowledgment",
            task_execution_id=execution.id,
            db=db
        )
        await db.commit()
        await asyncio.sleep(2)

        # Message 4: PM → Frontend
        print_message(
            "📝", "Project Manager", "Frontend Developer", "task_assignment",
            "Build the cart UI with React. Need: item list, quantity controls, price totals, and checkout button."
        )
        await bus.send_message(
            sender_id=pm.id,
            recipient_id=frontend.id,
            content="Build the cart UI with React. Need: item list, quantity controls, price totals, and checkout button.",
            message_type="task_assignment",
            task_execution_id=execution.id,
            metadata={"priority": "high"},
            db=db
        )
        await db.commit()
        await asyncio.sleep(2)

        # Message 5: Frontend → Backend
        print_message(
            "❓", "Frontend Developer", "Backend Developer", "question",
            "What endpoints will be available? Also, is there WebSocket support for real-time updates?"
        )
        await bus.send_message(
            sender_id=frontend.id,
            recipient_id=backend.id,
            content="What endpoints will be available? Also, is there WebSocket support for real-time updates?",
            message_type="question",
            task_execution_id=execution.id,
            db=db
        )
        await db.commit()
        await asyncio.sleep(2.5)

        # Message 6: Backend → Frontend
        print_message(
            "💬", "Backend Developer", "Frontend Developer", "answer",
            "Endpoints: POST /cart/items, PUT /cart/items/:id, DELETE /cart/items/:id, GET /cart. Yes, WebSocket at /ws/cart for live updates!"
        )
        await bus.send_message(
            sender_id=backend.id,
            recipient_id=frontend.id,
            content="Endpoints: POST /cart/items, PUT /cart/items/:id, DELETE /cart/items/:id, GET /cart. Yes, WebSocket at /ws/cart for live updates!",
            message_type="answer",
            task_execution_id=execution.id,
            db=db
        )
        await db.commit()
        await asyncio.sleep(2)

        # Message 7: Frontend acknowledges
        print_message(
            "👍", "Frontend Developer", "Backend Developer", "acknowledgment",
            "Perfect! Starting on the UI now. Will integrate WebSocket for real-time cart updates."
        )
        await bus.send_message(
            sender_id=frontend.id,
            recipient_id=backend.id,
            content="Perfect! Starting on the UI now. Will integrate WebSocket for real-time cart updates.",
            message_type="acknowledgment",
            task_execution_id=execution.id,
            db=db
        )
        await db.commit()
        await asyncio.sleep(3)

        # Message 8: Backend → PM
        print_message(
            "📊", "Backend Developer", "Project Manager", "status_update",
            "Progress: Cart API complete! ✓ CRUD operations ✓ Redis caching ✓ WebSocket support. Running tests now."
        )
        await bus.send_message(
            sender_id=backend.id,
            recipient_id=pm.id,
            content="Progress: Cart API complete! ✓ CRUD operations ✓ Redis caching ✓ WebSocket support. Running tests now.",
            message_type="status_update",
            task_execution_id=execution.id,
            metadata={"progress": 80},
            db=db
        )
        await db.commit()
        await asyncio.sleep(2.5)

        # Message 9: Frontend → PM
        print_message(
            "📊", "Frontend Developer", "Project Manager", "status_update",
            "UI is looking great! Cart items render, quantities update smoothly, totals calculate correctly. Integrating WebSocket next."
        )
        await bus.send_message(
            sender_id=frontend.id,
            recipient_id=pm.id,
            content="UI is looking great! Cart items render, quantities update smoothly, totals calculate correctly. Integrating WebSocket next.",
            message_type="status_update",
            task_execution_id=execution.id,
            metadata={"progress": 70},
            db=db
        )
        await db.commit()
        await asyncio.sleep(3)

        # Message 10: PM → QA
        print_message(
            "📝", "Project Manager", "QA Engineer", "task_assignment",
            "Backend and frontend are almost ready. Please prepare test scenarios for cart functionality."
        )
        await bus.send_message(
            sender_id=pm.id,
            recipient_id=qa.id,
            content="Backend and frontend are almost ready. Please prepare test scenarios for cart functionality.",
            message_type="task_assignment",
            task_execution_id=execution.id,
            db=db
        )
        await db.commit()
        await asyncio.sleep(2)

        # Message 11: QA acknowledges
        print_message(
            "🧪", "QA Engineer", "Project Manager", "acknowledgment",
            "Will test: add/remove items, quantity edge cases, persistence, concurrent users, and WebSocket sync. Test plan ready!"
        )
        await bus.send_message(
            sender_id=qa.id,
            recipient_id=pm.id,
            content="Will test: add/remove items, quantity edge cases, persistence, concurrent users, and WebSocket sync. Test plan ready!",
            message_type="acknowledgment",
            task_execution_id=execution.id,
            db=db
        )
        await db.commit()
        await asyncio.sleep(2.5)

        # Message 12: Backend completion
        print_message(
            "🎉", "Backend Developer", "All Agents", "completion_notification",
            "Backend DONE! All tests passing (127/127). Cart API is production-ready with Redis persistence and real-time WebSocket updates!"
        )
        await bus.send_message(
            sender_id=backend.id,
            recipient_id=None,
            content="Backend DONE! All tests passing (127/127). Cart API is production-ready with Redis persistence and real-time WebSocket updates!",
            message_type="completion_notification",
            task_execution_id=execution.id,
            metadata={"tests_passing": True},
            db=db
        )
        await db.commit()
        await asyncio.sleep(2)

        # Message 13: PM celebrates
        print_message(
            "🎊", "Project Manager", "All Agents", "standup",
            "Excellent teamwork! Backend is solid, frontend is beautiful, QA has the plan. Let's integrate and ship this cart feature! 🚀"
        )
        await bus.send_message(
            sender_id=pm.id,
            recipient_id=None,
            content="Excellent teamwork! Backend is solid, frontend is beautiful, QA has the plan. Let's integrate and ship this cart feature! 🚀",
            message_type="standup",
            task_execution_id=execution.id,
            db=db
        )
        await db.commit()

        # Final summary
        await asyncio.sleep(1.5)
        print_header("✅ Demo Complete!")

        print(f"{C.BOLD}{C.GREEN}What Just Happened:{C.END}")
        print(f"  ✓ All agent messages sent via {C.CYAN}NATS JetStream{C.END}")
        print(f"  ✓ Messages persisted in NATS Docker container")
        print(f"  ✓ Messages also saved to PostgreSQL")
        print(f"  ✓ 13 messages exchanged between 4 agents")
        print()
        print(f"{C.BOLD}{C.CYAN}NATS Stats:{C.END}")

        # Get NATS stats
        stats = await bus.get_stats()
        if stats.get('connected'):
            print(f"  Stream: {stats.get('stream_name')}")
            print(f"  Total messages in stream: {stats.get('total_messages', 0):,}")
            print(f"  Storage used: {stats.get('total_bytes', 0):,} bytes")

        print()
        print(f"{C.BOLD}{C.YELLOW}Check NATS Health:{C.END}")
        print(f"  curl http://localhost:8222/varz | jq")
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
