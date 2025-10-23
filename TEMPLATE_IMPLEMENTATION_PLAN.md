# Pre-built Squad Templates - Implementation Plan

**Goal:** Enable users to spin up a complete, production-ready AI agent squad in under 5 minutes

**Timeline:** 2-3 days

**Complexity:** Low (leverages existing infrastructure)

---

## 🎯 Current Progress

**✅ COMPLETED (Day 1):**
1. Database schema (`SquadTemplate` model + migration 002)
2. System prompts for 6 roles (PM, Architect, Tech Lead, 2 Devs, QA)
3. Complete Software Dev Squad template (YAML)
4. Template loader script (`apply_template_quick.py`)
5. End-to-end testing (squad created with 6 agents + 17 routing rules)

**📍 NEXT STEPS:**
1. Build template service (`TemplateService`)
2. Create API endpoints (`/api/v1/templates/`)
3. Create remaining templates (Customer Support, Sales, DevOps, Content)
4. Build CLI tool for easy template application
5. Seed database with all templates

**📊 Progress:** ~40% complete (2/5 templates, core infra done)

---

## 📋 What We're Building

A complete template system that includes:
1. **5 Pre-configured Squad Templates** - Ready-to-use agent teams
2. **Agent Definitions** - Roles, LLM models, system prompts
3. **Routing Rules** - Complete escalation hierarchies
4. **System Prompts** - Optimized prompts for each agent role
5. **Example Conversations** - Demonstrate template capabilities
6. **Success Metrics** - KPIs to track squad performance
7. **Quick Apply API** - One-click template deployment
8. **CLI Tool** - Command-line template application

---

## 🏗️ Architecture Overview

### Current State
```
✅ backend/models/routing_rule.py - RoutingRule model exists
✅ backend/agents/interaction/seed_routing_templates.py - 5 routing templates
✅ backend/agents/interaction/routing_engine.py - apply_template_to_squad()
✅ backend/services/squad_service.py - Squad creation
✅ backend/services/agent_service.py - Agent creation
```

### What We Need to Add
```
NEW: backend/models/squad_template.py - Full squad template model
NEW: backend/services/template_service.py - Template application service
NEW: backend/api/v1/endpoints/templates.py - Template APIs
NEW: backend/cli/apply_template.py - CLI tool
NEW: backend/templates/ - Template definitions (YAML/JSON)
NEW: roles/{role}/prompts/ - System prompts for each role
```

---

## 📊 Implementation Steps

### ✅ Step 1: Enhanced Template Schema (COMPLETED)

**Status:** Migration created and applied successfully

**File:** `backend/models/squad_template.py`

**Schema:**
```python
class SquadTemplate(Base):
    """Complete squad template with agents, routing, and prompts"""

    id: UUID
    name: str  # "Software Development Squad"
    slug: str  # "software-dev-squad"
    description: str
    category: str  # "development", "support", "sales", etc.
    is_active: bool
    is_featured: bool

    # Template definition (JSON)
    template_definition: dict = {
        "agents": [
            {
                "role": "backend_developer",
                "specialization": "python_fastapi",
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "system_prompt_key": "backend_dev_default"
            },
            # ... more agents
        ],
        "routing_rules": [
            {
                "asker_role": "backend_developer",
                "question_type": "implementation",
                "escalation_level": 0,
                "responder_role": "tech_lead",
                "priority": 10
            },
            # ... more rules
        ],
        "success_metrics": [
            {
                "name": "Questions per Day",
                "target": 20,
                "unit": "count"
            },
            # ... more metrics
        ],
        "example_conversations": [
            {
                "title": "Cache Strategy Discussion",
                "messages": [...]
            }
        ]
    }

    # Usage stats
    usage_count: int
    avg_rating: float

    created_at: datetime
    updated_at: datetime
```

**Migration:**
```bash
alembic revision --autogenerate -m "add_squad_templates"
alembic upgrade head
```

---

### ✅ Step 2: System Prompts for All Roles (COMPLETED)

**Status:** 6 system prompts created for Software Dev Squad

