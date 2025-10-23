"""
Enhanced Agent Conversation Demo - See Actual AI Messages

This demo shows the ACTUAL messages exchanged between agents,
with real AI-generated responses from Agno-powered agents.

You'll see:
- Real AI responses from each agent
- Full conversation threads
- Thinking processes
- Decision-making in action
"""
import asyncio
import os
from uuid import uuid4

# Set production configuration
os.environ['MESSAGE_BUS'] = 'nats'
os.environ['NATS_URL'] = 'nats://localhost:4222'

from backend.agents.factory import AgentFactory
from backend.agents.communication.message_bus import get_message_bus


def print_separator(char="=", length=80):
    """Print a separator line"""
    print(char * length)


def print_message_box(title: str, content: str, color_code: str = ""):
    """Print a formatted message box"""
    reset_code = '\033[0m' if color_code else ''
    print()
    print_separator("─")
    print(f"{color_code}📨 {title}{reset_code}")
    print_separator("─")
    print()
    # Word wrap content
    words = content.split()
    line = ""
    for word in words:
        if len(line + word) > 75:
            print(f"   {line}")
            line = word + " "
        else:
            line += word + " "
    if line:
        print(f"   {line}")
    print()
    print_separator("─")
    print()


async def main():
    """Run the enhanced conversation demo"""

    print_separator()
    print("🤖 ENHANCED AGENT CONVERSATION DEMO")
    print("    See Real AI-Powered Agent Interactions")
    print_separator()
    print()

    # Connect to NATS
    print("📡 Connecting to NATS...")
    message_bus = get_message_bus()
    if hasattr(message_bus, 'connect'):
        await message_bus.connect()
        print("   ✅ Connected to NATS JetStream")
    print()

    execution_id = uuid4()

    # Create agents
    print("🤖 Creating AI-powered agents...")
    print()

    pm_id = uuid4()
    pm = AgentFactory.create_agent(
        agent_id=pm_id,
        role="project_manager",
        llm_provider="openai",
        llm_model="gpt-4o",
        temperature=0.7,
    )
    session_info = f" (session: {pm.session_id[:16]}...)" if pm.session_id else ""
    print(f"   ✅ Project Manager created{session_info}")

    backend_dev_id = uuid4()
    backend_dev = AgentFactory.create_agent(
        agent_id=backend_dev_id,
        role="backend_developer",
        llm_provider="openai",
        llm_model="gpt-4o",
        temperature=0.7,
    )
    session_info = f" (session: {backend_dev.session_id[:16]}...)" if backend_dev.session_id else ""
    print(f"   ✅ Backend Developer created{session_info}")

    tech_lead_id = uuid4()
    tech_lead = AgentFactory.create_agent(
        agent_id=tech_lead_id,
        role="tech_lead",
        llm_provider="openai",
        llm_model="gpt-4o",
        temperature=0.7,
    )
    session_info = f" (session: {tech_lead.session_id[:16]}...)" if tech_lead.session_id else ""
    print(f"   ✅ Tech Lead created{session_info}")

    print()
    print("🎬 Starting agent conversation...")
    print()

    # ====================
    # Conversation 1: PM analyzes requirement
    # ====================
    print_separator("=")
    print("🎬 SCENE 1: PM Analyzes Product Requirement")
    print_separator("=")
    print()

    product_requirement = """
Product Owner Request:

We need to add user authentication to our web application. Users should be able to:
1. Register with email and password
2. Log in securely
3. Stay logged in for 7 days
4. Have their sessions expire for security

This is critical for our MVP launch next month. Please analyze and create a plan.
"""

    print("📥 INPUT: Product Owner Request")
    print(product_requirement)
    print()

    print("⏳ PM is analyzing the requirement...")
    print()

    pm_response = await pm.process_message(
        message=f"""Analyze this product requirement and create a technical plan:

{product_requirement}

Provide:
1. High-level technical approach
2. Key components needed
3. Estimated effort (in hours)
4. Which team member should handle this
5. Priority level
""",
        context={
            "role": "project_manager",
            "task": "requirement_analysis",
        }
    )

    print_message_box(
        "📋 PM's ANALYSIS & PLAN",
        pm_response.content,
        "\033[94m"  # Blue
    )

    # Store PM's analysis for context
    pm_plan = pm_response.content

    # ====================
    # Conversation 2: PM delegates to Backend Dev
    # ====================
    print_separator("=")
    print("🎬 SCENE 2: PM Delegates Task to Backend Developer")
    print_separator("=")
    print()

    delegation_message = f"""Based on my analysis, I'm assigning you the authentication feature:

{pm_plan}

Task ID: AUTH-001
Priority: High
Estimated: 16 hours

Please acknowledge and let me know if you have any immediate questions or concerns about this assignment."""

    print("📤 PM → Backend Dev:")
    print(f"   Task: Implement authentication system")
    print(f"   Priority: High")
    print(f"   Estimate: 16 hours")
    print()

    # Send via message bus
    await pm.send_message(
        recipient_id=backend_dev_id,
        content=delegation_message,
        message_type="task_assignment",
        task_execution_id=execution_id,
    )

    print("⏳ Backend Developer is reviewing the task...")
    print()

    backend_response_1 = await backend_dev.process_message(
        message=delegation_message,
        context={
            "role": "backend_developer",
            "task_id": "AUTH-001",
            "from": "project_manager",
        }
    )

    print_message_box(
        "💻 BACKEND DEVELOPER'S RESPONSE",
        backend_response_1.content,
        "\033[92m"  # Green
    )

    # ====================
    # Conversation 3: Backend Dev asks Tech Lead
    # ====================
    print_separator("=")
    print("🎬 SCENE 3: Backend Developer Consults Tech Lead")
    print_separator("=")
    print()

    # Extract key question from backend dev's response or create one
    tech_question = """I'm implementing the JWT authentication system for AUTH-001.

I need your guidance on a few technical decisions:

1. JWT Signing Algorithm: Should I use HS256 (symmetric) or RS256 (asymmetric)?
   - HS256 is simpler but requires secret sharing
   - RS256 is more complex but better for microservices

2. Refresh Token Storage: Where should I store refresh tokens?
   - Database with user_id reference?
   - Redis for faster lookup?
   - What about security considerations?

3. Token Expiry: You mentioned 7-day sessions. Should I implement:
   - Long-lived access tokens (not recommended)?
   - Short access tokens (15min) + refresh tokens (7 days)?

This is for production deployment, so I want to make sure we follow best practices."""

    print("📤 Backend Dev → Tech Lead:")
    print("   Question: JWT implementation approach")
    print("   Context: AUTH-001 authentication system")
    print()

    # Send via message bus
    await backend_dev.send_message(
        recipient_id=tech_lead_id,
        content=tech_question,
        message_type="question",
        task_execution_id=execution_id,
    )

    print("⏳ Tech Lead is reviewing the question...")
    print()

    tech_lead_response = await tech_lead.process_message(
        message=tech_question,
        context={
            "role": "tech_lead",
            "task_id": "AUTH-001",
            "from": "backend_developer",
            "type": "architectural_guidance",
        }
    )

    print_message_box(
        "🎯 TECH LEAD'S GUIDANCE",
        tech_lead_response.content,
        "\033[93m"  # Yellow
    )

    # ====================
    # Conversation 4: Backend Dev implements with guidance
    # ====================
    print_separator("=")
    print("🎬 SCENE 4: Backend Developer Starts Implementation")
    print_separator("=")
    print()

    implementation_context = f"""Now that I have Tech Lead's guidance:

{tech_lead_response.content}

I'm starting implementation. Let me outline my approach and first steps."""

    print("⏳ Backend Developer is planning implementation...")
    print()

    backend_response_2 = await backend_dev.process_message(
        message=implementation_context,
        context={
            "role": "backend_developer",
            "task_id": "AUTH-001",
            "phase": "implementation_planning",
        }
    )

    print_message_box(
        "💻 BACKEND DEVELOPER'S IMPLEMENTATION PLAN",
        backend_response_2.content,
        "\033[92m"  # Green
    )

    # ====================
    # Conversation 5: Backend Dev updates PM
    # ====================
    print_separator("=")
    print("🎬 SCENE 5: Backend Developer Updates PM on Progress")
    print_separator("=")
    print()

    status_request = """I've made good progress on AUTH-001. Here's where I'm at:

Completed:
- Set up JWT library (python-jose)
- Implemented RS256 key pair generation
- Created user registration endpoint
- Created login endpoint with JWT generation
- Implemented authentication middleware

In Progress:
- Refresh token mechanism (using Redis)
- Unit tests for auth endpoints

Can you review my progress and let me know if you need any updates for stakeholders?"""

    print("📤 Backend Dev → PM:")
    print("   Status update on AUTH-001")
    print("   Progress: ~60%")
    print()

    # Send via message bus
    await backend_dev.send_message(
        recipient_id=pm_id,
        content=status_request,
        message_type="status_update",
        task_execution_id=execution_id,
    )

    print("⏳ PM is reviewing the progress...")
    print()

    pm_response_2 = await pm.process_message(
        message=status_request,
        context={
            "role": "project_manager",
            "task_id": "AUTH-001",
            "from": "backend_developer",
            "type": "status_update",
        }
    )

    print_message_box(
        "📋 PM'S RESPONSE TO PROGRESS UPDATE",
        pm_response_2.content,
        "\033[94m"  # Blue
    )

    # ====================
    # Summary
    # ====================
    print_separator("=")
    print("📊 CONVERSATION SUMMARY")
    print_separator("=")
    print()

    print("✅ Conversations Completed:")
    print()
    print("   1. PM analyzed product requirement")
    print("      → Generated technical plan and task assignment")
    print()
    print("   2. PM delegated to Backend Developer")
    print("      → Backend Dev acknowledged and accepted task")
    print()
    print("   3. Backend Dev consulted Tech Lead")
    print("      → Tech Lead provided architectural guidance")
    print()
    print("   4. Backend Dev planned implementation")
    print("      → Created detailed implementation approach")
    print()
    print("   5. Backend Dev updated PM on progress")
    print("      → PM acknowledged progress and provided feedback")
    print()

    print("📨 Messages Exchanged: 5")
    print("🤖 Agents Involved: 3 (PM, Backend Dev, Tech Lead)")
    print("🎯 Task: AUTH-001 (JWT Authentication)")
    print()

    # Show NATS stats
    if hasattr(message_bus, 'get_stats'):
        stats = await message_bus.get_stats()
        print("📊 NATS JetStream Stats:")
        print(f"   • Total messages in stream: {stats.get('total_messages', 0)}")
        print(f"   • Stream: {stats.get('stream_name', 'unknown')}")
        print()

    # Cleanup
    if hasattr(message_bus, 'disconnect'):
        await message_bus.disconnect()
        print("✅ Disconnected from NATS")
    print()

    print_separator("=")
    print("🎉 DEMO COMPLETE!")
    print_separator("=")
    print()
    print("✨ You just witnessed:")
    print("   • Real AI-powered agent conversations")
    print("   • Hierarchical communication (PM → Dev → Tech Lead)")
    print("   • Context preservation across messages")
    print("   • Collaborative problem-solving")
    print("   • Professional software development workflow")
    print()
    print("🚀 Your Agno agents are thinking, deciding, and collaborating!")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
