# End-to-End AI Conversation Flow - Implementation Plan

**Feature:** Item 1.2 from PRODUCT_ROADMAP.md
**Goal:** Wire LLMs into the conversation flow so agents actually "think" and respond intelligently
**Status:** Planning Phase
**Estimated Time:** 3-5 days

---

## 🎯 Overview

### Current State (The Problem)

```
Backend Dev sends question
  ↓
Routing engine determines: Tech Lead
  ↓
Message stored in DB
  ✗ No actual AI response!
```

**What's missing:**
- Agents don't process incoming messages
- No LLM is called to generate responses
- Conversations remain in "waiting" state indefinitely
- No actual intelligence - just routing

### Target State (The Solution)

```
Backend Dev sends question
  ↓
Routing engine determines: Tech Lead
  ↓
Tech Lead agent receives message
  ↓
Tech Lead's BaseAgent.process_message() calls LLM (Claude)
  ↓
LLM generates thoughtful response with reasoning
  ↓
Tech Lead sends response via message bus
  ↓
Conversation marked as answered
  ↓
Backend Dev receives the answer
```

**What we'll achieve:**
- ✅ Agents actively process incoming messages
- ✅ LLM generates intelligent responses based on agent role
- ✅ Conversation context included in prompts
- ✅ Multi-turn conversations with memory
- ✅ Automatic state transitions (initiated → waiting → answered)
- ✅ Visible agent "thinking" process (optional)

---

## 📋 Implementation Steps

### Phase 1: Wire Message Bus to Agent Processing (Day 1)

**Objective:** When a message is sent to an agent, trigger that agent to process it.

#### Step 1.1: Create Agent Message Handler

**File:** `backend/agents/interaction/agent_message_handler.py` (NEW)

**Purpose:** Service that listens for messages and dispatches them to the appropriate agent for processing.

**Implementation:**
```python
"""
Agent Message Handler

Processes incoming messages and triggers agent responses.
"""
from typing import Optional
from uuid import UUID
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models import SquadMember, AgentMessage
from backend.agents.factory import AgentFactory
from backend.agents.communication.message_bus import get_message_bus
from backend.agents.interaction.conversation_manager import ConversationManager


class AgentMessageHandler:
    """
    Handles incoming messages and triggers agent processing.

    This is the glue between the message bus and the agent processing logic.
    When an agent receives a message, this handler:
    1. Retrieves the agent's configuration
    2. Creates/retrieves the BaseAgent instance
    3. Calls process_message() to get LLM response
    4. Sends the response back via message bus
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.message_bus = get_message_bus()
        self.conversation_manager = ConversationManager(db)
        self._processing_lock = asyncio.Lock()

    async def process_incoming_message(
        self,
        message_id: UUID,
        recipient_id: UUID,
        sender_id: UUID,
        content: str,
        message_type: str,
        conversation_id: Optional[UUID] = None
    ) -> None:
        """
        Process an incoming message and generate agent response.

        Args:
            message_id: ID of the message to process
            recipient_id: Agent who should respond (SquadMember ID)
            sender_id: Agent who sent the message (SquadMember ID)
            content: Message content (the question/request)
            message_type: Type of message (question, task_assignment, etc.)
            conversation_id: Optional conversation ID for context
        """

        # Only process certain message types
        if message_type not in ['question', 'task_assignment', 'code_review_request']:
            return

        try:
            # Get recipient agent configuration
            stmt = select(SquadMember).where(SquadMember.id == recipient_id)
            result = await self.db.execute(stmt)
            agent_member = result.scalar_one_or_none()

            if not agent_member:
                print(f"Agent not found: {recipient_id}")
                return

            # Create or retrieve agent instance
            agent = AgentFactory.create_agent(
                agent_id=recipient_id,
                role=agent_member.role,
                llm_provider=agent_member.llm_provider or "openai",
                llm_model=agent_member.llm_model or "gpt-4",
                specialization=agent_member.specialization,
                temperature=0.7
            )

            # Build conversation context
            context = await self._build_conversation_context(
                conversation_id=conversation_id,
                agent_id=recipient_id
            )

            # Process message with agent's LLM
            print(f"🤖 {agent_member.role} is thinking...")
            response = await agent.process_message(
                message=content,
                context=context
            )

            # Send response back via message bus
            await self.message_bus.send_message(
                sender_id=recipient_id,
                recipient_id=sender_id,
                content=response.content,
                message_type="answer",
                metadata={
                    "thinking": response.thinking if hasattr(response, 'thinking') else None,
                    "confidence": response.metadata.get("confidence") if hasattr(response, 'metadata') else None,
                    "conversation_id": str(conversation_id) if conversation_id else None
                },
                task_execution_id=None,
                db=self.db
            )

            # Update conversation state to answered
            if conversation_id:
                await self.conversation_manager.answer_conversation(
                    conversation_id=conversation_id,
                    responder_id=recipient_id,
                    answer_content=response.content
                )

            print(f"✅ {agent_member.role} responded successfully")

        except Exception as e:
            print(f"❌ Error processing message: {e}")
            import traceback
            traceback.print_exc()

    async def _build_conversation_context(
        self,
        conversation_id: Optional[UUID],
        agent_id: UUID
    ) -> dict:
        """
        Build context from conversation history.

        Args:
            conversation_id: Conversation ID to get history from
            agent_id: Agent ID for role-specific context

        Returns:
            Context dictionary with conversation history
        """
        if not conversation_id:
            return {}

        # Get conversation timeline
        timeline = await self.conversation_manager.get_conversation_timeline(conversation_id)

        # Get agent's role for context
        stmt = select(SquadMember).where(SquadMember.id == agent_id)
        result = await self.db.execute(stmt)
        agent = result.scalar_one_or_none()

        return {
            "conversation_id": str(conversation_id),
            "agent_role": agent.role if agent else "unknown",
            "conversation_state": timeline.get("current_state"),
            "question_type": timeline.get("question_type"),
            "escalation_level": timeline.get("escalation_level", 0),
            "conversation_history": timeline.get("events", [])
        }
```