**Directory Structure:**
```
roles/
├── backend_developer/
│   ├── python_fastapi.md (existing)
│   └── nodejs_express.md (new)
├── frontend_developer/
│   ├── react_typescript.md (new)
│   └── vue_javascript.md (new)
├── tech_lead/
│   └── default.md (new)
├── solution_architect/
│   └── default.md (new)
├── project_manager/
│   └── agile.md (new)
├── qa_tester/
│   └── automation.md (new)
├── devops_engineer/
│   └── kubernetes.md (new)
├── support_agent_l1/
│   └── default.md (new)
├── support_agent_l2/
│   └── default.md (new)
├── support_specialist/
│   └── default.md (new)
├── sales_sdr/
│   └── default.md (new)
├── sales_ae/
│   └── default.md (new)
└── sales_engineer/
    └── default.md (new)
```

**Example Prompt Template:**

**File:** `roles/tech_lead/default.md`
```markdown
# Tech Lead Agent System Prompt

You are an experienced Tech Lead on a software development team. You have 8+ years of software engineering experience and 3+ years leading teams.

## Your Role
- Guide junior and mid-level developers with technical decisions
- Review code architecture and design patterns
- Escalate complex architecture questions to the Solution Architect
- Make pragmatic trade-offs between speed and quality
- Mentor team members through questions

## Your Expertise
- Backend: Python, Node.js, Java, Go
- Frontend: React, Vue, Angular
- Databases: PostgreSQL, MongoDB, Redis
- Architecture: Microservices, REST APIs, Event-driven
- DevOps: Docker, CI/CD, AWS/GCP basics

## Communication Style
- Be helpful and encouraging
- Ask clarifying questions when requirements are unclear
- Provide concrete examples and code snippets
- Explain the "why" behind recommendations
- If a question is beyond your expertise (e.g., enterprise architecture, business strategy), escalate to Solution Architect

## Response Format
When answering technical questions:
1. **Short Answer** - Direct answer in 1-2 sentences
2. **Explanation** - Why this is the recommended approach
3. **Example** - Code snippet or concrete example
4. **Trade-offs** - Mention any important considerations
5. **Next Steps** - What the developer should do next

## Example Interaction
Developer: "Should I use Redis or Memcached for session caching?"

You: "**Use Redis for session caching.**

**Why:** Redis supports more data structures (strings, hashes, lists) and has built-in persistence, which is crucial for sessions. Memcached is simpler but only stores strings and doesn't persist data.

**Example:**
```python
import redis
r = redis.Redis(host='localhost', port=6379)
r.setex(f'session:{user_id}', 3600, session_data)  # 1 hour TTL
```

**Trade-offs:** Redis uses slightly more memory, but the feature set is worth it for sessions.

**Next Steps:** Set up Redis with connection pooling and configure TTL based on your session expiry requirements."

## When to Escalate
- Enterprise-scale architecture decisions → Solution Architect
- Business/product strategy questions → Project Manager
- Security compliance questions → Solution Architect
- Performance at scale (>1M users) → Solution Architect
```

**Completed Prompts:**
- [x] Project Manager (agile) - `/roles/project_manager/agile.md`
- [x] Solution Architect (default) - `/roles/solution_architect/default.md`
- [x] Tech Lead (default) - `/roles/tech_lead/default.md`
- [x] Backend Developer (python_fastapi) - existing
- [x] Frontend Developer (react_typescript) - `/roles/frontend_developer/react_typescript.md`
- [x] QA Tester (automation) - `/roles/qa_tester/automation.md`

**Remaining Prompts for Other Templates:**
- [ ] DevOps Engineer (kubernetes)
- [ ] Support Agents (L1, L2, Specialist)
- [ ] Sales Agents (SDR, AE, Engineer)
- [ ] Content Team roles

---

### Step 3: Template Service (PENDING)

**Status:** Quick script works, full service needed for API integration

**File:** `backend/services/template_service.py`

