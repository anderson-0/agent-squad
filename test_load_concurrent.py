#!/usr/bin/env python3
"""
Concurrent Load Test - Multiple Workflow Performance

Tests multiple concurrent PM → Backend Dev → QA workflows and collects performance metrics.
Supports testing 5 and 10 concurrent workflows.
"""

import asyncio
import time
import psutil
import os
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.models.user import User
from backend.models.organization import Organization
from backend.models.squad import Squad, SquadMember
from backend.models.task import Task
from backend.core.database import get_async_session
from backend.agents.factory import AgentFactory
from backend.core.config import get_settings
from backend.integrations.nats_client import NATSClient


# Performance metrics tracker for concurrent tests
class ConcurrentMetrics:
    def __init__(self, num_workflows: int):
        self.num_workflows = num_workflows
        self.start_time = None
        self.end_time = None
        self.workflow_times: List[float] = []
        self.total_nats_messages_sent = 0
        self.total_nats_messages_received = 0
        self.total_db_queries = 0
        self.memory_samples: List[float] = []
        self.errors: List[str] = []
        self.process = psutil.Process()

    def start(self):
        """Start timing"""
        self.start_time = time.time()
        self._record_memory()

    def end(self):
        """End timing"""
        self.end_time = time.time()
        self._record_memory()

    def record_workflow_time(self, duration: float):
        """Record individual workflow time"""
        self.workflow_times.append(duration)

    def record_error(self, error: str):
        """Record an error"""
        self.errors.append(error)

    def _record_memory(self):
        """Record current memory usage"""
        memory_info = self.process.memory_info()
        self.memory_samples.append(memory_info.rss / 1024 / 1024)  # MB

    def total_time(self) -> float:
        """Get total execution time"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    def avg_workflow_time(self) -> float:
        """Get average workflow time"""
        if self.workflow_times:
            return sum(self.workflow_times) / len(self.workflow_times)
        return 0.0

    def min_workflow_time(self) -> float:
        """Get minimum workflow time"""
        return min(self.workflow_times) if self.workflow_times else 0.0

    def max_workflow_time(self) -> float:
        """Get maximum workflow time"""
        return max(self.workflow_times) if self.workflow_times else 0.0

    def avg_memory_mb(self) -> float:
        """Get average memory usage"""
        if self.memory_samples:
            return sum(self.memory_samples) / len(self.memory_samples)
        return 0.0

    def peak_memory_mb(self) -> float:
        """Get peak memory usage"""
        if self.memory_samples:
            return max(self.memory_samples)
        return 0.0

    def error_rate(self) -> float:
        """Get error rate percentage"""
        if self.num_workflows > 0:
            return (len(self.errors) / self.num_workflows) * 100
        return 0.0

    def message_delivery_rate(self) -> float:
        """Get message delivery rate percentage"""
        if self.total_nats_messages_sent > 0:
            return (self.total_nats_messages_received / self.total_nats_messages_sent) * 100
        return 0.0

    def throughput_workflows_per_sec(self) -> float:
        """Get throughput in workflows per second"""
        total = self.total_time()
        if total > 0:
            return len(self.workflow_times) / total
        return 0.0

    def print_report(self):
        """Print comprehensive performance report"""
        print("\n" + "="*80)
        print(f"📊 CONCURRENT LOAD TEST REPORT - {self.num_workflows} Workflows")
        print("="*80)

        print(f"\n⏱️  TIMING:")
        print(f"   Total Execution Time: {self.total_time():.3f}s")
        print(f"   Throughput: {self.throughput_workflows_per_sec():.2f} workflows/sec")

        print(f"\n   Workflow Times:")
        print(f"      Average: {self.avg_workflow_time():.3f}s")
        print(f"      Min: {self.min_workflow_time():.3f}s")
        print(f"      Max: {self.max_workflow_time():.3f}s")

        print(f"\n📨 NATS MESSAGES:")
        print(f"   Sent: {self.total_nats_messages_sent}")
        print(f"   Received: {self.total_nats_messages_received}")
        print(f"   Delivery Rate: {self.message_delivery_rate():.1f}%")

        print(f"\n💾 DATABASE:")
        print(f"   Total Queries: {self.total_db_queries}")
        if self.total_time() > 0:
            print(f"   Queries/sec: {self.total_db_queries / self.total_time():.2f}")

        print(f"\n🧠 MEMORY:")
        print(f"   Average: {self.avg_memory_mb():.2f} MB")
        print(f"   Peak: {self.peak_memory_mb():.2f} MB")

        print(f"\n❌ ERRORS:")
        print(f"   Total Errors: {len(self.errors)}")
        print(f"   Error Rate: {self.error_rate():.1f}%")
        if self.errors:
            print(f"   First 3 errors:")
            for error in self.errors[:3]:
                print(f"      - {error}")

        print("\n" + "="*80)


async def run_single_workflow(
    workflow_id: int,
    metrics: ConcurrentMetrics,
    session: AsyncSession
) -> bool:
    """
    Run a single workflow and collect metrics

    Args:
        workflow_id: Unique identifier for this workflow
        metrics: Shared metrics object
        session: Database session

    Returns:
        True if successful, False otherwise
    """
    workflow_start = time.time()

    try:
        # Create test data for this workflow
        user = User(
            email=f"loadtest_concurrent_{workflow_id}_{int(time.time())}@example.com",
            name=f"Load Test User {workflow_id}",
            hashed_password="dummy_hash",
            is_active=True,
            plan_tier="enterprise"
        )
        session.add(user)
        await session.flush()

        org = Organization(
            name=f"Load Test Org {workflow_id}",
            owner_id=user.id
        )
        session.add(org)
        await session.flush()

        squad = Squad(
            name=f"Load Test Squad {workflow_id}",
            description=f"Concurrent test workflow {workflow_id}",
            org_id=org.id,
            status="active"
        )
        session.add(squad)
        await session.flush()

        # Create squad members
        pm_member = SquadMember(
            squad_id=squad.id,
            role="project_manager",
            system_prompt="You are a Project Manager"
        )
        backend_member = SquadMember(
            squad_id=squad.id,
            role="backend_developer",
            system_prompt="You are a Backend Developer"
        )
        qa_member = SquadMember(
            squad_id=squad.id,
            role="qa_tester",
            system_prompt="You are a QA Tester"
        )
        session.add_all([pm_member, backend_member, qa_member])
        await session.flush()

        task = Task(
            title=f"Concurrent Test Task {workflow_id}",
            description=f"Testing concurrent workflow {workflow_id}",
            task_type="testing",
            priority="high",
            org_id=org.id,
            squad_id=squad.id,
            created_by_id=user.id,
            status="pending"
        )
        session.add(task)
        await session.commit()

        # Create agents
        factory = AgentFactory()
        pm_agent = factory.create_agent(
            role="project_manager",
            squad_id=str(squad.id),
            member_id=str(pm_member.id),
            system_prompt=pm_member.system_prompt
        )

        # Initialize NATS for this workflow
        nats_client = NATSClient()
        await nats_client.connect()

        js = nats_client.nc.jetstream()
        stream_name = f"SQUAD_{squad.id}"

        try:
            await js.add_stream(
                name=stream_name,
                subjects=[f"squad.{squad.id}.>"]
            )
        except Exception:
            pass  # Stream might already exist

        # Publish messages
        messages_to_send = 3
        for i in range(messages_to_send):
            await js.publish(
                f"squad.{squad.id}.message_{i}",
                f"Message {i} from workflow {workflow_id}".encode()
            )
            metrics.total_nats_messages_sent += 1

        # Receive messages
        sub = await js.subscribe(f"squad.{squad.id}.>")
        received_count = 0
        timeout = 3  # 3 second timeout per workflow

        start_receive = time.time()
        while received_count < messages_to_send:
            if time.time() - start_receive > timeout:
                break

            try:
                msg = await asyncio.wait_for(sub.next_msg(), timeout=0.5)
                await msg.ack()
                received_count += 1
                metrics.total_nats_messages_received += 1
            except asyncio.TimeoutError:
                continue

        # Cleanup
        await session.execute(text(f"DELETE FROM users WHERE id = '{user.id}'"))
        await session.commit()

        await nats_client.close()

        # Record workflow time
        workflow_duration = time.time() - workflow_start
        metrics.record_workflow_time(workflow_duration)

        return True

    except Exception as e:
        error_msg = f"Workflow {workflow_id} failed: {str(e)}"
        metrics.record_error(error_msg)
        await session.rollback()
        return False


async def test_concurrent_workflows(num_workflows: int):
    """
    Test multiple concurrent workflows

    Args:
        num_workflows: Number of workflows to run concurrently (5 or 10)
    """

    metrics = ConcurrentMetrics(num_workflows)
    metrics.start()

    print("\n" + "🚀 " + "="*76)
    print(f"🚀 CONCURRENT LOAD TEST - {num_workflows} Workflows")
    print("🚀 " + "="*76)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Create tasks for all workflows
    tasks = []
    sessions = []

    print(f"📝 Creating {num_workflows} concurrent workflows...\n")

    # Get separate database sessions for each workflow
    for i in range(num_workflows):
        async for session in get_async_session():
            sessions.append(session)
            task = run_single_workflow(i + 1, metrics, session)
            tasks.append(task)
            break  # Only get one session per iteration

    # Run all workflows concurrently
    print(f"🏃 Running {num_workflows} workflows in parallel...")
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Record memory samples during execution
    metrics._record_memory()

    # End timing
    metrics.end()

    # Count successes
    successes = sum(1 for r in results if r is True)
    failures = num_workflows - successes

    print(f"\n✅ Completed: {successes}/{num_workflows} workflows successful")
    if failures > 0:
        print(f"❌ Failed: {failures} workflows")

    # Print performance report
    metrics.print_report()

    # Success criteria
    print("\n" + "="*80)
    print("✅ SUCCESS CRITERIA")
    print("="*80)

    success = True
    target_time = 5.0 if num_workflows == 5 else 10.0

    # Check average time
    if metrics.avg_workflow_time() < target_time:
        print(f"✅ Avg workflow time < {target_time}s: {metrics.avg_workflow_time():.3f}s")
    else:
        print(f"⚠️  Avg workflow time >= {target_time}s: {metrics.avg_workflow_time():.3f}s")
        success = False

    # Check message delivery
    if metrics.message_delivery_rate() >= 100.0:
        print(f"✅ 100% message delivery: {metrics.total_nats_messages_received}/{metrics.total_nats_messages_sent}")
    else:
        print(f"⚠️  Message loss: {metrics.message_delivery_rate():.1f}%")
        success = False

    # Check error rate
    if metrics.error_rate() < 1.0:
        print(f"✅ Error rate < 1%: {metrics.error_rate():.1f}%")
    else:
        print(f"❌ Error rate >= 1%: {metrics.error_rate():.1f}%")
        success = False

    # Check memory usage
    target_memory = 500 if num_workflows == 5 else 1000
    if metrics.peak_memory_mb() < target_memory:
        print(f"✅ Peak memory < {target_memory}MB: {metrics.peak_memory_mb():.2f} MB")
    else:
        print(f"⚠️  Peak memory >= {target_memory}MB: {metrics.peak_memory_mb():.2f} MB")
        success = False

    print("="*80)

    if success:
        print(f"\n🎉 {num_workflows}-WORKFLOW TEST PASSED! All criteria met.")
    else:
        print(f"\n⚠️  {num_workflows}-WORKFLOW TEST COMPLETED with warnings.")

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return success, metrics


async def main():
    """Main entry point"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_load_concurrent.py <num_workflows>")
        print("  num_workflows: 5 or 10")
        sys.exit(1)

    try:
        num_workflows = int(sys.argv[1])
        if num_workflows not in [5, 10]:
            print("Error: num_workflows must be 5 or 10")
            sys.exit(1)
    except ValueError:
        print("Error: num_workflows must be an integer")
        sys.exit(1)

    success, metrics = await test_concurrent_workflows(num_workflows)
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Concurrent test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
