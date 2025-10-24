# Agent System Prompts (Roles)

## Overview

The `roles/` directory contains system prompts for each agent role. These prompts define the agent's personality, capabilities, responsibilities, and behavior.

## Structure

```
roles/
├── project_manager/
│   └── default_prompt.md          # PM system prompt
├── tech_lead/
│   └── default_prompt.md          # TL system prompt
├── backend_developer/
│   ├── default_prompt.md          # Generic backend
│   ├── python_fastapi.md          # Python/FastAPI specialist
│   ├── nodejs_express.md          # Node.js/Express specialist
│   └── java_spring.md             # Java/Spring specialist
├── frontend_developer/
│   ├── default_prompt.md          # Generic frontend
│   ├── react_nextjs.md            # React/Next.js specialist
│   ├── vue_nuxt.md                # Vue/Nuxt specialist
│   └── angular.md                 # Angular specialist
├── qa_tester/
│   └── default_prompt.md          # QA system prompt
├── solution_architect/
│   └── default_prompt.md          # Architect prompt
├── devops_engineer/
│   └── default_prompt.md          # DevOps prompt
├── ai_engineer/
│   └── default_prompt.md          # AI/ML prompt
└── designer/
    └── default_prompt.md          # Designer prompt
```

## Prompt Structure

Each system prompt typically includes:

### 1. Role Definition
```markdown
# Role: Backend Developer (Python/FastAPI Specialist)

You are an expert backend developer specializing in Python and FastAPI.
```

### 2. Core Responsibilities
```markdown
## Responsibilities

1. Implement backend APIs using Python and FastAPI
2. Design database schemas with SQLAlchemy
3. Write comprehensive tests (unit + integration)
4. Optimize performance and scalability
5. Ensure security best practices
```

### 3. Technical Skills
```markdown
## Technical Expertise

- **Languages**: Python 3.11+
- **Frameworks**: FastAPI, SQLAlchemy, Pydantic
- **Databases**: PostgreSQL, Redis
- **Testing**: pytest, pytest-asyncio
- **Tools**: Docker, Git, VS Code
```

### 4. Communication Style
```markdown
## Communication

- Be concise and technical
- Ask clarifying questions when requirements are unclear
- Document decisions and trade-offs
- Provide code examples when helpful
```

### 5. Behavioral Guidelines
```markdown
## Guidelines

- Follow Python PEP 8 style guide
- Write self-documenting code
- Add docstrings for all functions
- Consider edge cases
- Prioritize maintainability
```

### 6. Collaboration
```markdown
## Team Collaboration

- Ask Tech Lead for architectural decisions
- Request code reviews before completion
- Communicate blockers to Project Manager
- Help other developers when possible
```

## Loading Prompts

Prompts are automatically loaded by `AgentFactory`:

```python
# Default prompt
system_prompt = AgentFactory.load_system_prompt("backend_developer")

# Specialized prompt
system_prompt = AgentFactory.load_system_prompt(
    role="backend_developer",
    specialization="python_fastapi"
)
```

### Load Order
1. Try `{role}/{specialization}.md`
2. Fall back to `{role}/default_prompt.md`
3. Fall back to generic default

## Creating Custom Prompts

### 1. Create Role Directory
```bash
mkdir roles/custom_role
```

### 2. Write Prompt File
```bash
touch roles/custom_role/default_prompt.md
```

### 3. Structure Your Prompt
```markdown
# Role: Custom Role

Define role clearly...

## Responsibilities
...

## Technical Skills
...

## Communication Style
...
```

### 4. Register Role
Update `AgentFactory` to recognize the new role.

## Prompt Best Practices

### DO:
✅ Be specific about technical requirements
✅ Include examples of expected behavior
✅ Define clear boundaries (what agent should/shouldn't do)
✅ Specify communication protocols
✅ Include collaboration guidelines

### DON'T:
❌ Make prompts too long (>2000 words)
❌ Include contradictory instructions
❌ Assume implicit knowledge
❌ Over-constrain creativity
❌ Forget to specify error handling

## Example: Backend Developer Prompt

```markdown
# Role: Backend Developer (Python/FastAPI)

You are an expert backend developer...

## Core Responsibilities

1. **API Development**
   - Design RESTful APIs
   - Implement endpoints with FastAPI
   - Use Pydantic for validation
   - Document with OpenAPI

2. **Database Design**
   - Create SQLAlchemy models
   - Write Alembic migrations
   - Optimize queries
   - Ensure data integrity

3. **Testing**
   - Write pytest tests
   - Achieve 80%+ coverage
   - Test edge cases
   - Use fixtures effectively

...
```

## Updating Prompts

### Version Control
- Track prompts in Git
- Review changes in PRs
- Tag major versions

### Testing Changes
```bash
# Test new prompt
python test_agent_with_new_prompt.py

# Compare responses
python compare_prompt_versions.py --old v1 --new v2
```

### Rollback
```bash
# Revert to previous version
git checkout HEAD~1 roles/backend_developer/default_prompt.md
```

## Prompt Engineering Tips

1. **Be Specific**: "Use Python type hints" vs "Write good code"
2. **Provide Examples**: Show what good output looks like
3. **Set Constraints**: Define limits (tokens, time, complexity)
4. **Iterate**: Test and refine based on actual usage
5. **Context Matters**: Consider what context agent receives

## Related Documentation

- See `../backend/agents/CLAUDE.md` for agent architecture
- See `../backend/agents/specialized/CLAUDE.md` for agent roles
- See `../backend/agents/factory.py` for prompt loading logic
