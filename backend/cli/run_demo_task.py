#!/usr/bin/env python3
"""
Run Demo Task CLI

Simulates a task execution with agents communicating with each other.
This is a simplified demo to showcase agent-to-agent communication via SSE.

Usage:
    python -m backend.cli.run_demo_task --squad-id <squad-uuid>
    python -m backend.cli.run_demo_task --squad-id <squad-uuid> --task-description "Build a login page"
"""
import asyncio
import sys
from typing import List
from uuid import UUID, uuid4
from datetime import datetime

import click
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import AsyncSessionLocal
from services.squad_service import SquadService
from services.agent_service import AgentService
from services.task_execution_service import TaskExecutionService
from agents.communication.message_bus import get_message_bus
from models.squad import SquadMember
from models.project import Task


async def create_demo_task(
    db: AsyncSession,
    squad_id: UUID,
    task_description: str
) -> Task:
    """Create a simple demo task."""
    from backend.models.project import Task, Project

    # First, get or create a demo project
    result = await db.execute(
        select(Project).where(Project.name == "Demo Project")
    )
    project = result.scalar_one_or_none()

    if not project:
        # Get squad to get user_id
        squad = await SquadService.get_squad(db, squad_id)
        project = Project(
            id=uuid4(),
            name="Demo Project",
            description="Demo project for testing",
            owner_id=squad.owner_id,
            status="active"
        )
        db.add(project)
        await db.flush()

    # Create task
    task = Task(
        id=uuid4(),
        project_id=project.id,
        title="Demo Task",
        description=task_description,
        status="pending",
        priority="medium",
        acceptance_criteria=[
            "Implementation complete",
            "Code reviewed",
            "Tests passing"
        ]
    )
    db.add(task)
    await db.flush()

    return task


async def simulate_agent_communication(
    db: AsyncSession,
    execution_id: UUID,
    agents: List[SquadMember],
    task_description: str
):
    """
    Simulate agents communicating about a task.

    This is a simplified demo - agents don't actually call LLMs,
    they just send pre-scripted messages to showcase the communication flow.
    """
    message_bus = get_message_bus()

    # Find agents by role
    pm = next((a for a in agents if a.role == "project_manager"), None)
    backend_dev = next((a for a in agents if a.role == "backend_developer"), None)
    frontend_dev = next((a for a in agents if a.role == "frontend_developer"), None)

    if not all([pm, backend_dev, frontend_dev]):
        raise ValueError("Demo squad must have PM, Backend Dev, and Frontend Dev")

    click.echo("🚀 Starting demo task execution...")
    click.echo(f"Task: {task_description}\n")

    # Scenario: PM assigns tasks, devs ask questions, work collaborates

    # 1. PM broadcasts standup
    await asyncio.sleep(1)
    click.echo("📢 PM: Starting daily standup...")
    await message_bus.send_message(
        sender_id=pm.id,
        recipient_id=None,  # Broadcast
        content=f"Good morning team! Today we're tackling: {task_description}",
        message_type="standup",
        task_execution_id=execution_id,
        metadata={"thread_id": "standup-1"},
        db=db
    )

    # 2. PM assigns task to backend dev
    await asyncio.sleep(2)
    click.echo("📝 PM → Backend Dev: Assigning backend work...")
    await message_bus.send_message(
        sender_id=pm.id,
        recipient_id=backend_dev.id,
        content="Please implement the API endpoints for this feature. We'll need authentication, data validation, and error handling.",
        message_type="task_assignment",
        task_execution_id=execution_id,
        metadata={"priority": "high", "estimated_hours": 8, "thread_id": "backend-work"},
        db=db
    )

    # 3. Backend dev acknowledges
    await asyncio.sleep(1.5)
    click.echo("✅ Backend Dev → PM: Acknowledged task...")
    await message_bus.send_message(
        sender_id=backend_dev.id,
        recipient_id=pm.id,
        content="Understood! I'll start with the data models and then build out the endpoints. Should be ready for review by EOD.",
        message_type="acknowledgment",
        task_execution_id=execution_id,
        metadata={"thread_id": "backend-work"},
        db=db
    )

    # 4. PM assigns task to frontend dev
    await asyncio.sleep(2)
    click.echo("📝 PM → Frontend Dev: Assigning UI work...")
    await message_bus.send_message(
        sender_id=pm.id,
        recipient_id=frontend_dev.id,
        content="Please create the user interface components. We need a clean, responsive design that works on mobile and desktop.",
        message_type="task_assignment",
        task_execution_id=execution_id,
        metadata={"priority": "high", "estimated_hours": 6, "thread_id": "frontend-work"},
        db=db
    )

    # 5. Frontend dev has a question
    await asyncio.sleep(1.5)
    click.echo("❓ Frontend Dev → Backend Dev: Asking question...")
    await message_bus.send_message(
        sender_id=frontend_dev.id,
        recipient_id=backend_dev.id,
        content="Hey! What will the API response format be? I want to make sure I handle the data correctly on the frontend.",
        message_type="question",
        task_execution_id=execution_id,
        metadata={"thread_id": "api-discussion"},
        db=db
    )

    # 6. Backend dev answers
    await asyncio.sleep(2)
    click.echo("💬 Backend Dev → Frontend Dev: Answering...")
    await message_bus.send_message(
        sender_id=backend_dev.id,
        recipient_id=frontend_dev.id,
        content="Good question! The API will return JSON with this structure: {data: {...}, meta: {count, page}, errors: [...]}. I'll document the full schema in Swagger.",
        message_type="answer",
        task_execution_id=execution_id,
        metadata={"thread_id": "api-discussion"},
        db=db
    )

    # 7. Frontend dev acknowledges
    await asyncio.sleep(1)
    click.echo("👍 Frontend Dev → Backend Dev: Thanks!")
    await message_bus.send_message(
        sender_id=frontend_dev.id,
        recipient_id=backend_dev.id,
        content="Perfect, that helps a lot! I'll start building the components now.",
        message_type="acknowledgment",
        task_execution_id=execution_id,
        metadata={"thread_id": "api-discussion"},
        db=db
    )

    # 8. Backend dev sends status update
    await asyncio.sleep(3)
    click.echo("📊 Backend Dev → PM: Status update...")
    await message_bus.send_message(
        sender_id=backend_dev.id,
        recipient_id=pm.id,
        content="Status update: Data models complete, 2 out of 5 endpoints implemented. On track for EOD delivery.",
        message_type="status_update",
        task_execution_id=execution_id,
        metadata={"progress": 40, "thread_id": "backend-work"},
        db=db
    )

    # 9. Frontend dev sends status update
    await asyncio.sleep(2)
    click.echo("📊 Frontend Dev → PM: Status update...")
    await message_bus.send_message(
        sender_id=frontend_dev.id,
        recipient_id=pm.id,
        content="UI components are coming along nicely. Created the main layout and starting on form validation.",
        message_type="status_update",
        task_execution_id=execution_id,
        metadata={"progress": 30, "thread_id": "frontend-work"},
        db=db
    )

    # 10. Backend dev requests code review
    await asyncio.sleep(3)
    click.echo("👀 Backend Dev → PM: Requesting code review...")
    await message_bus.send_message(
        sender_id=backend_dev.id,
        recipient_id=pm.id,
        content="Backend implementation complete! PR #123 is ready for review. All tests passing, coverage at 95%.",
        message_type="code_review_request",
        task_execution_id=execution_id,
        metadata={"pr_url": "github.com/demo/pr/123", "thread_id": "backend-work"},
        db=db
    )

    # 11. PM approves
    await asyncio.sleep(2)
    click.echo("✅ PM → Backend Dev: Code approved!")
    await message_bus.send_message(
        sender_id=pm.id,
        recipient_id=backend_dev.id,
        content="Excellent work! Code looks clean, tests are comprehensive. Approved and merged!",
        message_type="code_review_feedback",
        task_execution_id=execution_id,
        metadata={"approved": True, "thread_id": "backend-work"},
        db=db
    )

    # 12. Frontend dev completes work
    await asyncio.sleep(2)
    click.echo("🎉 Frontend Dev → PM: Work complete!")
    await message_bus.send_message(
        sender_id=frontend_dev.id,
        recipient_id=pm.id,
        content="Frontend is done! All components implemented, responsive on all devices. PR #124 ready for review.",
        message_type="completion_notification",
        task_execution_id=execution_id,
        metadata={"pr_url": "github.com/demo/pr/124", "thread_id": "frontend-work"},
        db=db
    )

    # 13. PM wraps up
    await asyncio.sleep(1.5)
    click.echo("🎊 PM → All: Task complete!")
    await message_bus.send_message(
        sender_id=pm.id,
        recipient_id=None,  # Broadcast
        content="Awesome teamwork everyone! Task completed successfully. Backend and frontend are merged and deployed. Great collaboration! 🚀",
        message_type="standup",
        task_execution_id=execution_id,
        metadata={"celebration": True},
        db=db
    )

    click.echo("\n✅ Demo task execution completed!")
    click.echo(f"Total messages: 13")
    click.echo(f"\n💡 Tip: Check the SSE stream to see these messages in real-time!")


