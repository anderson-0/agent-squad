# Agent Interaction Module

## Overview

The `interaction/` module manages hierarchical agent-to-agent conversations with automatic routing, escalation, and timeout handling. This enables agents to ask questions and get answers from appropriate team members following organizational hierarchies.

## Key Concepts

### Hierarchical Conversations
- **Asker** → asks question
- **Routing Engine** → determines responder based on rules
- **Responder** → provides answer
- **Escalation** → if no answer, escalate to next level
- **Timeout Monitoring** → automatic follow-ups

### Conversation States
```
INITIATED → WAITING → ANSWERED
     ↓          ↓          ↓
TIMED_OUT → ESCALATED → CANCELLED
```

## Key Files

### 1. `routing_engine.py` - Smart Routing 🧭

**Purpose**: Determines which agent should respond based on routing rules

**Routing Logic**:
1. Query database for matching routing rules
2. Consider: asker role, question type, escalation level
3. Prioritize: squad-specific > org-level
4. Return: best matching responder

**Usage**:
```python
from backend.agents.interaction.routing_engine import RoutingEngine

engine = RoutingEngine(db)

# Get responder for question
responder = await engine.get_responder(
    squad_id=squad_id,
    asker_role="backend_developer",
    question_type="architecture",  # or "implementation", "default"
    escalation_level=0,  # First contact
    organization_id=org_id
)
```

**Key Methods**:
- `get_responder()` - Find agent to answer question
- `get_escalation_chain()` - Get complete escalation hierarchy
- `apply_template_to_squad()` - Apply routing template
- `validate_routing_config()` - Check configuration validity

---

### 2. `conversation_manager.py` - Lifecycle Manager 💬

**Purpose**: Manage complete conversation lifecycle from question to answer

**Workflow**:
```
1. initiate_question() → Create conversation, route to responder
2. acknowledge_conversation() → Responder confirms receipt
3. answer_conversation() → Responder provides answer
4. [Optional] escalate if timeout
5. [Optional] cancel if needed
```

**Usage**:
```python
from backend.agents.interaction.conversation_manager import ConversationManager

manager = ConversationManager(db)

# Backend dev asks question
conversation = await manager.initiate_question(
    asker_id=backend_dev_id,
    question_content="How should we handle rate limiting?",
    question_type="architecture",
    task_execution_id=execution_id
)
# Automatically:
# - Routes to tech lead (based on rules)
# - Sends question via message bus
# - Creates conversation record
# - Sets timeout
# - Triggers AI processing in background ⭐
```

**NEW (Oct 22, 2025)**: Automatic AI agent processing! 🤖

When a question is initiated, the conversation manager automatically triggers AI agent processing in the background. The responder agent will:
1. Receive the question
2. Process it with its LLM
3. Generate a response
4. Send answer back to asker

**Key Methods**:
- `initiate_question()` - Start new conversation
- `acknowledge_conversation()` - Confirm receipt
- `answer_conversation()` - Provide answer
- `cancel_conversation()` - Cancel conversation
- `get_conversation_timeline()` - Get full event history

---

### 3. `agent_message_handler.py` - AI Response Handler 🤖

**Purpose**: Process incoming messages and trigger AI agent responses

**What It Does**:
1. Receives message for an agent
2. Gets or creates Agno agent instance
3. Builds context (conversation history, RAG)
4. Invokes agent's LLM to generate response
5. Sends response back via message bus
6. Updates conversation state

**Integration**:
- Automatically triggered by `ConversationManager.initiate_question()`
- Runs in background (async task)
- Uses independent database session
- Graceful error handling

---

### 4. `escalation_service.py` - Escalation Logic 📈

**Purpose**: Handle escalations when responders don't answer

**Escalation Triggers**:
- Timeout reached
- Responder explicitly escalates
- Multiple failed attempts

**Escalation Chain**:
```
Level 0: Backend Dev → Tech Lead
Level 1: Tech Lead → Solution Architect
Level 2: Solution Architect → Project Manager
Level 3: Project Manager → Human
```

---

### 5. `timeout_monitor.py` - Timeout Monitor ⏰

**Purpose**: Monitor conversations and trigger actions on timeout

**Features**:
- Periodic checks (every 60 seconds)
- Automatic follow-ups
- Escalation triggers
- Configurable timeouts

**Configuration** (from `interaction_config.py`):
```python
timeouts:
  initial_timeout_seconds: 1800  # 30 minutes
  reminder_timeout_seconds: 3600  # 1 hour
  max_reminder_count: 2
```

---

### 6. `celery_config.py` & `celery_tasks.py` - Background Tasks

**Purpose**: Background task processing with Celery

**Tasks**:
- `process_timed_out_conversations` - Handle timeouts
- `send_reminder_messages` - Send reminders
- `cleanup_old_conversations` - Archive old convos

**Celery Beat Schedule**:
- Timeout monitoring: Every 5 minutes
- Reminder sending: Every 15 minutes
- Cleanup: Daily