**Tasks:**
- [ ] Create `backend/agents/interaction/agent_message_handler.py`
- [ ] Implement `AgentMessageHandler` class
- [ ] Implement `process_incoming_message()` method
- [ ] Implement `_build_conversation_context()` method
- [ ] Add error handling and logging

**Testing:**
```python
# Test that handler processes messages
handler = AgentMessageHandler(db)
await handler.process_incoming_message(
    message_id=message_id,
    recipient_id=tech_lead_id,
    sender_id=backend_dev_id,
    content="Should we use Redis or Memcached for caching?",
    message_type="question",
    conversation_id=conversation_id
)
# Expect: Tech Lead agent responds with intelligent answer
```

---

#### Step 1.2: Integrate Handler with ConversationManager

**File:** `backend/agents/interaction/conversation_manager.py` (MODIFY)

**Purpose:** Trigger agent processing when a conversation is initiated.

**Changes:**

```python
# Add at top of file
from backend.agents.interaction.agent_message_handler import AgentMessageHandler

# Modify initiate_question() method
async def initiate_question(
    self,
    asker_id: UUID,
    question_content: str,
    question_type: str = "default",
    task_execution_id: Optional[UUID] = None,
    metadata: Optional[dict] = None
) -> Conversation:
    """
    Initiate a new question conversation.

    NEW: Now triggers agent processing automatically.
    """
    # ... existing code to create conversation ...

    # NEW: Trigger agent processing in background
    handler = AgentMessageHandler(self.db)

    # Use asyncio.create_task to process in background
    # (don't await - let it process asynchronously)
    asyncio.create_task(
        handler.process_incoming_message(
            message_id=message.id,
            recipient_id=responder.id,
            sender_id=asker_id,
            content=question_content,
            message_type="question",
            conversation_id=conversation.id
        )
    )

    return conversation
```

**Tasks:**
- [ ] Import `AgentMessageHandler` in `conversation_manager.py`
- [ ] Add background task to trigger agent processing in `initiate_question()`
- [ ] Ensure conversation is committed before triggering processing
- [ ] Add logging for debugging

**Testing:**
```python
# Test that initiating a question triggers agent response
conversation = await conv_manager.initiate_question(
    asker_id=backend_dev_id,
    question_content="How should I structure the API?",
    question_type="implementation"
)

# Wait a few seconds for LLM to respond
await asyncio.sleep(5)

# Check that conversation is now answered
await db.refresh(conversation)
assert conversation.current_state == "answered"
```

---

### Phase 2: Enhance BaseAgent Context Handling (Day 2)

**Objective:** Make agents aware of their role and conversation context when generating responses.

#### Step 2.1: Update BaseAgent to Accept Rich Context

