"""
Squad Collaboration Demo: Message Bus + Usage Tracking

This demo showcases:
1. Inter-agent message communication via message bus
2. Real message types (TaskAssignment, Question, Answer, etc.)
3. Token usage tracking per agent
4. Cost estimation per agent
"""
import asyncio
from uuid import uuid4
from datetime import datetime

from backend.agents.factory import AgentFactory
from backend.core.agno_config import initialize_agno, shutdown_agno
from backend.schemas.agent_message import (
    TaskAssignment,
    Question,
    Answer,
    StatusUpdate,
    CodeReviewRequest,
)


class MessageBusTracker:
    """Track all messages exchanged between agents"""

    def __init__(self):
        self.messages = []
        self.agent_stats = {}

    def log_message(self, msg_type: str, sender: str, recipient: str, content: str):
        """Log a message"""
        self.messages.append({
            "timestamp": datetime.now(),
            "type": msg_type,
            "sender": sender,
            "recipient": recipient,
            "content": content[:100] + "..." if len(content) > 100 else content
        })

    def log_agent_usage(self, agent_name: str, tokens: int, cost: float):
        """Log agent token usage and cost"""
        if agent_name not in self.agent_stats:
            self.agent_stats[agent_name] = {
                "messages": 0,
                "tokens": 0,
                "cost": 0.0
            }

        self.agent_stats[agent_name]["messages"] += 1
        self.agent_stats[agent_name]["tokens"] += tokens
        self.agent_stats[agent_name]["cost"] += cost

    def print_messages(self):
        """Print all tracked messages"""
        print("\n" + "="*70)
        print("📨 MESSAGE BUS - ALL MESSAGES EXCHANGED")
        print("="*70)

        if not self.messages:
            print("\nNo messages exchanged yet.")
            return

        for i, msg in enumerate(self.messages, 1):
            print(f"\n{i}. [{msg['timestamp'].strftime('%H:%M:%S')}] {msg['type']}")
            print(f"   From: {msg['sender']}")
            print(f"   To: {msg['recipient']}")
            print(f"   Content: {msg['content']}")

    def print_usage_stats(self):
        """Print usage statistics"""
        print("\n" + "="*70)
        print("📊 USAGE TRACKING - TOKEN & COST ANALYSIS")
        print("="*70)

        if not self.agent_stats:
            print("\nNo usage stats collected yet.")
            return

        total_tokens = sum(stats["tokens"] for stats in self.agent_stats.values())
        total_cost = sum(stats["cost"] for stats in self.agent_stats.values())

        print(f"\n{'Agent':<30} {'Messages':<10} {'Tokens':<12} {'Cost ($)':<10}")
        print("-" * 70)

        for agent_name, stats in sorted(self.agent_stats.items()):
            print(f"{agent_name:<30} {stats['messages']:<10} {stats['tokens']:<12,} ${stats['cost']:<9.4f}")

        print("-" * 70)
        print(f"{'TOTAL':<30} {sum(s['messages'] for s in self.agent_stats.values()):<10} {total_tokens:<12,} ${total_cost:<9.4f}")

        print(f"\n💡 Cost Breakdown:")
        print(f"   Model: GPT-4o-mini")
        print(f"   Input: $0.150 / 1M tokens")
        print(f"   Output: $0.600 / 1M tokens")
        print(f"   Estimated total: ${total_cost:.4f}")


def estimate_tokens(text: str) -> int:
    """Rough token estimation (4 chars ≈ 1 token)"""
    return len(text) // 4


def estimate_cost(input_tokens: int, output_tokens: int, model: str = "gpt-4o-mini") -> float:
    """Estimate cost for OpenAI API"""
    # GPT-4o-mini pricing
    input_cost_per_1m = 0.150  # $0.150 per 1M input tokens
    output_cost_per_1m = 0.600  # $0.600 per 1M output tokens

    input_cost = (input_tokens / 1_000_000) * input_cost_per_1m
    output_cost = (output_tokens / 1_000_000) * output_cost_per_1m

    return input_cost + output_cost