---

## Routing Rules

### Rule Structure
```python
RoutingRule:
  asker_role: str          # Who is asking
  question_type: str       # Type of question
  escalation_level: int    # Escalation level
  responder_role: str      # Who should respond
  priority: int            # Rule priority (higher = preferred)
  squad_id: UUID           # Squad-specific (optional)
  organization_id: UUID    # Org-level (optional)
```

### Example Rules
```python
# Backend dev asks architecture question → Tech Lead
{
  "asker_role": "backend_developer",
  "question_type": "architecture",
  "escalation_level": 0,
  "responder_role": "tech_lead"
}

# If tech lead doesn't answer → Solution Architect
{
  "asker_role": "backend_developer",
  "question_type": "architecture",
  "escalation_level": 1,
  "responder_role": "solution_architect"
}
```

### Default Templates
Pre-configured routing templates available:
- **Standard Development Team**
- **Microservices Team**
- **AI/ML Team**
- **Startup Team** (flat hierarchy)

---

## Database Models

### Conversation
```python
id: UUID
initial_message_id: UUID
current_state: ConversationState
asker_id: UUID
current_responder_id: UUID
escalation_level: int
question_type: str
task_execution_id: UUID (optional)
acknowledged_at: datetime (optional)
resolved_at: datetime (optional)
timeout_at: datetime (optional)
conv_metadata: dict
```

### ConversationEvent
```python
id: UUID
conversation_id: UUID
event_type: str  # initiated, acknowledged, answered, escalated, cancelled
from_state: str
to_state: str
message_id: UUID (optional)
triggered_by_agent_id: UUID (optional)
event_data: dict
```

### RoutingRule
```python
id: UUID
squad_id: UUID (optional)
organization_id: UUID (optional)
asker_role: str
question_type: str
escalation_level: int
responder_role: str
specific_responder_id: UUID (optional)
priority: int
is_active: bool
```

---

## Common Workflows

### Workflow 1: Simple Question-Answer
```python
# 1. Backend dev asks question
conversation = await manager.initiate_question(
    asker_id=backend_dev_id,
    question_content="Should we use REST or GraphQL?",
    question_type="architecture"
)
# → Routes to tech lead
# → Sends message
# → Triggers AI processing ⭐

# 2. AI agent (tech lead) automatically:
# - Receives question
# - Processes with LLM
# - Generates response
# - Sends answer back

# 3. Conversation marked as ANSWERED
```

### Workflow 2: Escalation
```python
# 1. Question initiated
conversation = await manager.initiate_question(...)

# 2. Timeout reached (30 minutes)
# → timeout_monitor detects
# → Sends reminder

# 3. Still no answer (another 30 minutes)
# → Escalates to next level
# → Routes to solution architect

# 4. Solution architect answers
await manager.answer_conversation(
    conversation_id=conversation.id,
    responder_id=architect_id,
    answer_content="Use REST for simplicity..."
)
```

---

## Configuration (`configuration/interaction_config.py`)

### InteractionConfig
```python
config = InteractionConfig(
    enable_auto_acknowledgment=True,
    enable_auto_escalation=True,
    enable_timeout_monitoring=True,

    timeouts={
        "initial_timeout_seconds": 1800,  # 30 min
        "reminder_timeout_seconds": 3600, # 1 hour
        "max_reminder_count": 2
    },

    message_templates={
        "acknowledgment": "I've received your question...",
        "reminder": "Following up on...",
        "escalation": "This question has been escalated..."
    },

    escalation_rules={
        "max_escalation_level": 3,
        "auto_escalate_to_human": True
    }
)
```

---

## Testing

```python
@pytest.mark.asyncio
async def test_routing_engine(db):
    engine = RoutingEngine(db)

    responder = await engine.get_responder(
        squad_id=squad_id,
        asker_role="backend_developer",
        question_type="architecture",
        escalation_level=0
    )

    assert responder.role == "tech_lead"

@pytest.mark.asyncio
async def test_conversation_lifecycle(db):
    manager = ConversationManager(db)

    # Initiate
    conv = await manager.initiate_question(
        asker_id=asker_id,
        question_content="Test question?"
    )

    assert conv.current_state == "initiated"

    # Answer
    await manager.answer_conversation(
        conversation_id=conv.id,
        responder_id=responder_id,
        answer_content="Test answer"
    )

    # Verify
    conv_refreshed = await db.get(Conversation, conv.id)
    assert conv_refreshed.current_state == "answered"
```

---

## Performance Considerations

- **Routing queries**: Indexed by squad_id, asker_role, question_type
- **Timeout monitoring**: Batch processing every 5 minutes
- **Background tasks**: Celery for async processing
- **Database sessions**: Independent sessions for background tasks

---

## Related Documentation

- See `../CLAUDE.md` for agent architecture
- See `../communication/CLAUDE.md` for message bus
- See `../specialized/CLAUDE.md` for agent roles
- See `../../services/conversation_service.py` for user-agent conversations
