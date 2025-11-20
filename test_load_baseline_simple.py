#!/usr/bin/env python3
"""
Baseline Load Test - Single Workflow Performance

Tests a single PM → Backend Dev → QA workflow and collects performance metrics.
Simplified version based on the working Phase 1 test.
"""

import asyncio
import time
import psutil
from datetime import datetime
from pathlib import Path
from uuid import uuid4
import sys
import json

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
from nats.js.api import StreamConfig, RetentionPolicy


# Performance metrics
metrics = {
    "start_time": None,
    "end_time": None,
    "step_times": {},
    "nats_sent": 0,
    "nats_received": 0,
    "memory_samples": []
}

def record_memory():
    """Record current memory usage"""
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    metrics["memory_samples"].append(memory_mb)

def print_metrics():
    """Print performance report"""
    total_time = metrics["end_time"] - metrics["start_time"]

    print("\n" + "="*80)
    print("📊 BASELINE PERFORMANCE REPORT")
    print("="*80)

    print(f"\n⏱️  TIMING:")
    print(f"   Total Time: {total_time:.3f}s")

    if metrics["step_times"]:
        print(f"\n   Step Breakdown:")
        for step, duration in metrics["step_times"].items():
            print(f"      {step}: {duration:.3f}s")

    print(f"\n📨 NATS:")
    print(f"   Sent: {metrics['nats_sent']}")
    print(f"   Received: {metrics['nats_received']}")
    if metrics['nats_sent'] > 0:
        rate = (metrics['nats_received'] / metrics['nats_sent']) * 100
        print(f"   Delivery Rate: {rate:.1f}%")

    print(f"\n🧠 MEMORY:")
    if metrics["memory_samples"]:
        avg = sum(metrics["memory_samples"]) / len(metrics["memory_samples"])
        peak = max(metrics["memory_samples"])
        print(f"   Average: {avg:.2f} MB")
        print(f"   Peak: {peak:.2f} MB")

    print("\n" + "="*80)

    # Success criteria
    print("\n✅ SUCCESS CRITERIA:")
    success = True

    if total_time < 2.0:
        print(f"✅ Total time < 2s: {total_time:.3f}s")
    else:
        print(f"⚠️  Total time >= 2s: {total_time:.3f}s")
        success = False

    if metrics['nats_sent'] == metrics['nats_received']:
        print(f"✅ 100% message delivery")
    else:
        print(f"❌ Message loss detected")
        success = False

    if metrics["memory_samples"] and max(metrics["memory_samples"]) < 200:
        print(f"✅ Peak memory < 200MB")
    else:
        print(f"⚠️  Peak memory >= 200MB")
        success = False

    print("="*80)

    return success


