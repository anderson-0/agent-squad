# Squad Template System - Quick Reference

Complete guide to creating and using squad templates in Agent Squad.

## Overview

The template system allows you to create pre-configured squads with agents and routing rules in seconds. Perfect for MVP deployments and standardizing team structures.

## What's Included

✅ **Database Models**
- `SquadTemplate` - Store reusable squad configurations
- Migration: `001_add_conversation_tracking_and_routing_rules.py`

✅ **Services**
- `TemplateService` - CRUD operations and template application
- Located: `backend/services/template_service.py`

✅ **REST API**
- 7 endpoints for template management
- Located: `backend/api/v1/endpoints/templates.py`
- Base URL: `/api/v1/templates/`

✅ **CLI Tool**
- `apply_template.py` - Quick squad creation
- Command: `python -m backend.cli.apply_template`

✅ **Demo Scripts**
- `demo_template_system.py` - Shows template loading and application
- `demo_template_squad_conversations.py` - Tests routing with template squads

✅ **Pre-built Template**
- Software Development Squad (6 agents, 17 routing rules)
- Located: `templates/software_dev_squad.yaml`

## Quick Start

### 1. List Available Templates

```bash
# Via CLI
python -m backend.cli.apply_template --list

# Via API
curl http://localhost:8000/api/v1/templates/
```

### 2. Create Squad from Template

```bash
# Via CLI (Recommended for MVP)
DEBUG=False python -m backend.cli.apply_template \
  --user-email demo@test.com \
  --template software-dev-squad \
  --squad-name "Alpha Team"

# Via API
curl -X POST http://localhost:8000/api/v1/templates/{template_id}/apply \
  -H "Content-Type: application/json" \
  -d '{
    "squad_id": "new-squad-uuid",
    "user_id": "user-uuid"
  }'
```

### 3. Verify Setup

```bash
# Run the demo
DEBUG=False python demo_template_squad_conversations.py
```

## Software Development Squad Template

### Agents (6)
1. **Project Manager** - Claude 3.5 Sonnet (agile)
2. **Solution Architect** - Claude 3.5 Sonnet (default)
3. **Tech Lead** - Claude 3.5 Sonnet (default)
4. **Backend Developer** - GPT-4 (python_fastapi)
5. **Frontend Developer** - GPT-4 (react_typescript)
6. **QA Tester** - GPT-4 (automation)

### Routing Rules (17)

Complete escalation hierarchy for all roles:

**Backend Developer** → Tech Lead (L0) → Solution Architect (L1) → Project Manager (L2)
**Frontend Developer** → Tech Lead (L0) → Solution Architect (L1)
**QA Tester** → Tech Lead (L0) → Solution Architect (L1)
**Tech Lead** → Solution Architect (L0) → Project Manager (L1)
**Solution Architect** → Project Manager (L0)

### Question Types
- `implementation` - Code implementation questions
- `architecture` - Architecture decisions
- `code_review` - Code review requests
- `test_strategy` - Testing approach
- `bug_verification` - Bug validation
- `business_requirement` - Business needs
- `resource_allocation` - Resource planning
- `default` - Fallback routing

## API Endpoints

### GET `/api/v1/templates/`
List all active templates

**Query Parameters:**
- `category` (optional) - Filter by category
- `featured_only` (optional) - Show only featured templates

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Software Development Squad",
    "slug": "software-dev-squad",
    "category": "development",
    "is_featured": true,
    "usage_count": 42,
    "agent_count": 6,
    "routing_rule_count": 17
  }
]
```

### GET `/api/v1/templates/{id}`
Get template details including full definition

**Response:**
```json
{
  "id": "uuid",
  "name": "Software Development Squad",
  "slug": "software-dev-squad",
  "description": "Complete development team...",
  "category": "development",
  "template_definition": {
    "agents": [...],
    "routing_rules": [...],
    "success_metrics": [...],
    "example_conversations": [...]
  },
  "usage_count": 42,
  "avg_rating": 4.8
}
```

### GET `/api/v1/templates/by-slug/{slug}`
Get template by slug (e.g., "software-dev-squad")

### POST `/api/v1/templates/{id}/apply`
Apply template to create squad with agents and routing rules

**Request:**
```json
{
  "squad_id": "uuid",
  "user_id": "uuid",
  "customization": {
    "agents": [
      {
        "role": "backend_developer",
        "specialization": "python_fastapi",
        "llm_provider": "anthropic",
        "llm_model": "claude-3-5-sonnet-20241022"
      }
    ]
  }
}
```

**Response:**
```json
{
  "success": true,
  "template_name": "Software Development Squad",
  "agents_created": 6,
  "rules_created": 17,
  "agents": [...],
  "routing_rules": [...]
}
```

### POST `/api/v1/templates/`
Create new template (admin)

### PATCH `/api/v1/templates/{id}`
Update template (admin)

### DELETE `/api/v1/templates/{id}`
Soft delete template (admin)

## CLI Tool Usage

### List Templates
```bash
python -m backend.cli.apply_template --list
```

### Apply Template
```bash
python -m backend.cli.apply_template \
  --user-email user@example.com \
  --template software-dev-squad \
  --squad-name "My Team" \
  --description "Optional description"
```

### Short Flags
```bash
python -m backend.cli.apply_template \
  -u user@example.com \
  -t software-dev-squad \
  -n "My Team" \
  -d "Description"
