#!/usr/bin/env python3
"""
Real-time Streaming Demo - Live Agent Communication

This script creates agents, sends messages one-by-one with realistic delays,
and shows them streaming in real-time (like ChatGPT/Claude interface).

Messages are stored in the database and broadcast via SSE, so you can watch
them in multiple ways:
1. This terminal (built-in display)
2. Another terminal (using the SSE CLI client)
3. Frontend web app (when implemented)

Usage:
    python realtime_streaming_demo.py

To watch in another terminal simultaneously:
    Terminal 1: python realtime_streaming_demo.py
    Terminal 2: python -m backend.cli.stream_agent_messages --execution-id <ID>
"""
import asyncio
import sys
import logging
import os
sys.path.insert(0, '/Users/anderson/Documents/anderson-0/agent-squad')

# Disable DEBUG mode and verbose logging
os.environ['DEBUG'] = 'False'
logging.basicConfig(level=logging.ERROR)
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.pool').setLevel(logging.ERROR)
import structlog
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.CRITICAL),
)

from sqlalchemy import select
from uuid import uuid4
from datetime import datetime
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


def print_message(emoji, sender, recipient, msg_type, content, show_streaming=True):
    """Print a message with streaming effect"""
    timestamp = datetime.now().strftime("%H:%M:%S")

    # Header
    print(f"{C.DIM}[{timestamp}]{C.END} {emoji} "
          f"{C.BOLD}{C.YELLOW}{sender}{C.END} → "
          f"{C.BOLD}{C.GREEN}{recipient}{C.END}")
    print(f"{C.DIM}           {msg_type.upper().replace('_', ' ')}{C.END}")
    print(f"{C.DIM}           ┌{'─' * 60}┐{C.END}")

    if show_streaming:
        # Simulate streaming/typing effect
        words = content.split()
        line = "           │ "
        for i, word in enumerate(words):
            if len(line) + len(word) + 1 > 71:
                print(f"{C.DIM}{line + ' ' * (73 - len(line))}│{C.END}")
                line = "           │ " + word
            else:
                if line.endswith('│ '):
                    line += word
                else:
                    line += ' ' + word

            # Print intermediate state for streaming effect
            if i % 3 == 0 and i > 0:
                sys.stdout.write(f"\r{C.DIM}{line + ' ' * (73 - len(line))}│{C.END}")
                sys.stdout.flush()
                asyncio.sleep(0.05)  # Small delay for streaming effect

        if line != "           │ ":
            print(f"{C.DIM}{line + ' ' * (73 - len(line))}│{C.END}")
    else:
        # No streaming, just print
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
    print_header("🚀 Real-time Agent Streaming Demo")

    print(f"{C.DIM}Initializing squad and agents...{C.END}")

    async with AsyncSessionLocal() as db:
        # Get user
        result = await db.execute(select(User).where(User.email == 'demo@test.com'))
        user = result.scalar_one_or_none()

        if not user:
            print(f"\n{C.RED}Error: Demo user not found.{C.END}")
            print(f"{C.YELLOW}Please run create_squad_now.py first to create the demo user.{C.END}\n")
            return

        # Create squad
        squad = await SquadService.create_squad(
            db=db, user_id=user.id,
            name='Real-time Streaming Squad',
            description='Live demo squad'
        )

        # Create agents
        pm = await AgentService.create_squad_member(
            db=db, squad_id=squad.id, role='project_manager',
            llm_provider='anthropic', llm_model='claude-3-5-sonnet-20241022'
        )
        backend = await AgentService.create_squad_member(
            db=db, squad_id=squad.id, role='backend_developer',
            specialization='python_fastapi', llm_provider='openai', llm_model='gpt-4'
        )
        frontend = await AgentService.create_squad_member(
            db=db, squad_id=squad.id, role='frontend_developer',
            specialization='react_nextjs', llm_provider='openai', llm_model='gpt-4'
        )
        await db.commit()

        # Create task
        project = Project(
            id=uuid4(), squad_id=squad.id, name='Demo Project',
            description='Demo', is_active=True
        )
        db.add(project)
        await db.flush()

        task = Task(
            id=uuid4(), project_id=project.id,
            title='Build WebSocket Chat',
            description='Real-time chat with WebSocket',
            status='pending', priority='high'
        )
        db.add(task)
        await db.flush()

        execution = await TaskExecutionService.start_task_execution(
            db=db, task_id=task.id, squad_id=squad.id
        )
        await db.commit()

        print(f"\n{C.GREEN}✓ Squad created{C.END}")
        print(f"{C.GREEN}✓ Agents: Project Manager, Backend Dev, Frontend Dev{C.END}")
        print(f"{C.GREEN}✓ Task: {task.title}{C.END}")
        print(f"{C.BOLD}{C.CYAN}✓ Execution ID: {execution.id}{C.END}\n")

        print(f"{C.DIM}{'─' * 80}{C.END}")
        print(f"{C.BOLD}💡 Pro tip:{C.END} Open another terminal and run:")
        print(f"{C.CYAN}   PYTHONPATH=/Users/anderson/Documents/anderson-0/agent-squad \\{C.END}")
        print(f"{C.CYAN}   uv run python -m backend.cli.stream_agent_messages \\{C.END}")
        print(f"{C.CYAN}   --execution-id {execution.id} --base-url http://localhost:8000{C.END}")
        print(f"{C.DIM}   (You'll see messages appear in both terminals simultaneously!){C.END}")
        print(f"{C.DIM}{'─' * 80}{C.END}\n")

        print_header("📡 Live Message Stream Starting...")
        print(f"{C.DIM}Messages will appear below as agents communicate...{C.END}\n")

        bus = get_message_bus()

        # Simulate realistic agent workflow with delays
        # Each message is stored in DB and broadcast via SSE

        await asyncio.sleep(1)

        # Message 1: PM starts standup
        print_message(
            "📢", "Project Manager", "All Agents", "standup",
            "Good morning team! Today we're implementing WebSocket-based real-time chat. Let's coordinate our approach."
        )
        await bus.send_message(
            sender_id=pm.id, recipient_id=None,
            content="Good morning team! Today we're implementing WebSocket-based real-time chat. Let's coordinate our approach.",
            message_type="standup", task_execution_id=execution.id, db=db
        )
        await db.commit()
        await asyncio.sleep(2.5)

        # Message 2: PM → Backend
        print_message(
            "📝", "Project Manager", "Backend Developer", "task_assignment",
            "Please implement the WebSocket server using Socket.IO. We need: connection handling, room management, message broadcasting, and presence tracking."
        )
        await bus.send_message(
            sender_id=pm.id, recipient_id=backend.id,
            content="Please implement the WebSocket server using Socket.IO. We need: connection handling, room management, message broadcasting, and presence tracking.",
            message_type="task_assignment", task_execution_id=execution.id,
            metadata={"priority": "high", "estimated_hours": 8}, db=db
        )
        await db.commit()
        await asyncio.sleep(2)

        # Message 3: Backend acknowledges
        print_message(
            "✅", "Backend Developer", "Project Manager", "acknowledgment",
            "Understood! I'll use Socket.IO with Redis adapter for horizontal scaling. Starting with connection management."
        )
        await bus.send_message(
            sender_id=backend.id, recipient_id=pm.id,
            content="Understood! I'll use Socket.IO with Redis adapter for horizontal scaling. Starting with connection management.",
            message_type="acknowledgment", task_execution_id=execution.id, db=db
        )
        await db.commit()
        await asyncio.sleep(2.5)

        # Message 4: PM → Frontend
        print_message(
            "📝", "Project Manager", "Frontend Developer", "task_assignment",
            "Create the chat UI with React. Components needed: message list with virtualization, message input, typing indicators, user presence, and real-time updates."
        )
        await bus.send_message(
            sender_id=pm.id, recipient_id=frontend.id,
            content="Create the chat UI with React. Components needed: message list with virtualization, message input, typing indicators, user presence, and real-time updates.",
            message_type="task_assignment", task_execution_id=execution.id,
            metadata={"priority": "high", "estimated_hours": 10}, db=db
        )
        await db.commit()
        await asyncio.sleep(3)

        # Message 5: Frontend → Backend question
        print_message(
            "❓", "Frontend Developer", "Backend Developer", "question",
            "What Socket.IO events should I listen for? Also, what's the message payload structure for incoming messages?"
        )
        await bus.send_message(
            sender_id=frontend.id, recipient_id=backend.id,
            content="What Socket.IO events should I listen for? Also, what's the message payload structure for incoming messages?",
            message_type="question", task_execution_id=execution.id, db=db
        )
        await db.commit()
        await asyncio.sleep(2.5)

        # Message 6: Backend detailed answer
        print_message(
            "💬", "Backend Developer", "Frontend Developer", "answer",
            "Events: 'message' (payload: {id, userId, username, content, timestamp, roomId}), 'user:joined', 'user:left', 'typing:start', 'typing:stop'. Full event spec coming in 20 mins!"
        )
        await bus.send_message(
            sender_id=backend.id, recipient_id=frontend.id,
            content="Events: 'message' (payload: {id, userId, username, content, timestamp, roomId}), 'user:joined', 'user:left', 'typing:start', 'typing:stop'. Full event spec coming in 20 mins!",
            message_type="answer", task_execution_id=execution.id, db=db
        )
        await db.commit()
        await asyncio.sleep(2)

        # Message 7: Frontend acknowledges
        print_message(
            "👍", "Frontend Developer", "Backend Developer", "acknowledgment",
            "Perfect! That's enough to get started. I'll build the basic UI structure while waiting for the full spec."
        )
        await bus.send_message(
            sender_id=frontend.id, recipient_id=backend.id,
            content="Perfect! That's enough to get started. I'll build the basic UI structure while waiting for the full spec.",
            message_type="acknowledgment", task_execution_id=execution.id, db=db
        )
        await db.commit()
        await asyncio.sleep(3.5)

        # Message 8: Backend status update
        print_message(
            "📊", "Backend Developer", "Project Manager", "status_update",
            "Progress update: WebSocket server is live! ✓ Connection handling ✓ Room management ✓ Message broadcasting. Working on presence tracking now."
        )
        await bus.send_message(
            sender_id=backend.id, recipient_id=pm.id,
            content="Progress update: WebSocket server is live! ✓ Connection handling ✓ Room management ✓ Message broadcasting. Working on presence tracking now.",
            message_type="status_update", task_execution_id=execution.id,
            metadata={"progress": 60}, db=db
        )
        await db.commit()
        await asyncio.sleep(3)

        # Message 9: Frontend status update
        print_message(
            "📊", "Frontend Developer", "Project Manager", "status_update",
            "UI coming together nicely! Message list renders smoothly with virtualization. Added auto-scroll and timestamp formatting. Next: typing indicators."
        )
        await bus.send_message(
            sender_id=frontend.id, recipient_id=pm.id,
            content="UI coming together nicely! Message list renders smoothly with virtualization. Added auto-scroll and timestamp formatting. Next: typing indicators.",
            message_type="status_update", task_execution_id=execution.id,
            metadata={"progress": 55}, db=db
        )
        await db.commit()
        await asyncio.sleep(4)

        # Message 10: Backend completion
        print_message(
            "🎉", "Backend Developer", "Project Manager", "completion_notification",
            "Backend COMPLETE! All WebSocket features implemented. 100+ integration tests passing. Load tested up to 10k concurrent connections. Ready to ship!"
        )
        await bus.send_message(
            sender_id=backend.id, recipient_id=pm.id,
            content="Backend COMPLETE! All WebSocket features implemented. 100+ integration tests passing. Load tested up to 10k concurrent connections. Ready to ship!",
            message_type="completion_notification", task_execution_id=execution.id,
            metadata={"tests_passing": True, "load_tested": "10k_concurrent"}, db=db
        )
        await db.commit()
        await asyncio.sleep(2.5)

        # Message 11: PM celebration
        print_message(
            "🎊", "Project Manager", "All Agents", "standup",
            "Outstanding work, team! Backend is production-ready, frontend is beautiful. Let's integrate and test end-to-end. We're shipping real-time chat! 🚀"
        )
        await bus.send_message(
            sender_id=pm.id, recipient_id=None,
            content="Outstanding work, team! Backend is production-ready, frontend is beautiful. Let's integrate and test end-to-end. We're shipping real-time chat! 🚀",
            message_type="standup", task_execution_id=execution.id, db=db
        )
        await db.commit()

        # Final summary
        await asyncio.sleep(1.5)
        print_header("✅ Streaming Demo Complete!")

        print(f"{C.GREEN}📊 Summary:{C.END}")
        print(f"{C.DIM}  • Execution ID: {execution.id}{C.END}")
        print(f"{C.DIM}  • Squad ID: {squad.id}{C.END}")
        print(f"{C.DIM}  • Messages Sent: 11{C.END}")
        print(f"{C.DIM}  • All messages stored in database ✓{C.END}")
        print(f"{C.DIM}  • All messages broadcast via SSE ✓{C.END}")
        print()
        print(f"{C.BOLD}{C.CYAN}🎯 What just happened:{C.END}")
        print(f"{C.DIM}  1. Messages appeared in this terminal in real-time{C.END}")
        print(f"{C.DIM}  2. Each message was saved to PostgreSQL database{C.END}")
        print(f"{C.DIM}  3. Each message was broadcast via Server-Sent Events{C.END}")
        print(f"{C.DIM}  4. Frontend web apps can subscribe to the SSE stream{C.END}")
        print()
        print(f"{C.BOLD}{C.YELLOW}💡 Try this now:{C.END}")
        print(f"{C.DIM}  Query the messages from the database:{C.END}")
        print(f"{C.CYAN}  psql agent_squad_dev -c \"SELECT sender_id, content FROM agent_messages WHERE task_execution_id='{execution.id}' ORDER BY created_at;\"{C.END}")
        print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{C.YELLOW}Demo interrupted by user{C.END}\n")
    except Exception as e:
        print(f"\n{C.RED}Error: {e}{C.END}")
        import traceback
        traceback.print_exc()
