#!/usr/bin/env python3
"""
Create Demo Squad CLI

Creates a demo squad with a few agents for testing agent-to-agent communication.

Usage:
    python -m backend.cli.create_demo_squad --user-email user@example.com
    python -m backend.cli.create_demo_squad --user-email user@example.com --squad-name "My Demo Squad"
"""
import asyncio
import sys
from typing import Optional
from uuid import UUID

import click
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from services.squad_service import SquadService
from services.agent_service import AgentService
from models.user import User
from sqlalchemy import select


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email."""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def create_demo_squad(
    db: AsyncSession,
    user_id: UUID,
    squad_name: str = "Demo Squad"
) -> tuple:
    """
    Create a demo squad with basic agents.

    Returns:
        Tuple of (squad, agents_list)
    """
    # Create squad
    squad = await SquadService.create_squad(
        db=db,
        user_id=user_id,
        name=squad_name,
        description="Demo squad for testing agent communication",
        config={
            "demo": True,
            "auto_communication": True
        }
    )

    # Create agents with different roles
    agents = []

    # 1. Project Manager
    pm = await AgentService.create_squad_member(
        db=db,
        squad_id=squad.id,
        role="project_manager",
        specialization=None,
        llm_provider="anthropic",
        llm_model="claude-3-5-sonnet-20241022",
        config={
            "temperature": 0.7,
            "max_tokens": 4000
        }
    )
    agents.append(pm)

    # 2. Backend Developer
    backend_dev = await AgentService.create_squad_member(
        db=db,
        squad_id=squad.id,
        role="backend_developer",
        specialization="python_fastapi",
        llm_provider="openai",
        llm_model="gpt-4",
        config={
            "temperature": 0.5,
            "max_tokens": 4000
        }
    )
    agents.append(backend_dev)

    # 3. Frontend Developer
    frontend_dev = await AgentService.create_squad_member(
        db=db,
        squad_id=squad.id,
        role="frontend_developer",
        specialization="react_nextjs",
        llm_provider="openai",
        llm_model="gpt-4",
        config={
            "temperature": 0.5,
            "max_tokens": 4000
        }
    )
    agents.append(frontend_dev)

    return squad, agents


@click.command()
@click.option(
    "--user-email",
    required=True,
    help="Email of the user who will own the squad"
)
@click.option(
    "--squad-name",
    default="Demo Squad",
    help="Name for the demo squad"
)
def main(user_email: str, squad_name: str):
    """Create a demo squad with agents for testing."""

    async def _create():
        async with AsyncSessionLocal() as db:
            # Get user
            user = await get_user_by_email(db, user_email)
            if not user:
                click.echo(f"❌ User not found: {user_email}", err=True)
                click.echo("\nPlease create a user first or use an existing email.", err=True)
                sys.exit(1)

            click.echo(f"Creating demo squad for user: {user.email}")
            click.echo(f"Squad name: {squad_name}\n")

            # Create squad and agents
            squad, agents = await create_demo_squad(db, user.id, squad_name)

            await db.commit()

            # Display results
            click.echo("✅ Demo squad created successfully!\n")
            click.echo("=" * 60)
            click.echo(f"Squad ID: {squad.id}")
            click.echo(f"Squad Name: {squad.name}")
            click.echo(f"Description: {squad.description}")
            click.echo("=" * 60)
            click.echo("\nAgents:")
            click.echo("-" * 60)

            for i, agent in enumerate(agents, 1):
                specialization = f" ({agent.specialization})" if agent.specialization else ""
                click.echo(f"{i}. {agent.role.replace('_', ' ').title()}{specialization}")
                click.echo(f"   ID: {agent.id}")
                click.echo(f"   LLM: {agent.llm_provider}/{agent.llm_model}")
                click.echo()

            click.echo("-" * 60)
            click.echo("\n📝 Next Steps:")
            click.echo("1. Start a demo task execution:")
            click.echo(f"   python -m backend.cli.run_demo_task --squad-id {squad.id}")
            click.echo("\n2. In another terminal, watch the messages:")
            click.echo(f"   python -m backend.cli.stream_agent_messages --squad-id {squad.id}")
            click.echo()

    asyncio.run(_create())


if __name__ == "__main__":
    main()