**File:** `backend/agents/base_agent.py` (MODIFY)

**Changes:**

```python
async def process_message(
    self,
    message: str,
    context: Optional[dict] = None  # NEW: Accept context
) -> AgentResponse:
    """
    Process a message and generate a response.

    NEW: Now uses conversation context to generate better responses.

    Args:
        message: The message/question to process
        context: Optional context including:
            - conversation_id: Current conversation ID
            - agent_role: This agent's role
            - conversation_history: Previous messages
            - question_type: Type of question (implementation, architecture, etc.)
            - escalation_level: Current escalation level
    """

    # Build enhanced system prompt with context
    system_prompt = self._build_contextual_prompt(context or {})

    # Build conversation messages with history
    conversation_messages = self._build_conversation_messages(
        message=message,
        context=context or {}
    )

    # ... rest of existing implementation ...


def _build_contextual_prompt(self, context: dict) -> str:
    """
    Build system prompt enhanced with conversation context.

    Args:
        context: Context dictionary

    Returns:
        Enhanced system prompt
    """
    base_prompt = self.system_prompt

    # Add role-specific context
    if context.get("agent_role"):
        base_prompt += f"\n\nYour role: {context['agent_role']}"

    # Add question type context
    if context.get("question_type"):
        base_prompt += f"\n\nQuestion type: {context['question_type']}"

    # Add escalation context
    if context.get("escalation_level", 0) > 0:
        base_prompt += f"\n\nNote: This question has been escalated to you from a lower level. Provide expert-level guidance."

    return base_prompt


def _build_conversation_messages(
    self,
    message: str,
    context: dict
) -> List[ConversationMessage]:
    """
    Build conversation messages including history.

    Args:
        message: Current message
        context: Context with conversation history

    Returns:
        List of conversation messages for LLM
    """
    messages = []

    # Add previous conversation events if available
    if context.get("conversation_history"):
        for event in context["conversation_history"][:5]:  # Limit to last 5
            event_type = event.get("event_type")
            if event_type in ["initiated", "answered"]:
                # Add event to conversation context
                role = "user" if event_type == "initiated" else "assistant"
                messages.append(ConversationMessage(
                    role=role,
                    content=event.get("event_data", {}).get("content", "")
                ))

    # Add current message
    messages.append(ConversationMessage(
        role="user",
        content=message
    ))

    return messages
```

**Tasks:**
- [ ] Update `process_message()` to accept context parameter
- [ ] Implement `_build_contextual_prompt()` method
- [ ] Implement `_build_conversation_messages()` with history
- [ ] Test with different question types and escalation levels

**Testing:**
```python
# Test context awareness
agent = AgentFactory.create_agent(
    agent_id=tech_lead_id,
    role="tech_lead",
    llm_provider="anthropic",
    llm_model="claude-3-5-sonnet-20241022"
)

response = await agent.process_message(
    message="How should I cache session data?",
    context={
        "agent_role": "tech_lead",
        "question_type": "implementation",
        "escalation_level": 0
    }
)

# Expect: Response includes tech lead perspective and implementation details
assert "redis" in response.content.lower() or "memcached" in response.content.lower()
```

---

### Phase 3: Add Response Streaming (Day 3) - Optional but Impressive

**Objective:** Stream LLM responses in real-time for better UX.

#### Step 3.1: Add Streaming Support to BaseAgent

**File:** `backend/agents/base_agent.py` (MODIFY)

**Changes:**

```python
async def process_message_streaming(
    self,
    message: str,
    context: Optional[dict] = None,
    on_token: Optional[Callable[[str], None]] = None
) -> AgentResponse:
    """
    Process message with streaming response.

    Args:
        message: Message to process
        context: Optional context
        on_token: Callback for each token (for streaming)

    Returns:
        Complete agent response
    """

    # Build prompt and messages
    system_prompt = self._build_contextual_prompt(context or {})
    conversation_messages = self._build_conversation_messages(message, context or {})

    # Stream response
    full_response = ""

    if self.llm_provider == "anthropic":
        # Anthropic streaming
        async with self.anthropic_client.messages.stream(
            model=self.llm_model,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": m.role, "content": m.content} for m in conversation_messages]
        ) as stream:
            async for text in stream.text_stream:
                full_response += text
                if on_token:
                    on_token(text)

    elif self.llm_provider == "openai":
        # OpenAI streaming
        stream = await self.openai_client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                *[{"role": m.role, "content": m.content} for m in conversation_messages]
            ],
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                full_response += token
                if on_token:
                    on_token(token)

    return AgentResponse(
        content=full_response,
        thinking=None,
        action_items=[]
    )
```

