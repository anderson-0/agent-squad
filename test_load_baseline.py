#!/usr/bin/env python3
"""
Baseline Load Test - Single Workflow Performance

Tests a single PM → Backend Dev → QA workflow and collects performance metrics.
This establishes baseline performance for comparison with concurrent load tests.
"""

import asyncio
import time
import psutil
import os
from datetime import datetime
from typing import Dict, List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend to path
import sys
from pathlib import Path
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).parent))

from backend.models.user import User, Organization
from backend.models.squad import Squad, SquadMember
from backend.models.project import Project, Task
from backend.core.database import get_db_context
from backend.core.config import settings
from backend.agents.specialized.agno_project_manager import AgnoProjectManagerAgent
from backend.agents.specialized.agno_backend_developer import AgnoBackendDeveloperAgent
from backend.agents.specialized.agno_qa_tester import AgnoQATesterAgent
from backend.agents.agno_base import AgentConfig, LLMProvider
import nats

# Performance metrics tracker
class PerformanceMetrics:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.step_times: Dict[str, float] = {}
        self.nats_messages_sent = 0
        self.nats_messages_received = 0
        self.db_queries = 0
        self.memory_usage_mb: List[float] = []
        self.process = psutil.Process()

    def start(self):
        """Start timing"""
        self.start_time = time.time()
        self._record_memory()

    def end(self):
        """End timing"""
        self.end_time = time.time()
        self._record_memory()

    def record_step(self, step_name: str, duration: float):
        """Record step timing"""
        self.step_times[step_name] = duration

    def _record_memory(self):
        """Record current memory usage"""
        memory_info = self.process.memory_info()
        self.memory_usage_mb.append(memory_info.rss / 1024 / 1024)  # Convert to MB

    def total_time(self) -> float:
        """Get total execution time"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    def avg_memory_mb(self) -> float:
        """Get average memory usage"""
        if self.memory_usage_mb:
            return sum(self.memory_usage_mb) / len(self.memory_usage_mb)
        return 0.0

    def peak_memory_mb(self) -> float:
        """Get peak memory usage"""
        if self.memory_usage_mb:
            return max(self.memory_usage_mb)
        return 0.0

    def print_report(self):
        """Print performance report"""
        print("\n" + "="*80)
        print("📊 BASELINE PERFORMANCE REPORT")
        print("="*80)

        print(f"\n⏱️  TIMING:")
        print(f"   Total Execution Time: {self.total_time():.3f}s")

        if self.step_times:
            print(f"\n   Step Breakdown:")
            for step, duration in self.step_times.items():
                print(f"      {step}: {duration:.3f}s")

        print(f"\n📨 NATS MESSAGES:")
        print(f"   Sent: {self.nats_messages_sent}")
        print(f"   Received: {self.nats_messages_received}")
        if self.nats_messages_sent > 0:
            delivery_rate = (self.nats_messages_received / self.nats_messages_sent) * 100
            print(f"   Delivery Rate: {delivery_rate:.1f}%")

        print(f"\n💾 DATABASE:")
        print(f"   Queries Executed: {self.db_queries}")
        if self.total_time() > 0:
            print(f"   Queries/sec: {self.db_queries / self.total_time():.2f}")

        print(f"\n🧠 MEMORY:")
        print(f"   Average: {self.avg_memory_mb():.2f} MB")
        print(f"   Peak: {self.peak_memory_mb():.2f} MB")

        print("\n" + "="*80)


async def count_db_queries(session: AsyncSession) -> int:
    """Count database queries (approximate via pg_stat_statements)"""
    try:
        result = await session.execute(text("SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active'"))
        count = result.scalar()
        return count or 0
    except Exception:
        # pg_stat_statements might not be available
        return 0


async def test_baseline_workflow():
    """
    Test a single workflow: PM → Backend Dev → QA
    Collect comprehensive performance metrics
    """

    metrics = PerformanceMetrics()
    metrics.start()

    print("\n" + "🚀 " + "="*76)
    print("🚀 BASELINE LOAD TEST - Single Workflow Performance")
    print("🚀 " + "="*76)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Setup test data
    test_data = None
    async with get_db_context() as db:
        try:
            # Step 1: Setup test data
            step_start = time.time()
            print("📝 Step 1: Setting up test data...")

            # Create user
            user = User(
                id=uuid4(),
                email=f"loadtest_baseline_{int(time.time())}@example.com",
                name="Load Test User",
                password_hash="dummy_hash",
                plan_tier="enterprise"
            )
            db.add(user)
            await db.flush()

            # Create organization
            org = Organization(
                id=uuid4(),
                name="Load Test Organization",
                owner_id=user.id
            )
            db.add(org)
            await db.flush()

            # Create squad
            squad = Squad(
                id=uuid4(),
                name="Load Test Squad",
                org_id=org.id,
                user_id=user.id,
                status="active"
            )
            db.add(squad)
            await db.flush()

            # Create squad members
            pm_member = SquadMember(
                id=uuid4(),
                squad_id=squad.id,
                role="project_manager",
                specialization="default",
                llm_provider="ollama",
                llm_model="llama3.2",
                system_prompt="You are a PM. Keep responses SHORT.",
                config={"temperature": 0.7}
            )
            backend_member = SquadMember(
                id=uuid4(),
                squad_id=squad.id,
                role="backend_developer",
                specialization="default",
                llm_provider="ollama",
                llm_model="llama3.2",
                system_prompt="You are a Backend Developer. Keep responses SHORT.",
                config={"temperature": 0.7}
            )
            qa_member = SquadMember(
                id=uuid4(),
                squad_id=squad.id,
                role="tester",
                specialization="default",
                llm_provider="ollama",
                llm_model="llama3.2",
                system_prompt="You are a QA Tester. Keep responses SHORT.",
                config={"temperature": 0.7}
            )
            db.add_all([pm_member, backend_member, qa_member])
            await db.flush()

            # Create project and task
            project = Project(
                id=uuid4(),
                name="Load Test Project",
                description="Baseline performance testing",
                squad_id=squad.id
            )
            db.add(project)

            task = Task(
                id=uuid4(),
                title="Baseline Performance Test Task",
                description="Testing single workflow performance",
                project_id=project.id,
                assigned_to=str(backend_member.id),
                status="pending"
            )
            db.add(task)
            await db.commit()

            db_queries_after_setup = await count_db_queries(db)
            metrics.db_queries += db_queries_after_setup

            # Store test data for later use
            test_data = {
                "user": user,
                "org": org,
                "squad": squad,
                "pm_member": pm_member,
                "backend_member": backend_member,
                "qa_member": qa_member,
                "project": project,
                "task": task
            }

            step_duration = time.time() - step_start
            metrics.record_step("1_setup_test_data", step_duration)
            print(f"   ✅ Test data created in {step_duration:.3f}s")
            metrics._record_memory()

        except Exception as e:
            print(f"   ❌ Setup failed: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            return False

    if not test_data:
        print("❌ Failed to create test data")
        return False

    # Step 2: Create agents (outside db context)
    step_start = time.time()
    print("\n🤖 Step 2: Creating agents...")

    try:
        pm_config = AgentConfig(
            role="project_manager",
            llm_provider=LLMProvider.OLLAMA,
            llm_model="llama3.2",
            temperature=0.7,
            system_prompt="You are a PM. Keep ALL responses SHORT (1-2 sentences max)."
        )

        backend_config = AgentConfig(
            role="backend_developer",
            llm_provider=LLMProvider.OLLAMA,
            llm_model="llama3.2",
            temperature=0.7,
            system_prompt="You are a Backend Dev. Keep ALL responses SHORT (1-2 sentences max)."
        )

        qa_config = AgentConfig(
            role="tester",
            llm_provider=LLMProvider.OLLAMA,
            llm_model="llama3.2",
            temperature=0.7,
            system_prompt="You are a QA Tester. Keep ALL responses SHORT (1-2 sentences max)."
        )

        pm_agent = AgnoProjectManagerAgent(
            config=pm_config,
            agent_id=test_data['pm_member'].id
        )

        backend_agent = AgnoBackendDeveloperAgent(
            config=backend_config,
            agent_id=test_data['backend_member'].id
        )

        qa_agent = AgnoQATesterAgent(
            config=qa_config,
            agent_id=test_data['qa_member'].id
        )

        step_duration = time.time() - step_start
        metrics.record_step("2_create_agents", step_duration)
        print(f"   ✅ 3 agents created in {step_duration:.3f}s")
        metrics._record_memory()

    except Exception as e:
        print(f"   ❌ Agent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 3: Initialize NATS
    step_start = time.time()
    print("\n📡 Step 3: Initializing NATS messaging...")

    nc = None
    js = None

    try:
        nc = await nats.connect(settings.NATS_URL)
        js = nc.jetstream()

        # Try to use existing stream or create new one
        try:
            await js.stream_info(settings.NATS_STREAM_NAME)
        except Exception:
            from nats.js.api import StreamConfig, RetentionPolicy
            stream_config = StreamConfig(
                name=settings.NATS_STREAM_NAME,
                subjects=[f"{settings.NATS_STREAM_NAME}.>"],
                retention=RetentionPolicy.LIMITS,
                max_msgs=settings.NATS_MAX_MSGS,
                max_age=settings.NATS_MAX_AGE_DAYS * 24 * 3600,
            )
            await js.add_stream(stream_config)

        step_duration = time.time() - step_start
        metrics.record_step("3_init_nats", step_duration)
        print(f"   ✅ NATS connected in {step_duration:.3f}s")
        metrics._record_memory()

    except Exception as e:
        print(f"   ❌ NATS connection failed: {e}")
        return False

            # Step 4: Publish messages (PM → Backend Dev → QA)
            step_start = time.time()
            print("\n📤 Step 4: Publishing NATS messages...")

            messages = [
                {
                    "from": "project_manager",
                    "to": "backend_developer",
                    "content": "Implement user authentication endpoint",
                    "subject": f"squad.{squad.id}.pm_to_backend"
                },
                {
                    "from": "backend_developer",
                    "to": "qa_tester",
                    "content": "Authentication endpoint implemented, ready for testing",
                    "subject": f"squad.{squad.id}.backend_to_qa"
                },
                {
                    "from": "qa_tester",
                    "to": "project_manager",
                    "content": "All tests passed, endpoint is working correctly",
                    "subject": f"squad.{squad.id}.qa_to_pm"
                }
            ]

            for msg in messages:
                await js.publish(
                    msg["subject"],
                    f'{msg["content"]}'.encode()
                )
                metrics.nats_messages_sent += 1

            step_duration = time.time() - step_start
            metrics.record_step("4_publish_messages", step_duration)
            print(f"   ✅ {metrics.nats_messages_sent} messages published in {step_duration:.3f}s")
            metrics._record_memory()

            # Step 5: Receive messages
            step_start = time.time()
            print("\n📥 Step 5: Receiving NATS messages...")

            # Subscribe to all squad messages
            sub = await js.subscribe(f"squad.{squad.id}.>")

            received_messages = []
            timeout = 5  # 5 second timeout
            start_receive = time.time()

            while len(received_messages) < metrics.nats_messages_sent:
                if time.time() - start_receive > timeout:
                    print(f"   ⚠️  Timeout after {timeout}s")
                    break

                try:
                    msg = await asyncio.wait_for(sub.next_msg(), timeout=1.0)
                    await msg.ack()
                    received_messages.append(msg)
                    metrics.nats_messages_received += 1
                except asyncio.TimeoutError:
                    continue

            step_duration = time.time() - step_start
            metrics.record_step("5_receive_messages", step_duration)
            print(f"   ✅ {metrics.nats_messages_received} messages received in {step_duration:.3f}s")
            metrics._record_memory()

            # Step 6: Cleanup
            step_start = time.time()
            print("\n🧹 Step 6: Cleaning up...")

            # Delete test data (cascade from user)
            await session.execute(text(f"DELETE FROM users WHERE id = '{user.id}'"))
            await session.commit()

            db_queries_after_cleanup = await count_db_queries(session)
            metrics.db_queries += db_queries_after_cleanup

            # Close NATS
            await nats_client.close()

            step_duration = time.time() - step_start
            metrics.record_step("6_cleanup", step_duration)
            print(f"   ✅ Cleanup completed in {step_duration:.3f}s")
            metrics._record_memory()

        except Exception as e:
            print(f"\n❌ Error during baseline test: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            return False

    # End timing
    metrics.end()

    # Print performance report
    metrics.print_report()

    # Success criteria
    print("\n" + "="*80)
    print("✅ SUCCESS CRITERIA")
    print("="*80)

    success = True

    # Check total time < 2s
    if metrics.total_time() < 2.0:
        print(f"✅ Total time < 2s: {metrics.total_time():.3f}s")
    else:
        print(f"⚠️  Total time >= 2s: {metrics.total_time():.3f}s")
        success = False

    # Check message delivery
    if metrics.nats_messages_sent == metrics.nats_messages_received:
        print(f"✅ 100% message delivery: {metrics.nats_messages_received}/{metrics.nats_messages_sent}")
    else:
        print(f"❌ Message loss detected: {metrics.nats_messages_received}/{metrics.nats_messages_sent}")
        success = False

    # Check memory usage < 200MB
    if metrics.peak_memory_mb() < 200:
        print(f"✅ Peak memory < 200MB: {metrics.peak_memory_mb():.2f} MB")
    else:
        print(f"⚠️  Peak memory >= 200MB: {metrics.peak_memory_mb():.2f} MB")
        success = False

    print("="*80)

    if success:
        print("\n🎉 BASELINE TEST PASSED! All criteria met.")
    else:
        print("\n⚠️  BASELINE TEST COMPLETED with warnings.")

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(test_baseline_workflow())
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Baseline test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