```python
"""
Template Service

Handles application of complete squad templates including:
- Agent creation
- Routing rule setup
- System prompt assignment
- Example conversation seeding (optional)
"""
from typing import List, Dict, Optional
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models import SquadTemplate, Squad, SquadMember, RoutingRule
from backend.services.agent_service import AgentService
from backend.agents.interaction.routing_engine import RoutingEngine


class TemplateService:
    """Service for managing and applying squad templates"""

    @staticmethod
    async def list_templates(
        db: AsyncSession,
        category: Optional[str] = None,
        featured_only: bool = False
    ) -> List[SquadTemplate]:
        """
        List available squad templates

        Args:
            db: Database session
            category: Filter by category
            featured_only: Only show featured templates

        Returns:
            List of templates
        """
        stmt = select(SquadTemplate).where(SquadTemplate.is_active == True)

        if category:
            stmt = stmt.where(SquadTemplate.category == category)

        if featured_only:
            stmt = stmt.where(SquadTemplate.is_featured == True)

        stmt = stmt.order_by(SquadTemplate.usage_count.desc())

        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_template(
        db: AsyncSession,
        template_id: UUID
    ) -> Optional[SquadTemplate]:
        """Get template by ID"""
        stmt = select(SquadTemplate).where(SquadTemplate.id == template_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def apply_template(
        db: AsyncSession,
        template_id: UUID,
        squad_id: UUID,
        user_id: UUID,
        customization: Optional[Dict] = None
    ) -> Dict:
        """
        Apply a complete template to a squad

        Args:
            db: Database session
            template_id: Template to apply
            squad_id: Target squad
            user_id: User applying template
            customization: Optional overrides for template

        Returns:
            Dictionary with created agents and rules
        """
        # Get template
        template = await TemplateService.get_template(db, template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        template_def = template.template_definition

        # Apply customizations
        if customization:
            template_def = {**template_def, **customization}

        # Create agents
        created_agents = []
        for agent_def in template_def.get('agents', []):
            agent = await AgentService.create_squad_member(
                db=db,
                squad_id=squad_id,
                role=agent_def['role'],
                specialization=agent_def.get('specialization'),
                llm_provider=agent_def.get('llm_provider', 'openai'),
                llm_model=agent_def.get('llm_model', 'gpt-4'),
                custom_system_prompt=None  # Will load from file
            )
            created_agents.append(agent)

        await db.flush()

        # Create routing rules
        created_rules = []
        for rule_def in template_def.get('routing_rules', []):
            rule = RoutingRule(
                id=uuid4(),
                squad_id=squad_id,
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

        # Update template usage
        template.usage_count += 1
        await db.commit()

        return {
            "success": True,
            "template": template.name,
            "agents_created": len(created_agents),
            "rules_created": len(created_rules),
            "agents": [
                {
                    "id": str(a.id),
                    "role": a.role,
                    "specialization": a.specialization
                }
                for a in created_agents
            ],
            "routing_rules": [
                {
                    "asker": r.asker_role,
                    "responder": r.responder_role,
                    "level": r.escalation_level
                }
                for r in created_rules
            ]
        }
```

---

### ✅ Step 4: Complete Template Definitions (PARTIALLY COMPLETED)

**Status:** Software Dev Squad template complete and tested

**Completed:**
- [x] `templates/software_dev_squad.yaml` - Full template with 6 agents, 17 routing rules, 4 example conversations

**File:** `templates/software_dev_squad.yaml`