**Tasks:**
- [ ] Implement `process_message_streaming()` method
- [ ] Add streaming support for Anthropic (Claude)
- [ ] Add streaming support for OpenAI (GPT-4)
- [ ] Add streaming support for Groq (optional)
- [ ] Create callback mechanism for tokens

#### Step 3.2: Stream to Frontend via SSE

**File:** `backend/agents/interaction/agent_message_handler.py` (MODIFY)

**Changes:**

```python
async def process_incoming_message(
    self,
    message_id: UUID,
    recipient_id: UUID,
    sender_id: UUID,
    content: str,
    message_type: str,
    conversation_id: Optional[UUID] = None
) -> None:
    """Process message with streaming."""

    # ... setup code ...

    # Stream response
    streamed_response = ""

    def on_token(token: str):
        """Callback for each token - broadcast via SSE"""
        nonlocal streamed_response
        streamed_response += token

        # Broadcast to SSE (if task_execution_id available)
        # This shows "agent is typing..." in real-time
        asyncio.create_task(
            self.message_bus._broadcast_to_sse(
                execution_id=task_execution_id,
                message=AgentMessageResponse(
                    id=uuid4(),
                    task_execution_id=task_execution_id,
                    sender_id=recipient_id,
                    recipient_id=sender_id,
                    content=streamed_response,  # Partial response
                    message_type="answer_streaming",
                    message_metadata={"streaming": True},
                    created_at=datetime.utcnow()
                ),
                sender_id=recipient_id,
                recipient_id=sender_id,
                content=streamed_response,
                message_type="answer_streaming",
                metadata={"streaming": True}
            )
        )

    # Process with streaming
    response = await agent.process_message_streaming(
        message=content,
        context=context,
        on_token=on_token
    )

    # ... rest of code ...
```

**Tasks:**
- [ ] Modify `process_incoming_message()` to use streaming
- [ ] Broadcast partial responses via SSE
- [ ] Send final response when complete
- [ ] Handle errors during streaming

---

### Phase 4: Multi-Turn Conversations (Day 4)

**Objective:** Support follow-up questions and extended conversations.

#### Step 4.1: Store Conversation History in Context

**File:** `backend/agents/interaction/agent_message_handler.py` (MODIFY)

**Changes:**

```python
async def _build_conversation_context(
    self,
    conversation_id: Optional[UUID],
    agent_id: UUID
) -> dict:
    """
    Build rich context from conversation history.

    NEW: Includes all messages in the conversation for context.
    """
    if not conversation_id:
        return {}

    # Get conversation
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await self.db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        return {}

    # Get all messages in this conversation
    stmt = select(AgentMessage).where(
        AgentMessage.conversation_id == conversation_id
    ).order_by(AgentMessage.created_at)
    result = await self.db.execute(stmt)
    messages = result.scalars().all()

    # Build conversation history
    history = []
    for msg in messages:
        history.append({
            "role": "assistant" if msg.sender_id == agent_id else "user",
            "content": msg.content,
            "message_type": msg.message_type,
            "created_at": msg.created_at.isoformat()
        })

    # Get agent details
    stmt = select(SquadMember).where(SquadMember.id == agent_id)
    result = await self.db.execute(stmt)
    agent = result.scalar_one_or_none()

    return {
        "conversation_id": str(conversation_id),
        "agent_role": agent.role if agent else "unknown",
        "question_type": conversation.question_type,
        "escalation_level": conversation.escalation_level,
        "conversation_history": history,
        "is_follow_up": len(history) > 1
    }
```

**Tasks:**
- [ ] Enhance `_build_conversation_context()` to include all messages
- [ ] Link messages to conversations (update AgentMessage model if needed)
- [ ] Test with multi-turn conversations
- [ ] Verify context is maintained across turns

**Testing:**
```python
# Test multi-turn conversation
# Turn 1
conv = await conv_manager.initiate_question(
    asker_id=backend_dev_id,
    question_content="How should I structure the payment service?",
    question_type="implementation"
)

await asyncio.sleep(5)  # Wait for response

# Turn 2 - Follow-up question
await message_bus.send_message(
    sender_id=backend_dev_id,
    recipient_id=tech_lead_id,
    content="Should I use Stripe or PayPal?",
    message_type="question",
    metadata={"conversation_id": str(conv.id)},
    db=db
)

# Trigger processing
await handler.process_incoming_message(...)

# Expect: Response references previous context about payment service
```

