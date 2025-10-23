#!/usr/bin/env python3
"""
Quick Template Application Script

Loads a template from YAML and applies it to create a complete squad.

Usage:
    python apply_template_quick.py
"""
import asyncio
import yaml
from pathlib import Path
from uuid import uuid4
from sqlalchemy import select

from backend.core.database import AsyncSessionLocal
from backend.models import SquadTemplate, User
from backend.services.squad_service import SquadService
from backend.services.agent_service import AgentService
from backend.models.routing_rule import RoutingRule


async def load_template_to_db():
    """Load template from YAML file into database"""
    template_file = Path("templates/software_dev_squad.yaml")

    with open(template_file) as f:
        data = yaml.safe_load(f)

    async with AsyncSessionLocal() as db:
        # Check if already exists
        stmt = select(SquadTemplate).where(SquadTemplate.slug == data['slug'])
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            print(f"✓ Template already exists: {data['name']}")
            return existing.id

        # Create template
        template = SquadTemplate(
            id=uuid4(),
            name=data['name'],
            slug=data['slug'],
            description=data['description'],
            category=data['category'],
            is_active=True,
            is_featured=data.get('is_featured', False),
            template_definition=data,
            usage_count=0,
            avg_rating=0.0
        )

        db.add(template)
        await db.commit()
        await db.refresh(template)

        print(f"✓ Created template: {data['name']}")
        return template.id


async def apply_template(template_id, squad_name="My Dev Squad"):
    """Apply template to create a squad"""
    async with AsyncSessionLocal() as db:
        # Get template
        stmt = select(SquadTemplate).where(SquadTemplate.id == template_id)
        result = await db.execute(stmt)
        template = result.scalar_one_or_none()

        if not template:
            print(f"✗ Template not found")
            return

        # Get or create user
        stmt = select(User).limit(1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            print("✗ No users found. Create a user first.")
            return

        print(f"\n🚀 Applying template: {template.name}")
        print(f"   Creating squad: {squad_name}\n")

        # Create squad
        squad = await SquadService.create_squad(
            db=db,
            user_id=user.id,
            name=squad_name,
            description=f"Squad created from template: {template.name}"
        )

        print(f"✓ Squad created: {squad.id}\n")

        # Get template definition
        template_def = template.template_definition

        # Create agents
        created_agents = []
        for agent_def in template_def.get('agents', []):
            agent = await AgentService.create_squad_member(
                db=db,
                squad_id=squad.id,
                role=agent_def['role'],
                specialization=agent_def.get('specialization'),
                llm_provider=agent_def.get('llm_provider', 'openai'),
                llm_model=agent_def.get('llm_model', 'gpt-4')
            )
            created_agents.append(agent)
            print(f"  ✓ Created {agent.role} ({agent_def.get('specialization', 'default')})")

        await db.flush()

        # Create routing rules
        created_rules = []
        for rule_def in template_def.get('routing_rules', []):
            rule = RoutingRule(
                id=uuid4(),
                squad_id=squad.id,
                asker_role=rule_def['asker_role'],
                question_type=rule_def['question_type'],
                escalation_level=rule_def['escalation_level'],
                responder_role=rule_def['responder_role'],
                is_active=True,
                priority=rule_def.get('priority', 10),
                rule_metadata={}
            )
            db.add(rule)
            created_rules.append(rule)

        await db.commit()

        print(f"\n✓ Created {len(created_rules)} routing rules")
        print(f"\n🎉 Squad ready! ID: {squad.id}")
        print(f"\n📋 Squad has:")
        print(f"   - {len(created_agents)} AI agents")
        print(f"   - {len(created_rules)} routing rules")
        print(f"   - Full escalation hierarchy")

        # Update template usage
        template.usage_count += 1
        await db.commit()

        return squad.id


async def main():
    print("=" * 80)
    print("🤖 Software Development Squad Template - Quick Setup".center(80))
    print("=" * 80)
    print()

    # Step 1: Load template
    print("Step 1: Loading template from YAML...")
    template_id = await load_template_to_db()

    # Step 2: Apply template
    print("\nStep 2: Applying template to create squad...")
    squad_id = await apply_template(template_id, "Software Dev Squad Demo")

    print("\n" + "=" * 80)
    print("✅ COMPLETE".center(80))
    print("=" * 80)
    print("\nYour squad is ready to use!")
    print("\nNext steps:")
    print("  1. Run: python demo_hierarchical_conversations.py")
    print("  2. Watch agents collaborate in real-time")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nCancelled by user\n")
    except Exception as e:
        print(f"\n✗ Error: {e}\n")
        import traceback
        traceback.print_exc()