async def test_baseline():
    """Run baseline load test"""

    metrics["start_time"] = time.time()
    record_memory()

    print("\n" + "🚀 " + "="*76)
    print("🚀 BASELINE LOAD TEST - Single Workflow")
    print("🚀 " + "="*76)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Step 1: Setup database
    step_start = time.time()
    print("📝 Step 1: Setting up test data...")

    test_data = None
    async with get_db_context() as db:
        user = User(
            id=uuid4(),
            email=f"loadtest_{int(time.time())}@example.com",
            name="Load Test User",
            password_hash="dummy_hash",
            plan_tier="pro"
        )
        db.add(user)
        await db.flush()

        org = Organization(
            id=uuid4(),
            name="Load Test Org",
            owner_id=user.id
        )
        db.add(org)
        await db.flush()

        squad = Squad(
            id=uuid4(),
            name="Load Test Squad",
            org_id=org.id,
            user_id=user.id,
            status="active"
        )
        db.add(squad)
        await db.flush()

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
            system_prompt="You are a Backend Dev. Keep responses SHORT.",
            config={"temperature": 0.7}
        )
        qa_member = SquadMember(
            id=uuid4(),
            squad_id=squad.id,
            role="tester",
            specialization="default",
            llm_provider="ollama",
            llm_model="llama3.2",
            system_prompt="You are a QA. Keep responses SHORT.",
            config={"temperature": 0.7}
        )
        db.add_all([pm_member, backend_member, qa_member])
        await db.flush()

        project = Project(
            id=uuid4(),
            name="Load Test Project",
            description="Baseline testing",
            squad_id=squad.id
        )
        db.add(project)

        task = Task(
            id=uuid4(),
            title="Baseline Test Task",
            description="Testing baseline performance",
            project_id=project.id,
            assigned_to=str(backend_member.id),
            status="pending"
        )
        db.add(task)
        await db.commit()

        test_data = {
            "user": user,
            "squad": squad,
            "pm_member": pm_member,
            "backend_member": backend_member,
            "qa_member": qa_member
        }

    metrics["step_times"]["1_setup"] = time.time() - step_start
    print(f"   ✅ Test data created in {metrics['step_times']['1_setup']:.3f}s")
    record_memory()

    # Step 2: Create agents
    step_start = time.time()
    print("\n🤖 Step 2: Creating agents...")

    pm_config = AgentConfig(
        role="project_manager",
        llm_provider=LLMProvider.OLLAMA,
        llm_model="llama3.2",
        temperature=0.7,
        system_prompt="PM. SHORT responses."
    )

    backend_config = AgentConfig(
        role="backend_developer",
        llm_provider=LLMProvider.OLLAMA,
        llm_model="llama3.2",
        temperature=0.7,
        system_prompt="Backend Dev. SHORT responses."
    )

    qa_config = AgentConfig(
        role="tester",
        llm_provider=LLMProvider.OLLAMA,
        llm_model="llama3.2",
        temperature=0.7,
        system_prompt="QA. SHORT responses."
    )

    pm_agent = AgnoProjectManagerAgent(config=pm_config, agent_id=test_data['pm_member'].id)
    backend_agent = AgnoBackendDeveloperAgent(config=backend_config, agent_id=test_data['backend_member'].id)
    qa_agent = AgnoQATesterAgent(config=qa_config, agent_id=test_data['qa_member'].id)

    metrics["step_times"]["2_agents"] = time.time() - step_start
    print(f"   ✅ 3 agents created in {metrics['step_times']['2_agents']:.3f}s")
    record_memory()

    # Step 3: Connect to NATS
    step_start = time.time()
    print("\n📡 Step 3: Connecting to NATS...")

    nc = await nats.connect(settings.NATS_URL)
    js = nc.jetstream()

    try:
        await js.stream_info(settings.NATS_STREAM_NAME)
    except Exception:
        stream_config = StreamConfig(
            name=settings.NATS_STREAM_NAME,
            subjects=[f"{settings.NATS_STREAM_NAME}.>"],
            retention=RetentionPolicy.LIMITS,
            max_msgs=settings.NATS_MAX_MSGS,
            max_age=settings.NATS_MAX_AGE_DAYS * 24 * 3600,
        )
        await js.add_stream(stream_config)

    metrics["step_times"]["3_nats"] = time.time() - step_start
    print(f"   ✅ NATS connected in {metrics['step_times']['3_nats']:.3f}s")
    record_memory()

    # Step 4: Send messages (PM → Backend → QA)
    step_start = time.time()
    print("\n📤 Step 4: Publishing messages...")

    messages = [
        {"from": "PM", "to": "Backend", "subject": f"{settings.NATS_STREAM_NAME}.task.backend", "content": "Build /login"},
        {"from": "Backend", "to": "QA", "subject": f"{settings.NATS_STREAM_NAME}.review.qa", "content": "Ready for testing"},
        {"from": "QA", "to": "PM", "subject": f"{settings.NATS_STREAM_NAME}.approval.pm", "content": "Tests pass"}
    ]

    for msg in messages:
        await js.publish(msg["subject"], msg["content"].encode())
        metrics["nats_sent"] += 1

    metrics["step_times"]["4_publish"] = time.time() - step_start
    print(f"   ✅ {metrics['nats_sent']} messages published in {metrics['step_times']['4_publish']:.3f}s")
    record_memory()

    # Step 5: Receive messages
    step_start = time.time()
    print("\n📥 Step 5: Receiving messages...")

    sub = await js.pull_subscribe(subject=f"{settings.NATS_STREAM_NAME}.>", durable="baseline-test")

    for i in range(metrics["nats_sent"]):
        try:
            msgs = await sub.fetch(batch=1, timeout=5)
            if msgs:
                await msgs[0].ack()
                metrics["nats_received"] += 1
        except Exception:
            break

    metrics["step_times"]["5_receive"] = time.time() - step_start
    print(f"   ✅ {metrics['nats_received']} messages received in {metrics['step_times']['5_receive']:.3f}s")
    record_memory()

    # Step 6: Cleanup
    step_start = time.time()
    print("\n🧹 Step 6: Cleanup...")

    async with get_db_context() as db:
        from sqlalchemy import delete
        await db.execute(delete(User).where(User.id == test_data['user'].id))
        await db.commit()

    await nc.close()

    metrics["step_times"]["6_cleanup"] = time.time() - step_start
    print(f"   ✅ Cleanup done in {metrics['step_times']['6_cleanup']:.3f}s")
    record_memory()

    # End timing
    metrics["end_time"] = time.time()

    # Print report
    success = print_metrics()

    if success:
        print("\n🎉 BASELINE TEST PASSED!\n")
    else:
        print("\n⚠️  BASELINE TEST COMPLETED with warnings\n")

    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(test_baseline())
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