---

### Phase 5: Integration & Testing (Day 5)

**Objective:** End-to-end testing and integration with existing systems.

#### Step 5.1: Update E2E Test

**File:** `test_mvp_e2e.py` (MODIFY)

**Changes:**

```python
# Step 6: Test Conversation Flow with Real AI Responses
print_step(6, "Test Conversation Flow with Real AI")

backend_dev_id = agents.get('backend_developer')
tech_lead_id = agents.get('tech_lead')

if backend_dev_id and tech_lead_id:
    conv_manager = ConversationManager(db)

    print("\n💬 Creating conversation: Backend Dev → Tech Lead")
    print("   Question: Should we use bcrypt or argon2 for password hashing?")

    conversation = await conv_manager.initiate_question(
        asker_id=backend_dev_id,
        question_content="Should we use bcrypt or argon2 for password hashing?",
        question_type="implementation",
        metadata={
            "task": "User authentication API",
            "concern": "Security best practices"
        }
    )

    print(f"  ✓ Conversation created: {conversation.id}")
    print(f"  State: {conversation.current_state}")

    # Wait for agent to process and respond
    print("\n⏳ Waiting for Tech Lead to think and respond...")

    max_wait = 30  # seconds
    for i in range(max_wait):
        await asyncio.sleep(1)
        await db.refresh(conversation)

        if conversation.current_state == "answered":
            break

        if i % 5 == 0:
            print(f"  Still waiting... ({i}s elapsed)")

    # Check final state
    if conversation.current_state == "answered":
        print(f"  ✅ Conversation answered in {i}s!")

        # Get the answer
        stmt = select(AgentMessage).where(
            AgentMessage.conversation_id == conversation.id,
            AgentMessage.message_type == "answer"
        ).order_by(AgentMessage.created_at.desc())
        result = await db.execute(stmt)
        answer_msg = result.scalar_one_or_none()

        if answer_msg:
            print(f"\n📝 Tech Lead's Answer:")
            print(f"  {answer_msg.content[:200]}...")
    else:
        print(f"  ⚠️  Conversation still in state: {conversation.current_state}")
```

**Tasks:**
- [ ] Update E2E test to wait for AI responses
- [ ] Add timeout handling (max 30 seconds)
- [ ] Verify answer content makes sense
- [ ] Test with different question types

#### Step 5.2: Create Demo Script

**File:** `demo_ai_conversation.py` (NEW)

**Purpose:** Interactive demo showing AI agents responding intelligently.

```python
"""
AI Conversation Demo

Demonstrates end-to-end AI conversation flow with real LLM responses.

Run:
    DEBUG=False python demo_ai_conversation.py
"""
import asyncio
from sqlalchemy import select

from backend.core.database import AsyncSessionLocal
from backend.models import Squad, SquadMember
from backend.services.template_service import TemplateService
from backend.services.squad_service import SquadService
from backend.agents.interaction.conversation_manager import ConversationManager


async def main():
    print("🤖 Agent Squad - AI Conversation Demo")
    print("=" * 80)

    async with AsyncSessionLocal() as db:
        # ... setup squad from template ...

        # Create conversation manager
        conv_manager = ConversationManager(db)

        # Demo 1: Implementation Question
        print("\n📝 Demo 1: Backend Dev asks Tech Lead about caching")
        conversation = await conv_manager.initiate_question(
            asker_id=backend_dev_id,
            question_content="How should I implement session caching for our API? We expect 10,000 concurrent users.",
            question_type="implementation"
        )

        print("⏳ Tech Lead is thinking...")
        await wait_for_answer(db, conversation)
        print_answer(db, conversation)

        # Demo 2: Architecture Question
        print("\n📝 Demo 2: Tech Lead asks Solution Architect")
        conversation = await conv_manager.initiate_question(
            asker_id=tech_lead_id,
            question_content="Should we use microservices or monolith for the initial MVP?",
            question_type="architecture"
        )

        print("⏳ Solution Architect is thinking...")
        await wait_for_answer(db, conversation)
        print_answer(db, conversation)


async def wait_for_answer(db, conversation, max_wait=30):
    """Wait for conversation to be answered."""
    for i in range(max_wait):
        await asyncio.sleep(1)
        await db.refresh(conversation)
        if conversation.current_state == "answered":
            return

    raise TimeoutError("Agent did not respond in time")


def print_answer(db, conversation):
    """Print the answer from the conversation."""
    # Get answer message
    stmt = select(AgentMessage).where(
        AgentMessage.conversation_id == conversation.id,
        AgentMessage.message_type == "answer"
    ).order_by(AgentMessage.created_at.desc())
    result = await db.execute(stmt)
    answer = result.scalar_one_or_none()

    if answer:
        print(f"\n✅ Answer:")
        print(f"{answer.content}\n")


if __name__ == "__main__":
    asyncio.run(main())
```

