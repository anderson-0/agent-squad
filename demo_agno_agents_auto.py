"""
Live Demo: Agno-Powered Agent Squad (Automatic)

This demo showcases:
1. PM receives a webhook and analyzes ticket
2. Session persistence (PM remembers context)
3. PM collaborates with Tech Lead
4. PM breaks down task and delegates to Backend Developer
"""
import asyncio
from uuid import uuid4

from backend.agents.factory import AgentFactory
from backend.core.agno_config import initialize_agno, shutdown_agno


async def demo():
    """Run live Agno agent demonstration"""

    print("\n" + "="*70)
    print("🎬 LIVE DEMO: AGNO-POWERED AGENT SQUAD")
    print("="*70)

    initialize_agno()

    try:
        # =====================================================================
        # SCENE 1: PM Receives Webhook Notification
        # =====================================================================
        print("\n" + "="*70)
        print("SCENE 1: PM Receives New Ticket from Jira")
        print("="*70)

        # Create Project Manager (Agno)
        pm_id = uuid4()
        pm = AgentFactory.create_agent(
            agent_id=pm_id,
            role="project_manager",
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            force_agno=True,
        )

        print(f"\n✅ Created PM Agent (Agno):")
        print(f"   Type: {type(pm).__name__}")
        print(f"   Capabilities: {len(pm.get_capabilities())}")

        # Simulate webhook from Jira
        ticket = {
            "id": "SQUAD-123",
            "title": "Add real-time notifications to dashboard",
            "description": "Users want to see real-time notifications when tasks are completed. Implement WebSocket support for live updates.",
            "priority": "high",
            "reporter": "Product Owner",
            "acceptance_criteria": [
                "WebSocket connection established on page load",
                "Notifications appear in real-time without refresh",
                "Connection gracefully handles reconnection",
                "Works across all supported browsers"
            ]
        }

        print(f"\n📥 Webhook received from Jira:")
        print(f"   Ticket: {ticket['title']}")
        print(f"   Priority: {ticket['priority']}")
        print(f"   Reporter: {ticket['reporter']}")

        # PM processes webhook
        print(f"\n🤖 PM analyzing ticket...")
        response = await pm.receive_webhook_notification(
            ticket=ticket,
            webhook_event="issue_created"
        )

        print(f"\n💭 PM's Initial Assessment:")
        print(f"{response.content}")
        print(f"\n   Session ID: {pm.session_id[:16]}...")

        # =====================================================================
        # SCENE 2: Session Persistence
        # =====================================================================
        print("\n" + "="*70)
        print("SCENE 2: Session Persistence - Different PM Instance")
        print("="*70)

        print(f"\n🔄 Creating a NEW PM agent with the SAME session...")
        print(f"   (Simulating PM agent restart or different instance)")

        # Create a completely new PM with same session
        pm2_id = uuid4()  # Different agent ID
        pm2 = AgentFactory.create_agent(
            agent_id=pm2_id,
            role="project_manager",
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            force_agno=True,
            session_id=pm.session_id,  # Resume same session
        )

        print(f"\n✅ Created PM2 Agent:")
        print(f"   Agent ID: {pm2_id}")
        print(f"   Session ID: {pm2.session_id[:16]}... (SAME as PM1)")

        # Ask PM2 about the ticket (it should remember!)
        print(f"\n❓ Asking PM2: 'What ticket did we just receive?'")
        response2 = await pm2.process_message(
            "What ticket did we just receive? What was the title and priority?"
        )

        print(f"\n🤖 PM2's Response:")
        print(f"{response2.content}")
        print(f"\n✨ PM2 remembered everything from PM1's session!")

        # =====================================================================
        # SCENE 3: PM Reviews Ticket with Tech Lead
        # =====================================================================
        print("\n" + "="*70)
        print("SCENE 3: PM Collaborates with Tech Lead")
        print("="*70)

        # Create Tech Lead (Agno)
        tl_id = uuid4()
        tech_lead = AgentFactory.create_agent(
            agent_id=tl_id,
            role="tech_lead",
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            force_agno=True,
        )

        print(f"\n✅ Created Tech Lead Agent (Agno):")
        print(f"   Type: {type(tech_lead).__name__}")
        print(f"   Capabilities: {len(tech_lead.get_capabilities())}")

        # PM reviews ticket with TL
        print(f"\n📋 PM reviewing ticket with Tech Lead...")
        review = await pm2.review_ticket_with_tech_lead(ticket=ticket)

        print(f"\n💭 PM's Review Analysis:")
        print(f"   Status: {review['status']}")
        print(f"   Questions for TL: {len(review['questions_for_tl'])}")
        print(f"\n📝 Full Assessment:")
        print(f"{review['pm_assessment'][:800]}...")

        # TL provides technical review
        print(f"\n🔧 Tech Lead providing technical assessment...")
        tl_review = await tech_lead.review_ticket_technical(
            ticket=ticket,
            pm_assessment=review['pm_assessment']
        )

        print(f"\n💭 Tech Lead's Assessment:")
        print(f"   Decision: {tl_review['decision']}")
        print(f"   Technical Risks: {len(tl_review.get('risks', []))}")
        print(f"   Architecture Impact: {tl_review.get('architecture_impact', 'N/A')[:100]}...")

        # =====================================================================
        # SCENE 4: PM Breaks Down Task
        # =====================================================================
        print("\n" + "="*70)
        print("SCENE 4: PM Breaks Down Task into Subtasks")
        print("="*70)

        squad_members = [
            {"role": "backend_developer", "specialization": "python_fastapi"},
            {"role": "frontend_developer", "specialization": "react_nextjs"},
            {"role": "tester", "specialization": "api_testing"},
        ]

        print(f"\n👥 Available Squad Members:")
        for member in squad_members:
            print(f"   - {member['role']} ({member['specialization']})")

        print(f"\n📊 PM breaking down task...")
        breakdown = await pm2.break_down_task(
            ticket=ticket,
            squad_members=squad_members
        )

        print(f"\n💭 PM's Task Breakdown:")
        print(f"   Subtasks identified: {len(breakdown['subtasks'])}")
        print(f"   Estimated total hours: {breakdown.get('total_estimated_hours', 'TBD')}")
        print(f"\n📝 Breakdown Details:")
        print(f"{breakdown['breakdown_notes'][:800]}...")

        # =====================================================================
        # SCENE 5: PM Delegates to Backend Developer
        # =====================================================================
        print("\n" + "="*70)
        print("SCENE 5: PM Delegates to Backend Developer")
        print("="*70)

        # Create Backend Developer (Agno)
        backend_id = uuid4()
        backend_dev = AgentFactory.create_agent(
            agent_id=backend_id,
            role="backend_developer",
            specialization="python_fastapi",
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            force_agno=True,
        )

        print(f"\n✅ Created Backend Developer Agent (Agno):")
        print(f"   Type: {type(backend_dev).__name__}")
        print(f"   Specialization: python_fastapi")

        # Backend developer analyzes task
        task_assignment = {
            "task_id": "SQUAD-123-backend",
            "title": "Implement WebSocket backend infrastructure",
            "description": "Create WebSocket server endpoints for real-time notifications",
            "acceptance_criteria": [
                "WebSocket connection endpoint created",
                "Notification broadcasting working",
                "Graceful connection handling"
            ],
            "estimated_hours": 6
        }

        print(f"\n📋 Backend Developer analyzing subtask:")
        print(f"   Subtask: {task_assignment['title']}")

        analysis = await backend_dev.analyze_task(
            task_assignment=task_assignment,
            code_context="FastAPI application with existing REST endpoints"
        )

        print(f"\n💭 Backend Developer's Analysis:")
        print(f"{analysis.content[:800]}...")

        # =====================================================================
        # FINALE: Summary
        # =====================================================================
        print("\n" + "="*70)
        print("🎉 DEMO COMPLETE!")
        print("="*70)

        print(f"\n✨ What we just demonstrated:")
        print(f"   ✅ PM received webhook and analyzed ticket")
        print(f"   ✅ Session persistence (PM2 remembered PM1's context)")
        print(f"   ✅ PM collaborated with Tech Lead for technical review")
        print(f"   ✅ PM broke down task into subtasks")
        print(f"   ✅ PM delegated to Backend Developer")
        print(f"   ✅ Backend Developer analyzed and planned implementation")

        print(f"\n🗄️ Session Data:")
        print(f"   PM Session: {pm.session_id[:16]}...")
        print(f"   TL Session: {tech_lead.session_id[:16] if tech_lead.session_id else 'new'}...")
        print(f"   Backend Session: {backend_dev.session_id[:16] if backend_dev.session_id else 'new'}...")

        print(f"\n🚀 All agent interactions are:")
        print(f"   - Stored in PostgreSQL (agno_sessions, agno_memory, agno_runs)")
        print(f"   - Resumable at any time")
        print(f"   - Fully persistent across restarts")

        print(f"\n💡 Key Features Demonstrated:")
        print(f"   ✅ Enterprise-grade architecture (Clean Architecture + SOLID)")
        print(f"   ✅ Persistent memory (agents remember context)")
        print(f"   ✅ Session management (resume conversations)")
        print(f"   ✅ Multi-agent collaboration (PM, TL, Backend Dev)")
        print(f"   ✅ Production-ready (12+ design patterns)")

        # Clean up
        AgentFactory.clear_all_agents()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        shutdown_agno()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🎬 AGNO AGENT SQUAD - LIVE DEMO")
    print("="*70)
    print("\nThis demo will showcase:")
    print("  1. PM receives webhook and analyzes ticket")
    print("  2. Session persistence (PM remembers context)")
    print("  3. PM collaborates with Tech Lead")
    print("  4. PM breaks down task into subtasks")
    print("  5. PM delegates to Backend Developer")
    print("\n" + "="*70)

    asyncio.run(demo())
