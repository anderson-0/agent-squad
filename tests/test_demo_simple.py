#!/usr/bin/env python3
"""
Simple standalone demo script that doesn't require package installation.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from uuid import uuid4
from backend.core.database import async_session_maker
from backend.models.user import User
from backend.models.squad import Squad, SquadMember
from backend.models.project import Project, Task
from backend.models.task_execution import TaskExecution
from sqlalchemy import select
from datetime import datetime


async def create_simple_demo():
    """Create and run a simple demo."""
    print("=" * 70)
    print("🤖  AGENT SQUAD - Simple Demo".center(70))
    print("=" * 70)
    print()

    async with async_session_maker() as db:
        # 1. Create or get user
        print("Step 1: Creating test user...")
        result = await db.execute(
            select(User).where(User.email == "demo@test.com")
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                id=uuid4(),
                email="demo@test.com",
                hashed_password="test_hash",
                full_name="Demo User",
                is_active=True,
                is_verified=True
            )
            db.add(user)
            await db.flush()
            print(f"✅ Created user: {user.email}")
        else:
            print(f"✅ Using existing user: {user.email}")

        # 2. Create squad
        print("\nStep 2: Creating squad...")
        squad = Squad(
            id=uuid4(),
            owner_id=user.id,
            name="Demo Squad",
            description="Simple demo squad",
            status="active"
        )
        db.add(squad)
        await db.flush()
        print(f"✅ Squad created: {squad.name} (ID: {squad.id})")

        # 3. Create agents
        print("\nStep 3: Creating agents...")
        agents = []

        # PM
        pm = SquadMember(
            id=uuid4(),
            squad_id=squad.id,
            role="project_manager",
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            is_active=True
        )
        db.add(pm)
        agents.append(pm)
        print(f"  ✅ Project Manager (ID: {pm.id})")

        # Backend Dev
        backend = SquadMember(
            id=uuid4(),
            squad_id=squad.id,
            role="backend_developer",
            specialization="python_fastapi",
            llm_provider="openai",
            llm_model="gpt-4",
            is_active=True
        )
        db.add(backend)
        agents.append(backend)
        print(f"  ✅ Backend Developer (ID: {backend.id})")

        # Frontend Dev
        frontend = SquadMember(
            id=uuid4(),
            squad_id=squad.id,
            role="frontend_developer",
            specialization="react_nextjs",
            llm_provider="openai",
            llm_model="gpt-4",
            is_active=True
        )
        db.add(frontend)
        agents.append(frontend)
        print(f"  ✅ Frontend Developer (ID: {frontend.id})")

        await db.flush()

        # 4. Create project and task
        print("\nStep 4: Creating task...")
        project = Project(
            id=uuid4(),
            name="Demo Project",
            description="Demo project",
            owner_id=user.id,
            status="active"
        )
        db.add(project)
        await db.flush()

        task = Task(
            id=uuid4(),
            project_id=project.id,
            title="Build User Authentication",
            description="Implement login and registration",
            status="pending",
            priority="high"
        )
        db.add(task)
        await db.flush()
        print(f"✅ Task created: {task.title}")

        # 5. Create execution
        print("\nStep 5: Starting execution...")
        execution = TaskExecution(
            id=uuid4(),
            task_id=task.id,
            squad_id=squad.id,
            status="in_progress",
            started_at=datetime.utcnow()
        )
        db.add(execution)
        await db.flush()
        print(f"✅ Execution started (ID: {execution.id})")

        # 6. Send messages via message bus
        print("\nStep 6: Simulating agent messages...")
        from backend.agents.communication.message_bus import get_message_bus

        bus = get_message_bus()

        # Message 1: PM broadcasts standup
        print("  📢 PM → All: Starting standup...")
        await bus.send_message(
            sender_id=pm.id,
            recipient_id=None,
            content="Good morning team! Today we're building user authentication.",
            message_type="standup",
            task_execution_id=execution.id,
            db=db
        )
        await asyncio.sleep(1)

        # Message 2: PM assigns to backend
        print("  📝 PM → Backend Dev: Assigning task...")
        await bus.send_message(
            sender_id=pm.id,
            recipient_id=backend.id,
            content="Please implement the authentication API endpoints.",
            message_type="task_assignment",
            task_execution_id=execution.id,
            metadata={"priority": "high"},
            db=db
        )
        await asyncio.sleep(1)

        # Message 3: Backend acknowledges
        print("  ✅ Backend Dev → PM: Acknowledged...")
        await bus.send_message(
            sender_id=backend.id,
            recipient_id=pm.id,
            content="Got it! I'll start with the data models.",
            message_type="acknowledgment",
            task_execution_id=execution.id,
            db=db
        )
        await asyncio.sleep(1)

        # Message 4: PM assigns to frontend
        print("  📝 PM → Frontend Dev: Assigning UI work...")
        await bus.send_message(
            sender_id=pm.id,
            recipient_id=frontend.id,
            content="Please create the login and registration UI components.",
            message_type="task_assignment",
            task_execution_id=execution.id,
            metadata={"priority": "high"},
            db=db
        )
        await asyncio.sleep(1)

        # Message 5: Frontend asks question
        print("  ❓ Frontend Dev → Backend Dev: Asking question...")
        await bus.send_message(
            sender_id=frontend.id,
            recipient_id=backend.id,
            content="What will the API response format be?",
            message_type="question",
            task_execution_id=execution.id,
            db=db
        )
        await asyncio.sleep(1)

        # Message 6: Backend answers
        print("  💬 Backend Dev → Frontend Dev: Answering...")
        await bus.send_message(
            sender_id=backend.id,
            recipient_id=frontend.id,
            content="The API will return JSON: {data: {...}, meta: {...}, errors: [...]}",
            message_type="answer",
            task_execution_id=execution.id,
            db=db
        )
        await asyncio.sleep(1)

        # Message 7: Task complete
        print("  🎉 PM → All: Task complete!")
        await bus.send_message(
            sender_id=pm.id,
            recipient_id=None,
            content="Great work team! Authentication system is complete and deployed! 🚀",
            message_type="completion_notification",
            task_execution_id=execution.id,
            db=db
        )

        await db.commit()

        print()
        print("=" * 70)
        print("✅  DEMO COMPLETED SUCCESSFULLY".center(70))
        print("=" * 70)
        print()
        print(f"📊 Summary:")
        print(f"  • Squad ID: {squad.id}")
        print(f"  • Execution ID: {execution.id}")
        print(f"  • Agents: {len(agents)}")
        print(f"  • Messages: 7")
        print()
        print(f"💡 To view messages via SSE stream:")
        print(f"   python -m backend.cli.stream_agent_messages \\")
        print(f"     --execution-id {execution.id}")
        print()


if __name__ == "__main__":
    asyncio.run(create_simple_demo())
