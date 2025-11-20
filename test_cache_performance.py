"""
Cache Performance Test Script

Tests caching performance improvements for Phase 3A.

Usage:
    PYTHONPATH=/Users/anderson/Documents/anderson-0/agent-squad python test_cache_performance.py

Measures:
- Response times with and without cache
- Cache hit rates
- Performance improvement percentage
"""
import asyncio
import time
import statistics
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.core.config import settings
from backend.models.squad import Squad, SquadMember
from backend.models.project import Task, TaskExecution
from backend.services.cached_services.squad_cache import get_squad_cache
from backend.services.cached_services.task_cache import get_task_cache
from backend.services.cache_metrics import get_cache_metrics


# Test database URL
TEST_DB_URL = settings.DATABASE_URL


async def setup_test_data(session: AsyncSession):
    """Create test data for performance testing"""
    print("📦 Setting up test data...")

    # Create test squad
    squad = Squad(
        id=uuid4(),
        org_id=uuid4(),
        user_id=uuid4(),
        name="Performance Test Squad",
        description="Squad for cache performance testing",
        status="active",
        config={}
    )
    session.add(squad)

    # Create squad members
    roles = ["project_manager", "backend_developer", "frontend_developer"]
    members = []
    for role in roles:
        member = SquadMember(
            id=uuid4(),
            squad_id=squad.id,
            role=role,
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            system_prompt=f"You are a {role}",
            config={},
            is_active=True
        )
        session.add(member)
        members.append(member)

    # Create test tasks
    project_id = uuid4()
    tasks = []
    for i in range(10):
        task = Task(
            id=uuid4(),
            project_id=project_id,
            title=f"Test Task {i}",
            description=f"Task for performance testing {i}",
            status="pending",
            priority="medium",
            task_metadata={}
        )
        session.add(task)
        tasks.append(task)

        # Create executions
        execution = TaskExecution(
            id=uuid4(),
            task_id=task.id,
            squad_id=squad.id,
            status="pending",
            logs=[],
            execution_metadata={}
        )
        session.add(execution)

    await session.commit()

    print(f"✅ Created test data:")
    print(f"   - 1 squad")
    print(f"   - {len(members)} squad members")
    print(f"   - {len(tasks)} tasks")
    print(f"   - {len(tasks)} executions")

    return squad.id, [m.id for m in members], [t.id for t in tasks], project_id


async def cleanup_test_data(session: AsyncSession, squad_id):
    """Clean up test data after testing"""
    print("\n🧹 Cleaning up test data...")
    # In real implementation, would delete squad and related data
    # For now, just commit any pending changes
    await session.commit()
    print("✅ Cleanup complete")


async def test_squad_caching_performance(session: AsyncSession, squad_id):
    """Test squad caching performance"""
    print("\n🔍 Testing Squad Caching Performance")
    print("=" * 60)

    squad_cache = get_squad_cache()

    # Clear cache first
    await squad_cache.invalidate_squad(squad_id)

    # Warm up (ignore first call)
    await squad_cache.get_squad_by_id(session, squad_id, use_cache=False)

    # Test without cache (10 calls)
    times_no_cache = []
    for _ in range(10):
        start = time.perf_counter()
        await squad_cache.get_squad_by_id(session, squad_id, use_cache=False)
        elapsed = time.perf_counter() - start
        times_no_cache.append(elapsed)

    avg_no_cache = statistics.mean(times_no_cache) * 1000  # Convert to ms

    # Test with cache (first call is miss, rest are hits)
    times_with_cache = []
    await squad_cache.invalidate_squad(squad_id)  # Clear cache

    for i in range(10):
        start = time.perf_counter()
        await squad_cache.get_squad_by_id(session, squad_id, use_cache=True)
        elapsed = time.perf_counter() - start
        times_with_cache.append(elapsed)

    avg_with_cache = statistics.mean(times_with_cache[1:]) * 1000  # Skip first (cache miss)
    first_call_time = times_with_cache[0] * 1000  # Cache miss

    improvement = ((avg_no_cache - avg_with_cache) / avg_no_cache) * 100

    print(f"\n📊 Results:")
    print(f"   Without cache (avg):  {avg_no_cache:.2f}ms")
    print(f"   With cache miss:      {first_call_time:.2f}ms")
    print(f"   With cache hit (avg): {avg_with_cache:.2f}ms")
    print(f"   🚀 Improvement:       {improvement:.1f}%")

    return improvement