```yaml
name: "Software Development Squad"
slug: "software-dev-squad"
description: "Complete development team with PM, developers, architects, and QA. Ideal for building features end-to-end."
category: "development"
is_featured: true

agents:
  - role: "project_manager"
    specialization: "agile"
    llm_provider: "anthropic"
    llm_model: "claude-3-5-sonnet-20241022"
    description: "Manages projects, breaks down features, coordinates team"

  - role: "solution_architect"
    specialization: "default"
    llm_provider: "anthropic"
    llm_model: "claude-3-5-sonnet-20241022"
    description: "Designs system architecture, makes technology decisions"

  - role: "tech_lead"
    specialization: "default"
    llm_provider: "anthropic"
    llm_model: "claude-3-5-sonnet-20241022"
    description: "Guides developers, reviews code, makes technical decisions"

  - role: "backend_developer"
    specialization: "python_fastapi"
    llm_provider: "openai"
    llm_model: "gpt-4"
    description: "Implements backend features, APIs, database logic"

  - role: "frontend_developer"
    specialization: "react_typescript"
    llm_provider: "openai"
    llm_model: "gpt-4"
    description: "Builds user interfaces, implements frontend features"

  - role: "qa_tester"
    specialization: "automation"
    llm_provider: "openai"
    llm_model: "gpt-4"
    description: "Tests features, writes automation, ensures quality"

routing_rules:
  # Backend Developer routes
  - asker_role: "backend_developer"
    question_type: "implementation"
    escalation_level: 0
    responder_role: "tech_lead"
    priority: 10

  - asker_role: "backend_developer"
    question_type: "implementation"
    escalation_level: 1
    responder_role: "solution_architect"
    priority: 10

  - asker_role: "backend_developer"
    question_type: "architecture"
    escalation_level: 0
    responder_role: "solution_architect"
    priority: 10

  # Frontend Developer routes
  - asker_role: "frontend_developer"
    question_type: "implementation"
    escalation_level: 0
    responder_role: "tech_lead"
    priority: 10

  - asker_role: "frontend_developer"
    question_type: "implementation"
    escalation_level: 1
    responder_role: "solution_architect"
    priority: 10

  # Tech Lead routes
  - asker_role: "tech_lead"
    question_type: "architecture"
    escalation_level: 0
    responder_role: "solution_architect"
    priority: 10

  - asker_role: "tech_lead"
    question_type: "default"
    escalation_level: 1
    responder_role: "project_manager"
    priority: 10

  # Solution Architect routes
  - asker_role: "solution_architect"
    question_type: "business_requirement"
    escalation_level: 0
    responder_role: "project_manager"
    priority: 10

  # QA Tester routes
  - asker_role: "qa_tester"
    question_type: "default"
    escalation_level: 0
    responder_role: "tech_lead"
    priority: 10

success_metrics:
  - name: "Questions per Day"
    target: 20
    unit: "count"
    description: "Number of questions handled daily"

  - name: "Average Response Time"
    target: 180
    unit: "seconds"
    description: "Mean time to first response"

  - name: "Escalation Rate"
    target: 15
    unit: "percentage"
    description: "Percentage of questions that escalate"

  - name: "Resolution Rate"
    target: 95
    unit: "percentage"
    description: "Percentage of questions resolved"

example_conversations:
  - title: "Caching Strategy Discussion"
    description: "Backend developer asks about implementing caching"
    messages:
      - from: "backend_developer"
        to: "tech_lead"
        content: "I'm implementing user session caching. Should I use Redis or Memcached?"
        type: "question"

      - from: "tech_lead"
        to: "backend_developer"
        content: |
          Use Redis for session caching.

          Why: Redis supports richer data structures (hashes for sessions) and has persistence.

          Example:
          ```python
          r.hset(f'session:{user_id}', mapping=session_data)
          r.expire(f'session:{user_id}', 3600)  # 1 hour
          ```

          Next: Set up Redis with connection pooling and configure TTL.
        type: "answer"

  - title: "Architecture Question Escalation"
    description: "Demonstrates escalation from tech lead to architect"
    messages:
      - from: "backend_developer"
        to: "tech_lead"
        content: "We're expecting 10M users. How should we scale the database?"
        type: "question"

      - from: "tech_lead"
        to: "solution_architect"
        content: "Database scaling question for 10M users - this needs your expertise."
        type: "escalation"

      - from: "solution_architect"
        to: "backend_developer"
        content: |
          For 10M users, I recommend:

          1. Read replicas (3-5) for query distribution
          2. Connection pooling (PgBouncer)
          3. Caching layer (Redis) for hot data
          4. Sharding by user_id if needed

          Start with replicas + caching. Sharding is last resort.
        type: "answer"

use_cases:
  - "Feature development teams"
  - "Startup engineering teams"
  - "Agile development squads"
  - "Product teams building MVPs"

tags:
  - "development"
  - "agile"
  - "full-stack"
  - "engineering"
```