@click.command()
@click.option(
    "--squad-id",
    required=True,
    type=str,
    help="UUID of the squad to execute the task"
)
@click.option(
    "--task-description",
    default="Build a user authentication system with login and registration",
    help="Description of the task to simulate"
)
def main(squad_id: str, task_description: str):
    """Run a demo task execution with simulated agent communication."""

    async def _run():
        async with AsyncSessionLocal() as db:
            try:
                squad_uuid = UUID(squad_id)
            except ValueError:
                click.echo(f"❌ Invalid squad ID format: {squad_id}", err=True)
                sys.exit(1)

            # Verify squad exists
            squad = await SquadService.get_squad(db, squad_uuid)
            if not squad:
                click.echo(f"❌ Squad not found: {squad_id}", err=True)
                sys.exit(1)

            # Get squad members
            agents = await AgentService.get_squad_members(db, squad_uuid, active_only=True)
            if len(agents) < 3:
                click.echo(f"❌ Squad needs at least 3 agents (found {len(agents)})", err=True)
                click.echo("Create a demo squad with: python -m backend.cli.create_demo_squad", err=True)
                sys.exit(1)

            click.echo(f"Squad: {squad.name}")
            click.echo(f"Agents: {len(agents)}")
            click.echo()

            # Create demo task
            task = await create_demo_task(db, squad_uuid, task_description)

            # Start execution
            execution = await TaskExecutionService.start_task_execution(
                db=db,
                task_id=task.id,
                squad_id=squad_uuid,
                execution_metadata={
                    "demo": True,
                    "task_description": task_description
                }
            )

            await db.commit()

            click.echo(f"Execution ID: {execution.id}")
            click.echo()

            # Run the demo communication
            await simulate_agent_communication(
                db=db,
                execution_id=execution.id,
                agents=agents,
                task_description=task_description
            )

            # Mark execution as completed
            await TaskExecutionService.complete_execution(
                db=db,
                execution_id=execution.id,
                result={
                    "status": "success",
                    "messages_sent": 13,
                    "demo": True
                }
            )

            await db.commit()

            click.echo(f"\n📺 To watch live messages, run:")
            click.echo(f"python -m backend.cli.stream_agent_messages --execution-id {execution.id}")

    asyncio.run(_run())


if __name__ == "__main__":
    main()
