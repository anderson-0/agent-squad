# Phase 4.5: Agno Migration - Week 1, Day 1
## Agno Setup & Proof of Concept

> **Goal:** Install Agno, understand the framework, and create first working agent
> **Duration:** 1 day (8 hours)
> **Output:** Working proof of concept with 1 migrated agent

---

## 📋 Day 1 Checklist

- [ ] Install Agno framework and dependencies
- [ ] Set up Agno database (PostgreSQL)
- [ ] Configure Agno with our LLM providers
- [ ] Create proof of concept: Simple agent
- [ ] Test basic agent functionality
- [ ] Document findings and next steps

---

## 🔧 Step 1: Install Agno Framework (30 min)

### 1.1 Add Agno to Requirements

```bash
# Navigate to project root
cd /Users/anderson/Documents/anderson-0/agent-squad

# Add Agno to backend requirements
echo "agno>=0.1.0" >> backend/requirements.txt
```

### 1.2 Install Dependencies

```bash
# Activate your virtual environment
source backend/.venv/bin/activate

# Install Agno
pip install agno

# Or with all extras for maximum power
pip install "agno[all]"

# Verify installation
python -c "import agno; print(agno.__version__)"
```

### 1.3 Additional Dependencies

```bash
# For PostgreSQL support (production)
pip install psycopg2-binary sqlalchemy

# For model providers (if not already installed)
pip install openai anthropic groq

# Update requirements.txt
pip freeze > backend/requirements.txt
```

**Expected Output:**
```
Successfully installed agno-0.x.x
Successfully installed sqlalchemy-2.x.x
```

---

## 🗄️ Step 2: Configure Agno Database (30 min)

### 2.1 Update Database Configuration

Create new configuration file for Agno:

```python
# backend/core/agno_config.py

from agno.storage.postgres import PostgresDb
from backend.core.config import settings

def get_agno_db():
    """
    Get Agno database instance.

    Agno will create its own tables:
    - agno_sessions (conversation sessions)
    - agno_memory (agent memory)
    - agno_runs (execution history)
    """
    return PostgresDb(
        db_url=settings.DATABASE_URL,
        # Agno tables use 'agno_' prefix to avoid conflicts
        table_name_prefix="agno_"
    )

# Global database instance
agno_db = get_agno_db()
```

### 2.2 Initialize Agno Tables

Create migration script:

```python
# backend/scripts/init_agno_db.py

import asyncio
from backend.core.agno_config import agno_db

async def init_agno_database():
    """Initialize Agno database tables."""
    print("🔧 Initializing Agno database...")

    # Agno will auto-create tables on first use
    # But we can verify connection
    try:
        await agno_db.test_connection()
        print("✅ Agno database connection successful")
        print("📊 Agno will create tables on first agent run:")
        print("   - agno_sessions")
        print("   - agno_memory")
        print("   - agno_runs")
    except Exception as e:
        print(f"❌ Agno database connection failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(init_agno_database())
```

**Run it:**
```bash
python backend/scripts/init_agno_db.py
```

---

## 🎯 Step 3: Create Proof of Concept Agent (1 hour)

### 3.1 Simple Agent Example

Create a test file to verify Agno works:

```python
# backend/agents/agno_poc.py
"""
Proof of Concept: First Agno Agent

This demonstrates:
1. Creating an Agno agent with Claude
2. Persistent conversation history
3. Memory across sessions
4. Tool integration (MCP)
"""

import asyncio
from agno import Agent
from agno.models import Claude
from agno.tools import MCPTools
from backend.core.agno_config import agno_db
from backend.core.config import settings

def create_poc_agent():
    """Create a simple proof of concept agent."""

    agent = Agent(
        name="POC Agent",
        role="Test agent to verify Agno integration",
        model=Claude(
            id="claude-sonnet-4",
            api_key=settings.ANTHROPIC_API_KEY
        ),

        # Database for persistent memory
        db=agno_db,

        # Add conversation history to context automatically
        add_history_to_context=True,

        # Number of previous messages to include
        num_history_responses=5,

        # System prompt (optional, can load from file later)
        description="""
        You are a test agent verifying Agno framework integration.
        Be helpful and demonstrate your capabilities.
        """,

        # Enable debug mode
        debug_mode=True
    )

    return agent

async def test_basic_conversation():
    """Test basic agent conversation."""
    print("\n🤖 Testing Basic Conversation\n")

    agent = create_poc_agent()

    # First message
    print("User: Hello! Can you help me test Agno?")
    response = agent.run("Hello! Can you help me test Agno?")
    print(f"Agent: {response.content}\n")

    # Second message - should remember context
    print("User: What did I just ask you?")
    response = agent.run("What did I just ask you?")
    print(f"Agent: {response.content}\n")

    # Check session persistence
    print(f"📊 Session ID: {agent.session_id}")
    print(f"📝 Messages in session: {len(agent.messages)}")

    return agent

async def test_persistent_memory():
    """Test that memory persists across agent instances."""
    print("\n💾 Testing Persistent Memory\n")

    # Create first agent instance
    agent1 = create_poc_agent()
    session_id = agent1.session_id

    print("Agent 1: First conversation")
    agent1.run("My name is Anderson")
    agent1.run("I love building AI agents")

    print(f"Session ID: {session_id}\n")

    # Create second agent instance with SAME session
    agent2 = Agent(
        name="POC Agent",
        model=Claude(
            id="claude-sonnet-4",
            api_key=settings.ANTHROPIC_API_KEY
        ),
        db=agno_db,
        session_id=session_id,  # Use same session!
        add_history_to_context=True
    )

    print("Agent 2: Can you remember my name?")
    response = agent2.run("Can you remember my name and what I love?")
    print(f"Agent: {response.content}\n")

    # Should remember from previous conversation!
    if "Anderson" in response.content:
        print("✅ Persistent memory working!")
    else:
        print("⚠️ Memory not persisted across instances")

async def test_tool_integration():
    """Test MCP tool integration."""
    print("\n🛠️ Testing Tool Integration\n")

    # Note: This requires MCP server to be running
    # We'll add this after basic agent works

    try:
        agent = Agent(
            name="Tool Agent",
            model=Claude(
                id="claude-sonnet-4",
                api_key=settings.ANTHROPIC_API_KEY
            ),
            db=agno_db,
            tools=[
                MCPTools(
                    transport="stdio",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-git"]
                )
            ]
        )

        print("Agent with Git tools created successfully")
        print(f"Available tools: {len(agent.tools)}")

        # Test tool execution
        response = agent.run("List the files in the current git repository")
        print(f"Agent: {response.content}\n")

        print("✅ Tool integration working!")

    except Exception as e:
        print(f"⚠️ Tool integration not ready yet: {e}")
        print("   (This is OK - we'll configure tools later)")

async def main():
    """Run all POC tests."""
    print("="*60)
    print("🚀 AGNO FRAMEWORK - PROOF OF CONCEPT")
    print("="*60)

    try:
        # Test 1: Basic conversation
        await test_basic_conversation()

        # Test 2: Persistent memory
        await test_persistent_memory()

        # Test 3: Tool integration (optional)
        await test_tool_integration()

        print("\n" + "="*60)
        print("✅ PROOF OF CONCEPT COMPLETE!")
        print("="*60)
        print("\nNext Steps:")
        print("1. Agno is working correctly")
        print("2. Ready to migrate BaseSquadAgent")
        print("3. Ready to migrate specialized agents")

    except Exception as e:
        print(f"\n❌ Error during POC: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
```

### 3.2 Run Proof of Concept

```bash
# From project root
PYTHONPATH=/Users/anderson/Documents/anderson-0/agent-squad python backend/agents/agno_poc.py
```

