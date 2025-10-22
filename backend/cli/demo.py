#!/usr/bin/env python3
"""
Complete Agent Communication Demo

This script runs a complete end-to-end demonstration:
1. Creates a test user (if needed)
2. Creates a demo squad with agents
3. Runs a simulated task with agent communication
4. Shows you how to watch messages in real-time

Usage:
    python -m backend.cli.demo
    python -m backend.cli.demo --user-email your@email.com
"""
import asyncio
import sys
from uuid import uuid4

import click
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import AsyncSessionLocal
from models.user import User
from cli.create_demo_squad import create_demo_squad
from cli.run_demo_task import create_demo_task, simulate_agent_communication
from services.task_execution_service import TaskExecutionService


async def get_or_create_test_user(db: AsyncSession, email: str) -> User:
    """Get existing user or create a test user."""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if not user:
        click.echo(f"Creating test user: {email}")
        user = User(
            id=uuid4(),
            email=email,
            hashed_password="demo_password_hash",  # Not used in demo
            full_name="Demo User",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        await db.flush()
        click.echo("✅ Test user created\n")
    else:
        click.echo(f"✅ Using existing user: {email}\n")

    return user


@click.command()
@click.option(
    "--user-email",
    default="demo@agentsquad.dev",
    help="Email for the demo user"
)
@click.option(
    "--task-description",
    default="Build a user authentication system with login and registration",
    help="Description of the task to simulate"
)
def main(user_email: str, task_description: str):
    """
    Run a complete agent communication demo.

    This creates a squad, runs a simulated task with agents communicating,
    and shows you how to watch the messages in real-time.
    """

    async def _run_demo():
        click.echo("=" * 70)
        click.echo("🤖  AGENT SQUAD - Live Communication Demo".center(70))
        click.echo("=" * 70)
        click.echo()

        async with AsyncSessionLocal() as db:
            # Step 1: Get or create user
            click.echo("Step 1: Setting up user...")
            user = await get_or_create_test_user(db, user_email)
            await db.commit()

            # Step 2: Create squad
            click.echo("Step 2: Creating demo squad...")
            squad, agents = await create_demo_squad(db, user.id, "Live Demo Squad")
            await db.commit()

            click.echo(f"✅ Squad created: {squad.name}")
            click.echo(f"   - {len(agents)} agents ready\n")

            # Step 3: Create task
            click.echo("Step 3: Creating demo task...")
            task = await create_demo_task(db, squad.id, task_description)
            execution = await TaskExecutionService.start_task_execution(
                db=db,
                task_id=task.id,
                squad_id=squad.id,
                execution_metadata={"demo": True, "live": True}
            )
            await db.commit()

            click.echo(f"✅ Task created: {task.title}")
            click.echo(f"   Execution ID: {execution.id}\n")

            # Step 4: Show how to watch messages
            click.echo("=" * 70)
            click.echo("📺  TO WATCH MESSAGES IN REAL-TIME:".center(70))
            click.echo("=" * 70)
            click.echo()
            click.echo("Open a NEW terminal window and run:")
            click.echo()
            click.echo(f"  python -m backend.cli.stream_agent_messages \\")
            click.echo(f"    --execution-id {execution.id}")
            click.echo()
            click.echo("=" * 70)
            click.echo()

            # Give user time to start the stream
            click.echo("⏳ Waiting 10 seconds for you to start the message stream...")
            click.echo("   (Press Ctrl+C to skip)")
            try:
                for i in range(10, 0, -1):
                    click.echo(f"   Starting in {i}...", nl=False)
                    await asyncio.sleep(1)
                    click.echo("\r", nl=False)
            except KeyboardInterrupt:
                click.echo("\n   Skipped waiting period")

            click.echo("\n")
            click.echo("=" * 70)
            click.echo("🚀  STARTING AGENT COMMUNICATION".center(70))
            click.echo("=" * 70)
            click.echo()

            # Step 5: Simulate agent communication
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
                result={"status": "success", "demo": True}
            )
            await db.commit()

            click.echo()
            click.echo("=" * 70)
            click.echo("✅  DEMO COMPLETED".center(70))
            click.echo("=" * 70)
            click.echo()
            click.echo("📝 What just happened:")
            click.echo("   • 3 AI agents collaborated on a task")
            click.echo("   • 13 messages were exchanged")
            click.echo("   • All messages were broadcast via SSE")
            click.echo()
            click.echo("💡 Next steps:")
            click.echo("   • Review the messages in the stream terminal")
            click.echo("   • Try creating your own squad with different agents")
            click.echo("   • Modify the demo task description")
            click.echo()
            click.echo("📚 Learn more:")
            click.echo("   • See backend/cli/README.md for CLI documentation")
            click.echo("   • See AGENT_STREAMING_IMPLEMENTATION_PLAN.md for architecture")
            click.echo()

    try:
        asyncio.run(_run_demo())
    except KeyboardInterrupt:
        click.echo("\n\n❌ Demo cancelled by user")
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n\n❌ Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