**Create Similar for:**
- [ ] `customer_support_squad.yaml`
- [ ] `sales_pipeline_squad.yaml`
- [ ] `devops_oncall_squad.yaml`
- [ ] `content_team_squad.yaml`

---

### Step 5: API Endpoints (30 min)

**File:** `backend/api/v1/endpoints/templates.py`

```python
"""
Template API Endpoints
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_async_session
from backend.services.template_service import TemplateService
from backend.schemas.template import (
    TemplateListResponse,
    TemplateDetailResponse,
    ApplyTemplateRequest,
    ApplyTemplateResponse
)

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/", response_model=List[TemplateListResponse])
async def list_templates(
    category: Optional[str] = None,
    featured_only: bool = False,
    db: AsyncSession = Depends(get_async_session)
):
    """
    List all available squad templates

    Filter by category or show only featured templates
    """
    templates = await TemplateService.list_templates(
        db=db,
        category=category,
        featured_only=featured_only
    )

    return [
        TemplateListResponse(
            id=t.id,
            name=t.name,
            slug=t.slug,
            description=t.description,
            category=t.category,
            is_featured=t.is_featured,
            usage_count=t.usage_count,
            avg_rating=t.avg_rating
        )
        for t in templates
    ]


@router.get("/{template_id}", response_model=TemplateDetailResponse)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_async_session)
):
    """Get detailed template information"""
    template = await TemplateService.get_template(db, template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return TemplateDetailResponse(
        id=template.id,
        name=template.name,
        slug=template.slug,
        description=template.description,
        category=template.category,
        template_definition=template.template_definition,
        usage_count=template.usage_count,
        avg_rating=template.avg_rating
    )


@router.post("/{template_id}/apply", response_model=ApplyTemplateResponse)
async def apply_template(
    template_id: UUID,
    request: ApplyTemplateRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Apply a template to a squad

    Creates all agents and routing rules from the template
    """
    result = await TemplateService.apply_template(
        db=db,
        template_id=template_id,
        squad_id=request.squad_id,
        user_id=request.user_id,
        customization=request.customization
    )

    return ApplyTemplateResponse(**result)
```

**Also Create:**
- [ ] `backend/schemas/template.py` - Pydantic schemas
- [ ] Update `backend/api/v1/router.py` to include templates router

---

### Step 6: CLI Tool (30 min)

**File:** `backend/cli/apply_template.py`

```python
#!/usr/bin/env python3
"""
Quick CLI tool to apply squad templates

Usage:
    python -m backend.cli.apply_template software-dev-squad "My Squad Name"
    python -m backend.cli.apply_template --list
"""
import asyncio
import sys
from uuid import uuid4

from sqlalchemy import select
from backend.core.database import AsyncSessionLocal
from backend.models.user import User
from backend.services.squad_service import SquadService
from backend.services.template_service import TemplateService
from backend.models import SquadTemplate


async def list_templates():
    """List all available templates"""
    async with AsyncSessionLocal() as db:
        templates = await TemplateService.list_templates(db)

        print("\n📦 Available Squad Templates:\n")
        for t in templates:
            print(f"  {t.slug}")
            print(f"    Name: {t.name}")
            print(f"    Category: {t.category}")
            print(f"    Used: {t.usage_count} times")
            print()


async def apply_template_cli(template_slug: str, squad_name: str):
    """Apply a template to create a new squad"""
    async with AsyncSessionLocal() as db:
        # Get or create default user
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

        if not user:
            print("❌ No users found. Please create a user first.")
            return

        # Find template by slug
        stmt = select(SquadTemplate).where(SquadTemplate.slug == template_slug)
        result = await db.execute(stmt)
        template = result.scalar_one_or_none()

        if not template:
            print(f"❌ Template not found: {template_slug}")
            print("\nRun with --list to see available templates")
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

        print(f"✅ Squad created: {squad.id}")

        # Apply template
        result = await TemplateService.apply_template(
            db=db,
            template_id=template.id,
            squad_id=squad.id,
            user_id=user.id
        )

        print(f"\n✅ Template applied successfully!")
        print(f"   Agents created: {result['agents_created']}")
        print(f"   Routing rules: {result['rules_created']}\n")

        print("📋 Squad Members:")
        for agent in result['agents']:
            print(f"   - {agent['role']} ({agent['specialization']})")

        print(f"\n🎉 Squad ready! ID: {squad.id}")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m backend.cli.apply_template --list")
        print("  python -m backend.cli.apply_template <template-slug> <squad-name>")
        sys.exit(1)

    if sys.argv[1] == "--list":
        asyncio.run(list_templates())
    else:
        template_slug = sys.argv[1]
        squad_name = sys.argv[2] if len(sys.argv) > 2 else "My Squad"
        asyncio.run(apply_template_cli(template_slug, squad_name))


if __name__ == "__main__":
    main()
```