**Tasks:**
- [ ] Create `demo_ai_conversation.py`
- [ ] Add 3-5 demo scenarios
- [ ] Show different question types
- [ ] Show escalation in action

---

## 🧪 Testing Strategy

### Unit Tests

**File:** `backend/tests/test_agents/test_agent_message_handler.py` (NEW)

```python
import pytest
from uuid import uuid4

from backend.agents.interaction.agent_message_handler import AgentMessageHandler


@pytest.mark.asyncio
async def test_process_incoming_message(db_session, mock_agents):
    """Test that handler processes messages and generates responses."""
    handler = AgentMessageHandler(db_session)

    # Create test message
    await handler.process_incoming_message(
        message_id=uuid4(),
        recipient_id=mock_agents['tech_lead'],
        sender_id=mock_agents['backend_dev'],
        content="How should I handle errors?",
        message_type="question"
    )

    # Verify response was generated
    # (check message bus for answer message)


@pytest.mark.asyncio
async def test_conversation_context_building(db_session, mock_conversation):
    """Test that context includes conversation history."""
    handler = AgentMessageHandler(db_session)

    context = await handler._build_conversation_context(
        conversation_id=mock_conversation.id,
        agent_id=mock_agents['tech_lead']
    )

    assert context['conversation_id'] == str(mock_conversation.id)
    assert context['agent_role'] == 'tech_lead'
    assert len(context['conversation_history']) > 0
```

**Tasks:**
- [ ] Create test file for AgentMessageHandler
- [ ] Test message processing
- [ ] Test context building
- [ ] Test error handling
- [ ] Mock LLM calls (use `pytest-mock`)

### Integration Tests

**File:** `backend/tests/test_agents/test_e2e_ai_conversation.py` (NEW)

```python
@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_ai_conversation_flow(db_session, software_dev_squad):
    """Test complete conversation flow with LLM responses."""

    # This test actually calls LLMs - mark as integration test
    # Requires API keys to be set

    conv_manager = ConversationManager(db_session)

    # Initiate question
    conversation = await conv_manager.initiate_question(
        asker_id=software_dev_squad.backend_dev_id,
        question_content="What's the best way to implement authentication?",
        question_type="implementation"
    )

    # Wait for response (with timeout)
    max_wait = 30
    for _ in range(max_wait):
        await asyncio.sleep(1)
        await db_session.refresh(conversation)
        if conversation.current_state == "answered":
            break

    # Verify
    assert conversation.current_state == "answered"

    # Check answer exists
    answer_msg = await get_answer_message(db_session, conversation.id)
    assert answer_msg is not None
    assert len(answer_msg.content) > 100  # Should be substantial
```

**Tasks:**
- [ ] Create integration test file
- [ ] Test with real LLM calls (mark as @integration)
- [ ] Test timeout scenarios
- [ ] Test multi-turn conversations

---

## 📊 Success Criteria

### Functional Requirements ✅

- [ ] Agent receives message and processes it automatically
- [ ] LLM is called with appropriate context
- [ ] Response is generated and sent back to asker
- [ ] Conversation state transitions correctly (initiated → answered)
- [ ] Multi-turn conversations maintain context
- [ ] Different question types route to appropriate agents
- [ ] Escalation works with AI responses

### Performance Requirements ✅

- [ ] Response time < 10 seconds for simple questions
- [ ] Response time < 20 seconds for complex questions
- [ ] Streaming shows first token < 2 seconds
- [ ] System handles 10+ concurrent conversations
- [ ] LLM costs < $0.05 per conversation

### Quality Requirements ✅

