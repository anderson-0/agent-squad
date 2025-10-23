#!/usr/bin/env python3
"""
Apply Template CLI

Quick command-line tool for applying squad templates.

Usage:
    # List available templates
    python -m backend.cli.apply_template --list

    # Apply template to create new squad
    python -m backend.cli.apply_template \
        --user-email user@example.com \
        --template software-dev-squad \
        --squad-name "My Dev Team"

    # Apply template with details
    python -m backend.cli.apply_template \
        --user-email user@example.com \
        --template software-dev-squad \
        --squad-name "Alpha Squad" \
        --description "Main development team"
"""
import asyncio
import sys
from typing import Optional

import click
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.core.database import AsyncSessionLocal
from backend.models.user import User
from backend.models.squad_template import SquadTemplate
from backend.services.template_service import TemplateService
from backend.services.squad_service import SquadService


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email."""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def list_templates_async():
    """List all available templates."""
    async with AsyncSessionLocal() as db:
        templates = await TemplateService.list_templates(db)

        if not templates:
            click.echo("❌ No templates found.")
            click.echo("\nCreate templates by loading them from YAML files.")
            return

        click.echo("\n" + "=" * 80)
        click.echo("  📋 AVAILABLE SQUAD TEMPLATES".center(80))
        click.echo("=" * 80 + "\n")

        for template in templates:
            featured = "⭐ " if template.is_featured else "   "
            click.echo(f"{featured}{template.name}")
            click.echo(f"    Slug: {template.slug}")
            click.echo(f"    Category: {template.category}")
            click.echo(f"    Description: {template.description}")
            click.echo(f"    Used: {template.usage_count} times")

            # Show contents
            agents = template.template_definition.get('agents', [])
            rules = template.template_definition.get('routing_rules', [])
            click.echo(f"    Contains: {len(agents)} agents, {len(rules)} routing rules")

            # Show agent roles
            if agents:
                roles = [agent['role'] for agent in agents]
                click.echo(f"    Roles: {', '.join(roles)}")

            click.echo()

        click.echo("=" * 80)
        click.echo(f"\nTotal: {len(templates)} template(s)")
        click.echo("\n💡 Tip: Use --template <slug> to apply a template\n")


async def apply_template_async(
    user_email: str,
    template_slug: str,
    squad_name: str,
    description: Optional[str] = None
):
    """Apply a template to create a new squad."""
    async with AsyncSessionLocal() as db:
        # Get user
        user = await get_user_by_email(db, user_email)
        if not user:
            click.echo(f"❌ User not found: {user_email}", err=True)
            click.echo("\nPlease create a user first or use an existing email.", err=True)
            sys.exit(1)

        # Get template
        template = await TemplateService.get_template_by_slug(db, template_slug)
        if not template:
            click.echo(f"❌ Template not found: {template_slug}", err=True)
            click.echo("\nAvailable templates:", err=True)

            # Show available templates
            templates = await TemplateService.list_templates(db)
            for t in templates:
                click.echo(f"  • {t.slug} - {t.name}", err=True)

            sys.exit(1)

        click.echo("\n" + "=" * 80)
        click.echo("  🚀 APPLYING SQUAD TEMPLATE".center(80))
        click.echo("=" * 80 + "\n")

        click.echo(f"Template: {template.name}")
        click.echo(f"User: {user.email}")
        click.echo(f"Squad Name: {squad_name}")
        if description:
            click.echo(f"Description: {description}")
        click.echo()

        # Create squad
        click.echo("⏳ Creating squad...")
        squad = await SquadService.create_squad(
            db=db,
            user_id=user.id,
            name=squad_name,
            description=description or f"Squad created from {template.name} template"
        )
        click.echo(f"✓ Squad created: {squad.id}")

        # Apply template
        click.echo(f"\n⏳ Applying template '{template.name}'...")
        result = await TemplateService.apply_template(
            db=db,
            template_id=template.id,
            squad_id=squad.id,
            user_id=user.id
        )

        click.echo(f"✓ Created {result['agents_created']} agents")
        click.echo(f"✓ Created {result['rules_created']} routing rules")

        # Display results
        click.echo("\n" + "=" * 80)
        click.echo("  ✅ SQUAD CREATED SUCCESSFULLY".center(80))
        click.echo("=" * 80 + "\n")

        click.echo(f"Squad ID: {squad.id}")
        click.echo(f"Squad Name: {squad.name}")
        click.echo(f"Template: {template.name}")
        click.echo(f"Status: {squad.status}")

        click.echo("\n👥 Agents:")
        click.echo("-" * 80)
        for i, agent in enumerate(result['agents'], 1):
            specialization = f" ({agent['specialization']})" if agent['specialization'] else ""
            click.echo(f"{i}. {agent['role'].replace('_', ' ').title()}{specialization}")
            click.echo(f"   ID: {agent['id']}")
            click.echo(f"   LLM: {agent['llm_provider']}/{agent['llm_model']}")

        click.echo("\n🔄 Routing Configuration:")
        click.echo("-" * 80)
        click.echo(f"Total Routing Rules: {result['rules_created']}")

        # Group routing rules by asker role
        rules_by_asker = {}
        for rule in result['routing_rules']:
            asker = rule['asker_role']
            if asker not in rules_by_asker:
                rules_by_asker[asker] = []
            rules_by_asker[asker].append(rule)

        for asker_role in sorted(rules_by_asker.keys()):
            click.echo(f"\n{asker_role}:")
            rules = sorted(
                rules_by_asker[asker_role],
                key=lambda r: (r['question_type'], r['escalation_level'])
            )
            for rule in rules:
                q_type = rule['question_type']
                level = rule['escalation_level']
                responder = rule['responder_role']
                click.echo(f"  • {q_type} (level {level}) → {responder}")

        click.echo("\n" + "=" * 80)
        click.echo("\n📝 Next Steps:")
        click.echo(f"1. Create a task execution for your squad:")
        click.echo(f"   python -m backend.cli.run_demo_task --squad-id {squad.id}")
        click.echo(f"\n2. Test agent-to-agent communication:")
        click.echo(f"   python demo_hierarchical_conversations.py")
        click.echo(f"\n3. View your squad via API:")
        click.echo(f"   curl http://localhost:8000/api/v1/squads/{squad.id}")
        click.echo()


@click.command()
@click.option(
    "--list",
    "-l",
    is_flag=True,
    help="List all available templates"
)
@click.option(
    "--user-email",
    "-u",
    help="Email of the user who will own the squad"
)
@click.option(
    "--template",
    "-t",
    help="Template slug to apply (e.g., 'software-dev-squad')"
)
@click.option(
    "--squad-name",
    "-n",
    help="Name for the new squad"
)
@click.option(
    "--description",
    "-d",
    help="Description for the squad (optional)"
)
def main(list: bool, user_email: str, template: str, squad_name: str, description: str):
    """
    Apply squad templates quickly from the command line.

    Examples:
        # List templates
        python -m backend.cli.apply_template --list

        # Apply template
        python -m backend.cli.apply_template \\
            --user-email user@example.com \\
            --template software-dev-squad \\
            --squad-name "My Dev Team"
    """

    if list:
        # List templates
        asyncio.run(list_templates_async())
    elif user_email and template and squad_name:
        # Apply template
        asyncio.run(apply_template_async(user_email, template, squad_name, description))
    else:
        # Show help if required args missing
        click.echo("❌ Missing required arguments\n", err=True)
        click.echo("To list templates:", err=True)
        click.echo("  python -m backend.cli.apply_template --list\n", err=True)
        click.echo("To apply a template:", err=True)
        click.echo("  python -m backend.cli.apply_template \\", err=True)
        click.echo("      --user-email <email> \\", err=True)
        click.echo("      --template <slug> \\", err=True)
        click.echo("      --squad-name <name>\n", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