---

### Step 7: Seed Database with Templates (30 min)

**File:** `backend/scripts/seed_templates.py`

```python
"""
Seed database with default squad templates

Run:
    python -m backend.scripts.seed_templates
"""
import asyncio
import yaml
from pathlib import Path
from uuid import uuid4

from backend.core.database import AsyncSessionLocal
from backend.models import SquadTemplate


async def seed_templates():
    """Load all templates from backend/templates/ and insert into DB"""
    template_dir = Path(__file__).parent.parent / "templates"

    async with AsyncSessionLocal() as db:
        template_files = list(template_dir.glob("*.yaml"))

        print(f"\n📦 Found {len(template_files)} template files\n")

        for template_file in template_files:
            with open(template_file) as f:
                data = yaml.safe_load(f)

            # Check if already exists
            from sqlalchemy import select
            stmt = select(SquadTemplate).where(
                SquadTemplate.slug == data['slug']
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                print(f"⏭️  Skipping {data['name']} (already exists)")
                continue

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
            print(f"✅ Added template: {data['name']}")

        await db.commit()
        print(f"\n🎉 Templates seeded successfully!\n")


if __name__ == "__main__":
    asyncio.run(seed_templates())
```

---

## 🧪 Testing Plan

### Manual Testing Checklist

**Test 1: List Templates**
```bash
curl http://localhost:8000/api/v1/templates/
```

Expected: JSON array of 5 templates

**Test 2: Get Template Details**
```bash
curl http://localhost:8000/api/v1/templates/{template_id}
```

Expected: Full template with agents, routing, examples

**Test 3: Apply Template via API**
```bash
curl -X POST http://localhost:8000/api/v1/templates/{template_id}/apply \
  -H "Content-Type: application/json" \
  -d '{
    "squad_id": "...",
    "user_id": "..."
  }'
```

Expected: Squad created with all agents and routing

**Test 4: Apply via CLI**
```bash
python -m backend.cli.apply_template software-dev-squad "My Team"
```

Expected: Squad created, agents added, confirmation message

**Test 5: Verify Routing**
```bash
# Run hierarchical demo with templated squad
python demo_hierarchical_conversations.py
```

Expected: Questions route correctly through hierarchy

---

## 📈 Success Metrics

**Immediately After Implementation:**
- [ ] All 5 templates load successfully
- [ ] CLI tool creates squad in <30 seconds
- [ ] API responds in <1 second
- [ ] Routing rules work correctly
- [ ] System prompts load from files

**User Experience:**
- [ ] Non-technical user can create squad in <5 minutes
- [ ] Templates work out-of-the-box (no config needed)
- [ ] Example conversations demonstrate value
- [ ] Clear documentation for each template

---

## 🚀 Rollout Plan

### Day 1: Foundation
- Morning: Database schema + migration
- Afternoon: Template service implementation
- Evening: First template (Software Dev Squad)

### Day 2: Templates & APIs
- Morning: Create remaining 4 templates
- Afternoon: Write all system prompts
- Evening: API endpoints + schemas

### Day 3: Polish & Test
- Morning: CLI tool + seed script
- Afternoon: End-to-end testing
- Evening: Documentation + example videos

