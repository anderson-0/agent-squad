#!/usr/bin/env python3
"""Create demo squad and run agent communication"""
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
from backend.core.database import AsyncSessionLocal
from backend.models.user import User
from backend.services.squad_service import SquadService
from backend.services.agent_service import AgentService
from backend.services.task_execution_service import TaskExecutionService
from backend.agents.communication.message_bus import get_message_bus
from backend.models.project import Project, Task
from uuid import uuid4

async def main():
    print("=" * 70)
    print("🤖  Creating Demo Squad and Running Agent Communication".center(70))
    print("=" * 70)
    print()

    async with AsyncSessionLocal() as db:
        # 1. Create or get user
        print("Step 1: Creating user...")
        result = await db.execute(select(User).where(User.email == 'demo@test.com'))
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                id=uuid4(),
                email='demo@test.com',
                password_hash='demo_hash',
                name='Demo User',
                is_active=True,
                email_verified=True
            )
            db.add(user)
            await db.flush()
            print(f"✅ Created user: {user.email}")
        else:
            print(f"✅ Using existing user: {user.email}")

        # 2. Create squad
        print("\nStep 2: Creating squad...")
        squad = await SquadService.create_squad(
            db=db,
            user_id=user.id,
            name='Live Demo Squad',
            description='Demo squad for agent communication'
        )
        print(f"✅ Squad created: {squad.name}")
        print(f"   Squad ID: {squad.id}")

        # 3. Create agents
        print("\nStep 3: Creating agents...")

        pm = await AgentService.create_squad_member(
            db=db,
            squad_id=squad.id,
            role='project_manager',
            specialization=None,
            llm_provider='anthropic',
            llm_model='claude-3-5-sonnet-20241022'
        )
        print(f"✅ Project Manager created (ID: {pm.id})")

        backend = await AgentService.create_squad_member(
            db=db,
            squad_id=squad.id,
            role='backend_developer',
            specialization='python_fastapi',
            llm_provider='openai',
            llm_model='gpt-4'
        )
        print(f"✅ Backend Developer created (ID: {backend.id})")

        frontend = await AgentService.create_squad_member(
            db=db,
            squad_id=squad.id,
            role='frontend_developer',
            specialization='react_nextjs',
            llm_provider='openai',
            llm_model='gpt-4'
        )
        print(f"✅ Frontend Developer created (ID: {frontend.id})")

        await db.commit()

        # 4. Create project and task
        print("\nStep 4: Creating task...")
        project = Project(
            id=uuid4(),
            squad_id=squad.id,
            name='Demo Project',
            description='Demo project for testing',
            is_active=True
        )
        db.add(project)
        await db.flush()

        task = Task(
            id=uuid4(),
            project_id=project.id,
            title='Build User Authentication',
            description='Implement login and registration with JWT',
            status='pending',
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

        print(f"✅ Task created: {task.title}")
        print(f"   Execution ID: {execution.id}")

        # 5. Simulate agent messages
        print("\n" + "=" * 70)
        print("🚀  Simulating Agent Communication".center(70))
        print("=" * 70)
        print()

        bus = get_message_bus()

        # Message 1: PM standup
        print("📢 PM → All: Starting daily standup...")
        await bus.send_message(
            sender_id=pm.id,
            recipient_id=None,
            content="Good morning team! Today we're building user authentication.",
            message_type="standup",
            task_execution_id=execution.id,
            db=db
        )
        await db.commit()
        await asyncio.sleep(0.5)

        # Message 2: PM assigns to backend
        print("📝 PM → Backend Dev: Assigning backend work...")
        await bus.send_message(
            sender_id=pm.id,
            recipient_id=backend.id,
            content="Please implement the authentication API endpoints with JWT.",
            message_type="task_assignment",
            task_execution_id=execution.id,
            metadata={"priority": "high", "estimated_hours": 8},
            db=db
        )
        await db.commit()
        await asyncio.sleep(0.5)

        # Message 3: Backend acknowledges
        print("✅ Backend Dev → PM: Acknowledged task...")
        await bus.send_message(
            sender_id=backend.id,
            recipient_id=pm.id,
            content="Got it! I'll start with the data models and then build the endpoints.",
            message_type="acknowledgment",
            task_execution_id=execution.id,
            db=db
        )
        await db.commit()
        await asyncio.sleep(0.5)

        # Message 4: PM assigns to frontend
        print("📝 PM → Frontend Dev: Assigning UI work...")
        await bus.send_message(
            sender_id=pm.id,
            recipient_id=frontend.id,
            content="Please create the login and registration UI components.",
            message_type="task_assignment",
            task_execution_id=execution.id,
            metadata={"priority": "high", "estimated_hours": 6},
            db=db
        )
        await db.commit()
        await asyncio.sleep(0.5)

        # Message 5: Frontend asks question
        print("❓ Frontend Dev → Backend Dev: Asking about API...")
        await bus.send_message(
            sender_id=frontend.id,
            recipient_id=backend.id,
            content="What will the API response format be? I want to handle the data correctly.",
            message_type="question",
            task_execution_id=execution.id,
            db=db
        )
        await db.commit()
        await asyncio.sleep(0.5)

        # Message 6: Backend answers
        print("💬 Backend Dev → Frontend Dev: Explaining API format...")
        await bus.send_message(
            sender_id=backend.id,
            recipient_id=frontend.id,
            content="The API returns JSON: {data: {...}, meta: {count, page}, errors: [...]}. I'll document it in Swagger.",
            message_type="answer",
            task_execution_id=execution.id,
            db=db
        )
        await db.commit()
        await asyncio.sleep(0.5)

        # Message 7: Frontend thanks
        print("👍 Frontend Dev → Backend Dev: Thank you!")
        await bus.send_message(
            sender_id=frontend.id,
            recipient_id=backend.id,
            content="Perfect, that helps a lot! Starting on the components now.",
            message_type="acknowledgment",
            task_execution_id=execution.id,
            db=db
        )
        await db.commit()

        # Complete
        print()
        print("=" * 70)
        print("✅  Demo Completed Successfully!".center(70))
        print("=" * 70)
        print()
        print(f"📊 Summary:")
        print(f"  • Squad ID: {squad.id}")
        print(f"  • Execution ID: {execution.id}")
        print(f"  • Agents: 3 (PM, Backend Dev, Frontend Dev)")
        print(f"  • Messages Sent: 7")
        print()
        print(f"💡 To view messages via SSE stream:")
        print(f"   PYTHONPATH=/Users/anderson/Documents/anderson-0/agent-squad \\")
        print(f"     uv run python -m backend.cli.stream_agent_messages \\")
        print(f"     --execution-id {execution.id}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