```

### Help
```bash
python -m backend.cli.apply_template --help
```

## Demo Scripts

### Template System Demo
Shows complete template lifecycle:
1. Load template from YAML
2. List available templates
3. Apply template to create squad
4. Verify squad setup
5. Test template customization

```bash
DEBUG=False python demo_template_system.py
```

### Squad Conversations Demo
Tests routing engine with template-created squads:
1. Create squad from template
2. Test basic routing (Dev → Tech Lead)
3. Test escalation chain (3 levels)
4. Test question type routing
5. Test cross-role routing

```bash
DEBUG=False python demo_template_squad_conversations.py
```

**Note:** Use `DEBUG=False` for clean output without SQL logs

## Creating Custom Templates

### 1. Create YAML File

```yaml
# templates/my_custom_squad.yaml
name: "My Custom Squad"
slug: "my-custom-squad"
description: "Description of what this squad does"
category: "custom"
version: "1.0.0"
is_featured: false

agents:
  - role: "manager"
    specialization: "default"
    llm_provider: "anthropic"
    llm_model: "claude-3-5-sonnet-20241022"
    config:
      temperature: 0.7

routing_rules:
  - asker_role: "developer"
    question_type: "implementation"
    escalation_level: 0
    responder_role: "manager"
    priority: 10
```

### 2. Load Template

```python
import asyncio
import yaml
from pathlib import Path
from backend.core.database import AsyncSessionLocal
from backend.services.template_service import TemplateService

async def load_template():
    with open("templates/my_custom_squad.yaml") as f:
        data = yaml.safe_load(f)

    async with AsyncSessionLocal() as db:
        template = await TemplateService.create_template(
            db=db,
            name=data['name'],
            slug=data['slug'],
            description=data['description'],
            category=data['category'],
            template_definition=data,
            is_featured=data.get('is_featured', False)
        )
        print(f"Created template: {template.name}")

asyncio.run(load_template())
```

### 3. Apply Template

```bash
python -m backend.cli.apply_template \
  --user-email user@example.com \
  --template my-custom-squad \
  --squad-name "New Squad"
```

## Template Customization

When applying templates, you can override specific agents:

```python
customization = {
    "agents": [
        {
            "role": "backend_developer",
            "specialization": "python_fastapi",
            "llm_provider": "anthropic",  # Override to use Claude
            "llm_model": "claude-3-5-sonnet-20241022"
        }
    ]
}

result = await TemplateService.apply_template(
    db=db,
    template_id=template_id,
    squad_id=squad_id,
    user_id=user_id,
    customization=customization
)
```

This creates only the specified agents instead of all template agents.

## File Structure

```
agent-squad/
├── backend/
│   ├── api/v1/endpoints/
│   │   └── templates.py                 # REST API endpoints
│   ├── cli/
│   │   ├── apply_template.py           # CLI tool ⭐
│   │   └── README.md                   # CLI documentation
│   ├── models/
│   │   └── squad_template.py           # Database model
│   ├── schemas/
│   │   └── template.py                 # API schemas
│   └── services/
│       └── template_service.py         # Business logic
├── templates/
│   └── software_dev_squad.yaml         # Pre-built template
├── demo_template_system.py             # Template system demo
└── demo_template_squad_conversations.py # Routing tests demo
```

## Best Practices

### For MVP Deployment
1. Use the Software Development Squad template
2. Apply via CLI for fastest setup
3. Verify routing with the demo scripts
4. Test agent communication before production

### For Production
1. Create custom templates for your use cases
2. Use API endpoints for programmatic access
3. Monitor template usage statistics
4. Version your templates in YAML files

### Template Design
1. Include complete escalation hierarchy
2. Cover all common question types
3. Balance LLM costs (Claude for seniors, GPT-4 for juniors)
4. Document routing rules clearly
5. Include example conversations

## Troubleshooting

### Template Not Found
```bash
# List available templates
python -m backend.cli.apply_template --list

# Check slug matches exactly
python -m backend.cli.apply_template -t software-dev-squad  # ✓
python -m backend.cli.apply_template -t software_dev_squad  # ✗
```

### User Not Found
```bash
# Verify user exists
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"

# Or create user first
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

### SQL Logs Cluttering Output
```bash
# Always use DEBUG=False for demos
DEBUG=False python demo_template_system.py
DEBUG=False python demo_template_squad_conversations.py
DEBUG=False python -m backend.cli.apply_template --list
```

### Routing Not Working
```bash
# Run the routing tests demo
DEBUG=False python demo_template_squad_conversations.py

# Check routing rules in database
curl http://localhost:8000/api/v1/routing-rules/?squad_id={squad_id}
```

## Performance

- **Template Application**: ~2 seconds for 6 agents + 17 rules
- **Database Queries**: Single transaction with batch inserts
- **Memory Usage**: Minimal (templates loaded on demand)
- **Scalability**: Templates shared across all users

## Next Steps

1. ✅ Load the Software Development Squad template
2. ✅ Create your first squad via CLI
3. ✅ Run the conversation demo to verify routing
4. ✅ Test agent communication
5. 🎯 Deploy to production!

## Support

- **Documentation**: `backend/cli/README.md`
- **Examples**: `demo_template_*.py` files
- **API Reference**: `/api/v1/docs` (Swagger UI)
- **Template Files**: `templates/*.yaml`

## Summary

The template system provides:
- 🚀 **Fast Setup**: Create complete squads in seconds
- 📋 **Pre-configured**: Tested agent configurations and routing
- 🔄 **Reusable**: Templates work across all users
- 🎨 **Customizable**: Override settings as needed
- 🛠️ **Production-Ready**: Battle-tested for MVP deployment

Perfect for getting Agent Squad MVP deployed quickly with a proven development team structure!