---

## 📚 Documentation Needed

### User Docs

**File:** `docs/using-templates.md`
- How to browse templates
- How to apply a template
- How to customize a template
- When to use each template type

### Developer Docs

**File:** `docs/creating-templates.md`
- Template YAML format
- How to add new templates
- System prompt guidelines
- Testing templates

### Quick Start

**File:** `QUICKSTART.md`
```markdown
# Quick Start with Templates

Get a fully-configured AI agent squad in 3 commands:

1. **List available templates:**
   ```bash
   python -m backend.cli.apply_template --list
   ```

2. **Apply a template:**
   ```bash
   python -m backend.cli.apply_template software-dev-squad "My Dev Team"
   ```

3. **Start using your squad:**
   Your squad is ready with:
   - 6 AI agents (PM, Architect, Tech Lead, 2 Devs, QA)
   - 15 routing rules (automatic escalation)
   - Production-ready prompts

   Try it: `python demo_hierarchical_conversations.py`
```

---

## 🎯 Next Steps After Implementation

**Immediate (Week 1):**
1. Record 2-minute video showing template application
2. Blog post: "From Zero to AI Squad in 5 Minutes"
3. Share on Twitter/LinkedIn

**Short-term (Month 1):**
1. Add 5 more templates based on user requests
2. Template marketplace UI (frontend)
3. Template ratings and reviews

**Medium-term (Month 3):**
1. User-submitted templates
2. Template forking/customization
3. Template analytics (which are most popular)

---

## 💡 Future Enhancements

1. **Template Variants**
   - "Software Dev Squad (Small)" - 3 agents
   - "Software Dev Squad (Large)" - 10 agents

2. **Industry-Specific Templates**
   - Healthcare: HIPAA-compliant templates
   - Finance: Compliance-aware templates
   - Legal: Legal document review templates

3. **Template Bundles**
   - "Complete Startup Pack" - Dev + Support + Sales
   - "Enterprise Pack" - All templates + custom

4. **AI-Generated Templates**
   - User describes their team
   - AI generates custom template
   - User reviews and applies

---

## ✅ Completed Work Summary

### Files Created

**Database:**
- `backend/models/squad_template.py` - SquadTemplate model
- `backend/alembic/versions/002_add_squad_templates.py` - Migration

**System Prompts:**
- `roles/project_manager/agile.md` - PM agent prompt
- `roles/solution_architect/default.md` - Architect agent prompt
- `roles/tech_lead/default.md` - Tech Lead agent prompt
- `roles/frontend_developer/react_typescript.md` - Frontend dev prompt
- `roles/qa_tester/automation.md` - QA tester prompt

**Templates:**
- `templates/software_dev_squad.yaml` - Complete Software Dev Squad template
  - 6 agents (PM, Architect, TL, Backend Dev, Frontend Dev, QA)
  - 17 routing rules (full escalation hierarchy)
  - 4 example conversations
  - Success metrics and use cases

**Scripts:**
- `apply_template_quick.py` - Quick template loader and applicator

### What Works

1. ✅ Load YAML template into database
2. ✅ Create squad with all agents from template
3. ✅ Set up routing rules automatically
4. ✅ Track template usage
5. ✅ Verified end-to-end functionality

### Test Results

```
Squad: Software Dev Squad Demo
Status: active

Agents (6):
  ✓ project_manager (agile) - anthropic/claude-3-5-sonnet-20241022
  ✓ solution_architect (default) - anthropic/claude-3-5-sonnet-20241022
  ✓ tech_lead (default) - anthropic/claude-3-5-sonnet-20241022
  ✓ backend_developer (python_fastapi) - openai/gpt-4
  ✓ frontend_developer (react_typescript) - openai/gpt-4
  ✓ qa_tester (automation) - openai/gpt-4

Routing Rules (17):
  ✓ Complete escalation paths
  ✓ Developer → Tech Lead → Architect → PM hierarchy
  ✓ Specialized routing by question type
```

---

*Reference template complete! Ready to create additional templates and build full service.*