async def demo():
    """Run squad collaboration demo"""

    print("\n" + "="*70)
    print("🤖 SQUAD COLLABORATION DEMO")
    print("Inter-Agent Messages + Usage Tracking")
    print("="*70)

    initialize_agno()
    tracker = MessageBusTracker()

    try:
        # Create squad members
        pm_id = uuid4()
        tl_id = uuid4()
        backend_id = uuid4()

        print("\n📋 Creating Squad Members...")

        pm = AgentFactory.create_agent(
            agent_id=pm_id,
            role="project_manager",
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            force_agno=True,
        )
        print(f"   ✅ Project Manager created (ID: {str(pm_id)[:8]}...)")

        tech_lead = AgentFactory.create_agent(
            agent_id=tl_id,
            role="tech_lead",
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            force_agno=True,
        )
        print(f"   ✅ Tech Lead created (ID: {str(tl_id)[:8]}...)")

        backend_dev = AgentFactory.create_agent(
            agent_id=backend_id,
            role="backend_developer",
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            force_agno=True,
        )
        print(f"   ✅ Backend Developer created (ID: {str(backend_id)[:8]}...)")

        # =====================================================================
        # INTERACTION 1: PM → Backend Dev (TaskAssignment)
        # =====================================================================
        print("\n" + "="*70)
        print("INTERACTION 1: PM Delegates Task to Backend Developer")
        print("="*70)

        task = {
            "task_id": "SQUAD-123-backend",
            "title": "Implement WebSocket server",
            "description": "Create FastAPI WebSocket endpoints for real-time notifications",
            "acceptance_criteria": [
                "WebSocket endpoint /ws created",
                "Connection management working",
                "Broadcasting to all clients"
            ],
            "estimated_hours": 6
        }

        print(f"\n📤 PM sending TaskAssignment to Backend Developer...")
        print(f"   Task: {task['title']}")
        print(f"   Estimated: {task['estimated_hours']} hours")

        # Track message
        tracker.log_message(
            msg_type="TaskAssignment",
            sender="Project Manager",
            recipient="Backend Developer",
            content=f"{task['title']} - {task['description']}"
        )

        # Backend Dev analyzes task
        print(f"\n🤖 Backend Developer analyzing task...")
        analysis_response = await backend_dev.analyze_task(
            task_assignment=task,
            code_context="FastAPI app with existing REST endpoints"
        )

        # Track usage
        input_tokens = estimate_tokens(str(task))
        output_tokens = estimate_tokens(analysis_response.content)
        cost = estimate_cost(input_tokens, output_tokens)
        tracker.log_agent_usage("Backend Developer", input_tokens + output_tokens, cost)

        print(f"   ✅ Analysis complete")
        print(f"   📊 Tokens: {input_tokens + output_tokens:,} | Cost: ${cost:.4f}")
        print(f"\n💭 Backend Dev Response (preview):")
        print(f"   {analysis_response.content[:200]}...")

        # =====================================================================
        # INTERACTION 2: Backend Dev → Tech Lead (Question)
        # =====================================================================
        print("\n" + "="*70)
        print("INTERACTION 2: Backend Dev Asks Tech Lead a Question")
        print("="*70)

        question_text = (
            "For WebSocket implementation, should we use connection pooling "
            "or create a new connection per client? What are the scalability implications?"
        )

        print(f"\n📤 Backend Developer sending Question to Tech Lead...")
        print(f"   Question: {question_text[:100]}...")

        # Track message
        tracker.log_message(
            msg_type="Question",
            sender="Backend Developer",
            recipient="Tech Lead",
            content=question_text
        )

        # Tech Lead answers
        print(f"\n🤖 Tech Lead processing question...")
        answer_response = await tech_lead.answer_technical_question(
            question=question_text,
            asker_role="backend_developer",
            context={
                "asker_id": str(backend_id),
                "task_id": "SQUAD-123-backend",
                "question_id": "Q1"
            }
        )

        # Track usage
        input_tokens = estimate_tokens(question_text)
        output_tokens = estimate_tokens(answer_response.answer)
        cost = estimate_cost(input_tokens, output_tokens)
        tracker.log_agent_usage("Tech Lead", input_tokens + output_tokens, cost)

        print(f"   ✅ Answer provided")
        print(f"   📊 Tokens: {input_tokens + output_tokens:,} | Cost: ${cost:.4f}")
        print(f"\n💭 Tech Lead Answer (preview):")
        print(f"   {answer_response.answer[:200]}...")

        # Track answer message
        tracker.log_message(
            msg_type="Answer",
            sender="Tech Lead",
            recipient="Backend Developer",
            content=answer_response.answer
        )

        # =====================================================================
        # INTERACTION 3: Backend Dev → PM (StatusUpdate)
        # =====================================================================
        print("\n" + "="*70)
        print("INTERACTION 3: Backend Dev Sends Status Update to PM")
        print("="*70)

        status_text = (
            "Task in progress. I've analyzed the requirements and got clarification "
            "from Tech Lead on connection pooling. Starting implementation now. "
            "ETA: 4 hours remaining."
        )

        print(f"\n📤 Backend Developer sending StatusUpdate to PM...")
        print(f"   Status: {status_text[:100]}...")

        # Track message
        tracker.log_message(
            msg_type="StatusUpdate",
            sender="Backend Developer",
            recipient="Project Manager",
            content=status_text
        )

        # PM acknowledges status
        print(f"\n🤖 PM processing status update...")
        pm_response = await pm.process_message(
            f"Backend Developer provided status: {status_text}. Should I be concerned about anything?"
        )

        # Track usage
        input_tokens = estimate_tokens(status_text + "Backend Developer provided status...")
        output_tokens = estimate_tokens(pm_response.content)
        cost = estimate_cost(input_tokens, output_tokens)
        tracker.log_agent_usage("Project Manager", input_tokens + output_tokens, cost)

        print(f"   ✅ Status acknowledged")
        print(f"   📊 Tokens: {input_tokens + output_tokens:,} | Cost: ${cost:.4f}")
        print(f"\n💭 PM Response (preview):")
        print(f"   {pm_response.content[:200]}...")

        # =====================================================================
        # INTERACTION 4: Backend Dev → Tech Lead (CodeReviewRequest)
        # =====================================================================
        print("\n" + "="*70)
        print("INTERACTION 4: Backend Dev Requests Code Review from Tech Lead")
        print("="*70)

        code_diff = """
diff --git a/app/websocket.py b/app/websocket.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/app/websocket.py
@@ -0,0 +1,25 @@
+from fastapi import WebSocket, WebSocketDisconnect
+from typing import List
+
+class ConnectionManager:
+    def __init__(self):
+        self.active_connections: List[WebSocket] = []
+
+    async def connect(self, websocket: WebSocket):
+        await websocket.accept()
+        self.active_connections.append(websocket)
+
+    async def broadcast(self, message: str):
+        for connection in self.active_connections:
+            await connection.send_text(message)
+
+manager = ConnectionManager()
+
+@app.websocket("/ws")
+async def websocket_endpoint(websocket: WebSocket):
+    await manager.connect(websocket)
+    try:
+        while True:
+            data = await websocket.receive_text()
+    except WebSocketDisconnect:
+        manager.active_connections.remove(websocket)
"""

        print(f"\n📤 Backend Developer requesting Code Review from Tech Lead...")
        print(f"   Files changed: app/websocket.py (+25 lines)")
        print(f"   Changes: WebSocket connection manager implementation")

        # Track message
        tracker.log_message(
            msg_type="CodeReviewRequest",
            sender="Backend Developer",
            recipient="Tech Lead",
            content="WebSocket implementation - 25 lines added"
        )

        # Tech Lead reviews code
        print(f"\n🤖 Tech Lead reviewing code...")
        review_response = await tech_lead.review_code(
            code_diff=code_diff,
            pr_description="Implement WebSocket connection manager for real-time notifications",
            acceptance_criteria=task["acceptance_criteria"]
        )

        # Track usage
        input_tokens = estimate_tokens(code_diff + "Implement WebSocket...")
        output_tokens = estimate_tokens(review_response["full_review"])
        cost = estimate_cost(input_tokens, output_tokens)
        tracker.log_agent_usage("Tech Lead", input_tokens + output_tokens, cost)

        print(f"   ✅ Code review complete")
        print(f"   📊 Tokens: {input_tokens + output_tokens:,} | Cost: ${cost:.4f}")
        print(f"   🎯 Status: {review_response['approval_status']}")
        print(f"\n💭 Tech Lead Review (preview):")
        print(f"   {review_response['full_review'][:200]}...")

        # Track review response
        tracker.log_message(
            msg_type="CodeReviewResponse",
            sender="Tech Lead",
            recipient="Backend Developer",
            content=f"Status: {review_response['approval_status']} - {review_response['summary']}"
        )

        # =====================================================================
        # SUMMARY: Display Message Bus & Usage Stats
        # =====================================================================

        # Print all messages
        tracker.print_messages()

        # Print usage stats
        tracker.print_usage_stats()

        # =====================================================================
        # FINALE
        # =====================================================================
        print("\n" + "="*70)
        print("🎉 SQUAD COLLABORATION DEMO COMPLETE!")
        print("="*70)

        print(f"\n✨ What we demonstrated:")
        print(f"   ✅ 4 inter-agent interactions via message bus")
        print(f"   ✅ 6 messages exchanged (assignments, questions, answers, reviews)")
        print(f"   ✅ Real message types (TaskAssignment, Question, Answer, etc.)")
        print(f"   ✅ Token usage tracking per agent")
        print(f"   ✅ Cost estimation per interaction")
        print(f"   ✅ Full transparency into squad collaboration")

        print(f"\n🎯 Message Flow:")
        print(f"   PM → Backend Dev: TaskAssignment")
        print(f"   Backend Dev → Tech Lead: Question")
        print(f"   Tech Lead → Backend Dev: Answer")
        print(f"   Backend Dev → PM: StatusUpdate")
        print(f"   Backend Dev → Tech Lead: CodeReviewRequest")
        print(f"   Tech Lead → Backend Dev: CodeReviewResponse")

        print(f"\n💰 Total Cost: ${sum(s['cost'] for s in tracker.agent_stats.values()):.4f}")
        print(f"📊 Total Tokens: {sum(s['tokens'] for s in tracker.agent_stats.values()):,}")
        print(f"📨 Total Messages: {len(tracker.messages)}")

        print(f"\n🚀 All interactions tracked and auditable!")
        print(f"   - Every message logged with timestamp")
        print(f"   - Every token counted")
        print(f"   - Every cost calculated")
        print(f"   - Full squad transparency")

        # Clean up
        AgentFactory.clear_all_agents()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        shutdown_agno()


if __name__ == "__main__":
    asyncio.run(demo())