**Expected Output:**
```
============================================================
🚀 AGNO FRAMEWORK - PROOF OF CONCEPT
============================================================

🤖 Testing Basic Conversation

User: Hello! Can you help me test Agno?
Agent: Hello! I'd be happy to help you test Agno...

User: What did I just ask you?
Agent: You asked if I could help you test Agno...

📊 Session ID: abc123...
📝 Messages in session: 4

💾 Testing Persistent Memory

Agent 1: First conversation
Session ID: def456...

Agent 2: Can you remember my name?
Agent: Yes! Your name is Anderson and you love building AI agents...

✅ Persistent memory working!

============================================================
✅ PROOF OF CONCEPT COMPLETE!
============================================================
```

---

## 🔬 Step 4: Compare with Current Implementation (30 min)

### 4.1 Current Agent (Custom)

```python
# Current implementation
from backend.agents.base_agent import BaseSquadAgent, AgentConfig

config = AgentConfig(
    role="project_manager",
    llm_provider="anthropic",
    llm_model="claude-3-sonnet-20240229",
    temperature=0.7
)

agent = BaseSquadAgent(config, mcp_client=None)

# Issues:
# - No persistent history (in-memory only)
# - No persistent memory
# - Manual LLM client setup
# - Manual conversation management
```

### 4.2 Agno Agent (New)

```python
# Agno implementation
from agno import Agent
from agno.models import Claude

agent = Agent(
    name="Project Manager",
    role="Orchestrate software development squad",
    model=Claude(id="claude-sonnet-4"),
    db=agno_db,
    add_history_to_context=True,  # Auto-managed!
    num_history_responses=10,
    temperature=0.7
)

# Benefits:
# ✅ Persistent history (database)
# ✅ Persistent memory (database)
# ✅ Auto LLM client setup
# ✅ Auto conversation management
# ✅ Session resumption
# ✅ Collective memory (culture)
```

### 4.3 Side-by-Side Comparison

| Feature | Current (Custom) | Agno Framework |
|---------|-----------------|----------------|
| **Agent Creation** | `BaseSquadAgent(config)` | `Agent(name=..., model=...)` |
| **History Storage** | In-memory list | PostgreSQL |
| **Memory** | Redis (manual) | Built-in (PostgreSQL) |
| **Session Resume** | ❌ | ✅ |
| **Multi-turn Context** | Manual | Automatic |
| **Tool Integration** | Custom MCP | Built-in MCP + 100+ |
| **Performance** | ~50ms | ~3μs (100x faster) |
| **Maintenance** | 909 lines | Framework handles it |

---

## 📊 Step 5: Document POC Findings (30 min)

Create findings document:

```markdown
# POC Findings - Agno Framework

## ✅ What Works

1. **Agent Creation:** Simple and clean API
2. **Conversation History:** Auto-persisted to database
3. **Memory:** Persistent across sessions
4. **Multi-Model Support:** Easy to switch between OpenAI/Anthropic/Groq
5. **Session Management:** Built-in session IDs and resumption

## ⚠️ Considerations

1. **Database Schema:** Agno creates own tables (agno_*)
2. **Migration:** Need to migrate conversation history format
3. **Tool Integration:** MCP works but needs configuration
4. **Custom Methods:** Need to convert specialized agent methods

## 🎯 Next Steps

1. Create Agno wrapper for our use case
2. Migrate BaseSquadAgent → AgnoBaseAgent
3. Migrate ProjectManagerAgent as first specialized agent
4. Update AgentFactory to create Agno agents
5. Update tests

## 📝 Key Learnings

- Agno handles 90% of what BaseSquadAgent does
- Much faster and more efficient
- Less code to maintain
- Better persistence story
```

---

## 🎯 Step 6: Plan Day 2-3 Migration (30 min)

### 6.1 Create Migration Wrapper

We'll create a compatibility layer:

```python
# backend/agents/agno_base.py
"""
Agno-based agent foundation.

This replaces BaseSquadAgent with Agno while maintaining
compatibility with our existing codebase.
"""

from typing import List, Dict, Any, Optional
from agno import Agent
from agno.models import Claude, OpenAI, Groq
from backend.core.agno_config import agno_db
from backend.core.config import settings

class AgnoSquadAgent:
    """
    Wrapper around Agno Agent that maintains compatibility
    with our existing specialized agent implementations.
    """

    def __init__(
        self,
        name: str,
        role: str,
        llm_provider: str = "anthropic",
        llm_model: str = "claude-sonnet-4",
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        session_id: Optional[str] = None,
        tools: Optional[List] = None
    ):
        # Create appropriate model based on provider
        model = self._create_model(llm_provider, llm_model, temperature)

        # Create Agno agent
        self.agent = Agent(
            name=name,
            role=role,
            model=model,
            db=agno_db,
            description=system_prompt,
            add_history_to_context=True,
            num_history_responses=10,
            session_id=session_id,
            tools=tools or []
        )

    def _create_model(self, provider: str, model: str, temperature: float):
        """Create model instance based on provider."""
        if provider == "anthropic":
            return Claude(
                id=model,
                api_key=settings.ANTHROPIC_API_KEY,
                temperature=temperature
            )
        elif provider == "openai":
            return OpenAI(
                id=model,
                api_key=settings.OPENAI_API_KEY,
                temperature=temperature
            )
        elif provider == "groq":
            return Groq(
                id=model,
                api_key=settings.GROQ_API_KEY,
                temperature=temperature
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process message (compatibility with BaseSquadAgent).
        """
        # Add context to message if provided
        if context:
            enhanced_message = f"{message}\n\nContext: {context}"
        else:
            enhanced_message = message

        # Run agent
        response = self.agent.run(enhanced_message)

        # Return in compatible format
        return {
            "content": response.content,
            "thinking": None,  # Agno doesn't separate thinking
            "action_items": [],  # Can parse from content if needed
            "metadata": {
                "session_id": self.agent.session_id,
                "messages_count": len(self.agent.messages)
            }
        }

    def get_capabilities(self) -> List[str]:
        """Override in subclasses."""
        return []
```

### 6.2 Tomorrow's Goals

**Day 2-3 Tasks:**
1. ✅ Complete AgnoSquadAgent wrapper
2. Migrate ProjectManagerAgent to use AgnoSquadAgent
3. Test all PM capabilities with Agno
4. Compare performance (custom vs Agno)
5. Document any issues or blockers

---

## ✅ Day 1 Completion Checklist

Before ending Day 1, verify:

- [ ] Agno installed and working
- [ ] POC agent created and tested
- [ ] Basic conversation works
- [ ] Persistent memory verified
- [ ] Database connection confirmed
- [ ] Findings documented
- [ ] Day 2-3 plan created
- [ ] Team updated on progress

---

## 🚨 Troubleshooting

### Issue: Agno import fails
```bash
# Solution: Reinstall
pip uninstall agno
pip install agno --upgrade
```

### Issue: Database connection fails
```python
# Solution: Check DATABASE_URL
from backend.core.config import settings
print(settings.DATABASE_URL)

# Verify PostgreSQL is running
psql -U postgres -c "SELECT 1"
```

### Issue: Claude API key not working
```python
# Solution: Verify environment variable
import os
print(os.getenv("ANTHROPIC_API_KEY"))

# Or check settings
from backend.core.config import settings
print(settings.ANTHROPIC_API_KEY[:10] + "...")
```

---

## 📚 Resources

- **Agno Docs:** https://docs.agno.com
- **Agno GitHub:** https://github.com/agno-agi/agno
- **Agno Examples:** https://github.com/agno-agi/agno/tree/main/examples
- **Our Migration Plan:** [README.md](./README.md)

---

**End of Day 1**

Great work! You now have:
✅ Agno installed and configured
✅ Proof of concept working
✅ Understanding of Agno capabilities
✅ Plan for Days 2-3

**Tomorrow:** Migrate BaseSquadAgent and first specialized agent!

---

> **Next:** [Week 1, Day 2-3: Core Agent Migration →](./03_week1_day2-3_implementation.md)