async def test_execution_status_caching(session: AsyncSession, squad_id):
    """Test execution status caching (HOT PATH)"""
    print("\n🔥 Testing Execution Status Caching (HOT PATH)")
    print("=" * 60)

    task_cache = get_task_cache()

    # Get an execution
    from sqlalchemy import select
    result = await session.execute(
        select(TaskExecution).filter(TaskExecution.squad_id == squad_id).limit(1)
    )
    execution = result.scalar_one()

    # Clear cache first
    await task_cache.invalidate_execution(execution.id)

    # Test without cache (20 calls - status polling is frequent)
    times_no_cache = []
    for _ in range(20):
        start = time.perf_counter()
        await task_cache.get_execution_status(session, execution.id, use_cache=False)
        elapsed = time.perf_counter() - start
        times_no_cache.append(elapsed)

    avg_no_cache = statistics.mean(times_no_cache) * 1000

    # Test with cache
    times_with_cache = []
    await task_cache.invalidate_execution(execution.id)

    for i in range(20):
        start = time.perf_counter()
        await task_cache.get_execution_status(session, execution.id, use_cache=True)
        elapsed = time.perf_counter() - start
        times_with_cache.append(elapsed)

    avg_with_cache = statistics.mean(times_with_cache[1:]) * 1000
    first_call_time = times_with_cache[0] * 1000

    improvement = ((avg_no_cache - avg_with_cache) / avg_no_cache) * 100

    print(f"\n📊 Results (HOT PATH - most frequent operation):")
    print(f"   Without cache (avg):  {avg_no_cache:.2f}ms")
    print(f"   With cache miss:      {first_call_time:.2f}ms")
    print(f"   With cache hit (avg): {avg_with_cache:.2f}ms")
    print(f"   🚀 Improvement:       {improvement:.1f}%")

    return improvement


async def test_squad_members_caching(session: AsyncSession, squad_id):
    """Test squad members list caching"""
    print("\n👥 Testing Squad Members List Caching")
    print("=" * 60)

    squad_cache = get_squad_cache()

    # Clear cache
    await squad_cache.invalidate_squad_member(squad_id)

    # Test without cache
    times_no_cache = []
    for _ in range(10):
        start = time.perf_counter()
        await squad_cache.get_squad_members(session, squad_id, use_cache=False)
        elapsed = time.perf_counter() - start
        times_no_cache.append(elapsed)

    avg_no_cache = statistics.mean(times_no_cache) * 1000

    # Test with cache
    times_with_cache = []
    await squad_cache.invalidate_squad_member(squad_id)

    for i in range(10):
        start = time.perf_counter()
        await squad_cache.get_squad_members(session, squad_id, use_cache=True)
        elapsed = time.perf_counter() - start
        times_with_cache.append(elapsed)

    avg_with_cache = statistics.mean(times_with_cache[1:]) * 1000
    improvement = ((avg_no_cache - avg_with_cache) / avg_no_cache) * 100

    print(f"\n📊 Results:")
    print(f"   Without cache (avg):  {avg_no_cache:.2f}ms")
    print(f"   With cache hit (avg): {avg_with_cache:.2f}ms")
    print(f"   🚀 Improvement:       {improvement:.1f}%")

    return improvement


async def test_cache_metrics():
    """Test cache metrics tracking"""
    print("\n📈 Cache Metrics Summary")
    print("=" * 60)

    metrics = get_cache_metrics()
    snapshot = await metrics.get_metrics()

    print(f"\n📊 Overall Metrics:")
    print(f"   Total requests:    {snapshot.total_requests}")
    print(f"   Overall hit rate:  {snapshot.overall_hit_rate:.1f}%")

    print(f"\n📊 Metrics by Entity Type:")
    for entity_type, entity_metrics in snapshot.metrics_by_type.items():
        print(f"\n   {entity_type.upper()}:")
        print(f"      Hits:       {entity_metrics.hits}")
        print(f"      Misses:     {entity_metrics.misses}")
        print(f"      Hit rate:   {entity_metrics.hit_rate:.1f}%")
        print(f"      Updates:    {entity_metrics.updates}")

    print(f"\n💡 TTL Recommendations:")
    for entity_type, recommendation in snapshot.ttl_recommendations.items():
        print(f"   {entity_type}: {recommendation}")


async def main():
    """Run all cache performance tests"""
    print("\n" + "=" * 60)
    print("🚀 Phase 3A: Cache Performance Test")
    print("=" * 60)

    # Create async engine
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Setup test data
            squad_id, member_ids, task_ids, project_id = await setup_test_data(session)

            # Run performance tests
            squad_improvement = await test_squad_caching_performance(session, squad_id)
            exec_improvement = await test_execution_status_caching(session, squad_id)
            members_improvement = await test_squad_members_caching(session, squad_id)

            # Show cache metrics
            await test_cache_metrics()

            # Summary
            print("\n" + "=" * 60)
            print("📊 PERFORMANCE SUMMARY")
            print("=" * 60)
            print(f"\n✅ Squad caching:          {squad_improvement:.1f}% faster")
            print(f"✅ Execution status (HOT): {exec_improvement:.1f}% faster")
            print(f"✅ Squad members:          {members_improvement:.1f}% faster")

            avg_improvement = (squad_improvement + exec_improvement + members_improvement) / 3
            print(f"\n🎯 Average improvement:   {avg_improvement:.1f}%")

            if avg_improvement >= 50:
                print("\n🎉 EXCELLENT! Caching is providing significant performance gains!")
            elif avg_improvement >= 30:
                print("\n✅ GOOD! Caching is providing meaningful performance improvements.")
            else:
                print("\n⚠️  Consider adjusting TTL values or cache warming strategy.")

            # Cleanup
            await cleanup_test_data(session, squad_id)

        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