- [ ] Responses are relevant to the question
- [ ] Responses match the agent's role/expertise
- [ ] No hallucinations (answers are factual)
- [ ] Conversation context is maintained across turns
- [ ] Error messages are clear when LLM fails

---

## 🔍 Monitoring & Debugging

### Logging

Add comprehensive logging:

```python
# In agent_message_handler.py
import logging

logger = logging.getLogger(__name__)

async def process_incoming_message(...):
    logger.info(f"Processing message {message_id} for agent {recipient_id}")

    try:
        # ... processing ...
        logger.info(f"Agent {recipient_id} responded successfully in {elapsed}s")
    except Exception as e:
        logger.error(f"Error processing message {message_id}: {e}", exc_info=True)
```

### Metrics to Track

- **Response time** - Time from question to answer
- **LLM token usage** - Track costs per conversation
- **Success rate** - % of questions that get answered
- **Error rate** - % of failed LLM calls
- **Context size** - Number of messages in conversation history

---

## 💰 Cost Estimation

### LLM Costs per Conversation

**Claude 3.5 Sonnet (Tech Lead, Architect, PM):**
- Input: ~500 tokens (prompt + context) × $0.003/1K = $0.0015
- Output: ~300 tokens × $0.015/1K = $0.0045
- **Total: ~$0.006 per response**

**GPT-4 (Developers, QA):**
- Input: ~500 tokens × $0.01/1K = $0.005
- Output: ~300 tokens × $0.03/1K = $0.009
- **Total: ~$0.014 per response**

**Average per Conversation:**
- Assuming 2 turns average, mix of agents
- **~$0.02 - $0.04 per conversation**

**Monthly at Scale:**
- 1,000 conversations/month = $20 - $40
- 10,000 conversations/month = $200 - $400
- 100,000 conversations/month = $2,000 - $4,000

---

## 🚀 Deployment Checklist

### Before Deploying

- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] E2E test with real LLMs passing
- [ ] Demo script working
- [ ] Error handling tested
- [ ] Logging configured
- [ ] Metrics tracked
- [ ] Cost monitoring in place

### Configuration

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Control which LLM to use
DEFAULT_LLM_PROVIDER=anthropic
DEFAULT_LLM_MODEL=claude-3-5-sonnet-20241022

# Optional: Streaming
ENABLE_STREAMING=true

# Optional: Response timeout
AGENT_RESPONSE_TIMEOUT=30
```

---

## 📋 Task Breakdown & Estimates

| Task | Description | Time | Status |
|------|-------------|------|--------|
| **Phase 1** | Wire Message Bus to Agent Processing | | |
| 1.1 | Create AgentMessageHandler | 3h | ⏳ |
| 1.2 | Integrate with ConversationManager | 2h | ⏳ |
| **Phase 2** | Enhance BaseAgent Context | | |
| 2.1 | Update process_message() for context | 3h | ⏳ |
| 2.2 | Implement contextual prompts | 2h | ⏳ |
| **Phase 3** | Response Streaming (Optional) | | |
| 3.1 | Add streaming to BaseAgent | 3h | ⏳ |
| 3.2 | Stream to frontend via SSE | 2h | ⏳ |
| **Phase 4** | Multi-Turn Conversations | | |
| 4.1 | Store conversation history | 2h | ⏳ |
| 4.2 | Include history in context | 2h | ⏳ |
| **Phase 5** | Testing & Integration | | |
| 5.1 | Unit tests | 4h | ⏳ |
| 5.2 | Integration tests | 3h | ⏳ |
| 5.3 | E2E test updates | 2h | ⏳ |
| 5.4 | Demo script | 2h | ⏳ |
| **Total** | | **30h** (~4-5 days) | |

---

## 🎯 Next Steps

1. **Review this plan** - Discuss any concerns or questions
2. **Set up development environment** - Ensure API keys are configured
3. **Start with Phase 1** - Create AgentMessageHandler
4. **Iterate quickly** - Test each phase before moving to next
5. **Demo early** - Show working AI responses ASAP

---

## 📚 References

- [BaseAgent Documentation](backend/agents/CLAUDE.md)
- [Conversation Manager](backend/agents/interaction/conversation_manager.py:1)
- [Message Bus](backend/agents/communication/message_bus.py:1)
- [Template System Guide](TEMPLATE_SYSTEM_GUIDE.md)
- [E2E Test](test_mvp_e2e.py:1)

---

**Ready to implement?** Start with Phase 1 and we'll iterate from there! 🚀
