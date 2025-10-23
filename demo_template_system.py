#!/usr/bin/env python3
"""
Demo: Template System

Shows the new template features:
1. Loading templates from YAML
2. Listing available templates
3. Applying template to create complete squad
4. Verifying squad setup (agents + routing rules)

Run:
    python demo_template_system.py
"""
import logging

# Hide SQL commands - must be before any SQLAlchemy imports
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

import asyncio
from uuid import uuid4
from sqlalchemy import select
from pathlib import Path
import yaml

from backend.core.database import AsyncSessionLocal
from backend.models import Squad, SquadMember, User
from backend.models.squad_template import SquadTemplate
from backend.models.routing_rule import RoutingRule
from backend.services.template_service import TemplateService
from backend.services.squad_service import SquadService


def print_header(title: str):
    """Print a section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


async def load_template_from_yaml():
    """Load Software Dev Squad template from YAML"""
    print_header("📦 Step 1: Load Template from YAML")

    template_file = Path("templates/software_dev_squad.yaml")

    with open(template_file) as f:
        data = yaml.safe_load(f)

    async with AsyncSessionLocal() as db:
        # Check if already exists
        template = await TemplateService.get_template_by_slug(db, data['slug'])

        if template:
            print(f"✓ Template already loaded: {template.name}")
            print(f"  ID: {template.id}")
            print(f"  Usage Count: {template.usage_count}")
            return template.id

        # Create new template
        template = await TemplateService.create_template(
            db=db,
            name=data['name'],
            slug=data['slug'],
            description=data['description'],
            category=data['category'],
            template_definition=data,
            is_featured=data.get('is_featured', False)
        )

        print(f"✓ Created new template: {template.name}")
        print(f"  ID: {template.id}")
        print(f"  Agents: {len(data['agents'])}")
        print(f"  Routing Rules: {len(data['routing_rules'])}")

        return template.id


async def list_available_templates():
    """List all available templates"""
    print_header("📋 Step 2: List Available Templates")

    async with AsyncSessionLocal() as db:
        # List all templates
        all_templates = await TemplateService.list_templates(db)

        print(f"Total Templates: {len(all_templates)}\n")

        for template in all_templates:
            print(f"• {template.name}")
            print(f"  Slug: {template.slug}")
            print(f"  Category: {template.category}")
            print(f"  Featured: {'⭐' if template.is_featured else '  '}")
            print(f"  Used: {template.usage_count} times")

            # Show what's in the template
            agents = template.template_definition.get('agents', [])
            rules = template.template_definition.get('routing_rules', [])
            print(f"  Contains: {len(agents)} agents, {len(rules)} routing rules")
            print()


async def apply_template_to_new_squad(template_id):
    """Apply template to create a new squad"""
    print_header("🚀 Step 3: Apply Template to Create Squad")

    async with AsyncSessionLocal() as db:
        # Get or create user
        stmt = select(User).limit(1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            print("❌ No users found. Please create a user first.")
            return None

        print(f"Using user: {user.email}")

        # Create new squad
        squad = await SquadService.create_squad(
            db=db,
            user_id=user.id,
            name="Demo Template Squad",
            description="Squad created from template for demo"
        )

        print(f"\n✓ Created squad: {squad.name}")
        print(f"  ID: {squad.id}")

        # Apply template
        print(f"\n⏳ Applying template to squad...")

        result = await TemplateService.apply_template(
            db=db,
            template_id=template_id,
            squad_id=squad.id,
            user_id=user.id
        )

        print(f"\n✅ Template Applied Successfully!")
        print(f"  Template: {result['template_name']}")
        print(f"  Agents Created: {result['agents_created']}")
        print(f"  Routing Rules: {result['rules_created']}")

        # Show created agents
        print(f"\n👥 Agents:")
        for agent in result['agents']:
            print(f"  • {agent['role']} ({agent['specialization']})")
            print(f"    LLM: {agent['llm_provider']}/{agent['llm_model']}")

        return squad.id


async def verify_squad_setup(squad_id):
    """Verify the squad was set up correctly"""
    print_header("✅ Step 4: Verify Squad Setup")

    async with AsyncSessionLocal() as db:
        # Get squad
        stmt = select(Squad).where(Squad.id == squad_id)
        result = await db.execute(stmt)
        squad = result.scalar_one_or_none()

        print(f"Squad: {squad.name}")
        print(f"Status: {squad.status}\n")

        # Get agents
        stmt = select(SquadMember).where(SquadMember.squad_id == squad_id)
        result = await db.execute(stmt)
        members = result.scalars().all()

        print(f"Agents ({len(members)}):")
        role_counts = {}
        for member in members:
            role_counts[member.role] = role_counts.get(member.role, 0) + 1
            print(f"  ✓ {member.role} ({member.specialization})")
            print(f"    Provider: {member.llm_provider}, Model: {member.llm_model}")
            print(f"    Active: {member.is_active}")

        # Get routing rules
        stmt = select(RoutingRule).where(RoutingRule.squad_id == squad_id)
        result = await db.execute(stmt)
        rules = result.scalars().all()

        print(f"\nRouting Rules ({len(rules)}):")

        # Group by asker role
        rules_by_asker = {}
        for rule in rules:
            if rule.asker_role not in rules_by_asker:
                rules_by_asker[rule.asker_role] = []
            rules_by_asker[rule.asker_role].append(rule)

        for asker_role, asker_rules in sorted(rules_by_asker.items()):
            print(f"\n  {asker_role}:")
            for rule in sorted(asker_rules, key=lambda r: (r.question_type, r.escalation_level)):
                print(f"    • {rule.question_type} (level {rule.escalation_level}) → {rule.responder_role}")

        # Verify escalation hierarchy
        print(f"\n🔗 Escalation Hierarchy Check:")

        # Check backend_developer escalation path
        backend_rules = [r for r in rules if r.asker_role == 'backend_developer' and r.question_type == 'implementation']
        backend_rules.sort(key=lambda r: r.escalation_level)

        if len(backend_rules) >= 3:
            print(f"  Backend Developer (implementation):")
            for rule in backend_rules[:3]:
                print(f"    Level {rule.escalation_level}: → {rule.responder_role}")
            print(f"  ✓ Full escalation chain configured!")

        # Summary
        print(f"\n📊 Summary:")
        print(f"  Squad ID: {squad_id}")
        print(f"  Total Agents: {len(members)}")
        print(f"  Total Rules: {len(rules)}")
        print(f"  Unique Roles: {len(role_counts)}")
        print(f"  Status: {'✅ Ready for Use' if squad.status == 'active' else '❌ Not Active'}")


async def test_template_customization(template_id):
    """Test applying template with customizations"""
    print_header("🎨 Step 5: Test Template Customization")

    async with AsyncSessionLocal() as db:
        # Get user
        stmt = select(User).limit(1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        # Create squad
        squad = await SquadService.create_squad(
            db=db,
            user_id=user.id,
            name="Custom Template Squad",
            description="Squad with customized template"
        )

        print(f"Created squad: {squad.name}")

        # Apply with customization (override some agent LLMs)
        customization = {
            "agents": [
                {
                    "role": "project_manager",
                    "specialization": "agile",
                    "llm_provider": "anthropic",
                    "llm_model": "claude-3-5-sonnet-20241022"
                },
                {
                    "role": "backend_developer",
                    "specialization": "python_fastapi",
                    "llm_provider": "anthropic",  # Override to Anthropic
                    "llm_model": "claude-3-5-sonnet-20241022"
                },
                {
                    "role": "tech_lead",
                    "specialization": "default",
                    "llm_provider": "anthropic",
                    "llm_model": "claude-3-5-sonnet-20241022"
                }
            ]
        }

        print(f"\nApplying template with customization:")
        print(f"  Override backend_developer to use Anthropic/Claude")
        print(f"  Only create 3 agents instead of 6")

        result = await TemplateService.apply_template(
            db=db,
            template_id=template_id,
            squad_id=squad.id,
            user_id=user.id,
            customization=customization
        )

        print(f"\n✅ Customized template applied!")
        print(f"  Agents created: {result['agents_created']}")

        for agent in result['agents']:
            print(f"  • {agent['role']}: {agent['llm_provider']}/{agent['llm_model']}")


async def main():
    """Run all demos"""
    print("\n" + "🤖" * 40)
    print("  TEMPLATE SYSTEM DEMO".center(80))
    print("🤖" * 40)

    try:
        # Step 1: Load template
        template_id = await load_template_from_yaml()

        # Step 2: List templates
        await list_available_templates()

        # Step 3: Apply template
        squad_id = await apply_template_to_new_squad(template_id)

        if squad_id:
            # Step 4: Verify setup
            await verify_squad_setup(squad_id)

            # Step 5: Test customization
            await test_template_customization(template_id)

        print_header("✅ DEMO COMPLETE")
        print("Template system is working perfectly!")
        print("\nNext Steps:")
        print("  1. Run: python demo_template_squad_conversations.py")
        print("  2. Test API endpoints with curl or Postman")
        print("  3. Create additional templates")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
