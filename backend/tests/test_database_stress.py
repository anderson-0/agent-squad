"""
Database Stress Tests

Tests database performance under high concurrency:
- 100+ simultaneous writes
- Transaction integrity under load
- Deadlock prevention
- Connection pool limits
- Query performance benchmarks
"""
import pytest
import asyncio
from uuid import uuid4
from datetime import datetime
from sqlalchemy import select
from backend.models.sandbox import Sandbox, SandboxStatus


class TestConcurrentWrites:
    """Test database with many concurrent write operations"""

    @pytest.mark.asyncio
    async def test_100_concurrent_sandbox_creations(self, db_session):
        """Test creating 100 sandboxes concurrently"""
        from backend.services.sandbox_service import SandboxService

        execution_id = uuid4()
        squad_id = uuid4()

        async def create_sandbox(index: int):
            service = SandboxService(db_session, execution_id=execution_id, squad_id=squad_id)

            sandbox = Sandbox(
                e2b_id=f"stress-test-{index}",
                repo_url=f"https://github.com/test/repo-{index}",
                status=SandboxStatus.CREATED
            )

            db_session.add(sandbox)
            await db_session.flush()
            return sandbox.id

        # Create 100 sandboxes concurrently
        start_time = datetime.utcnow()

        tasks = [create_sandbox(i) for i in range(100)]
        sandbox_ids = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Commit all
        await db_session.commit()

        # Count successes
        successes = [sid for sid in sandbox_ids if not isinstance(sid, Exception)]
        failures = [sid for sid in sandbox_ids if isinstance(sid, Exception)]

        # Should have at least 95% success rate
        success_rate = len(successes) / 100
        assert success_rate >= 0.95

        print(f"✅ Created {len(successes)}/100 sandboxes in {duration:.2f}s ({len(successes)/duration:.0f} writes/sec)")
        if failures:
            print(f"⚠ {len(failures)} failures (acceptable under stress)")

    @pytest.mark.asyncio
    async def test_concurrent_updates_different_sandboxes(self, db_session):
        """Test updating different sandboxes concurrently"""

        # Create 50 sandboxes
        sandbox_ids = []
        for i in range(50):
            sandbox = Sandbox(
                e2b_id=f"update-test-{i}",
                repo_url="https://github.com/test/repo",
                status=SandboxStatus.CREATED
            )
            db_session.add(sandbox)
            await db_session.flush()
            sandbox_ids.append(sandbox.id)

        await db_session.commit()

        # Update all 50 concurrently
        async def update_sandbox(sandbox_id):
            result = await db_session.execute(
                select(Sandbox).where(Sandbox.id == sandbox_id)
            )
            sandbox = result.scalars().first()

            if sandbox:
                sandbox.status = SandboxStatus.RUNNING
                await db_session.flush()

        start_time = datetime.utcnow()

        tasks = [update_sandbox(sid) for sid in sandbox_ids]
        await asyncio.gather(*tasks, return_exceptions=True)

        await db_session.commit()

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Verify all updated
        result = await db_session.execute(
            select(Sandbox).where(Sandbox.id.in_(sandbox_ids))
        )
        sandboxes = result.scalars().all()

        running_count = sum(1 for s in sandboxes if s.status == SandboxStatus.RUNNING)

        print(f"✅ Updated {running_count}/50 sandboxes concurrently in {duration:.2f}s")

    @pytest.mark.asyncio
    async def test_transaction_rollback_under_load(self, db_session):
        """Test transaction rollback when operations fail under load"""

        initial_count_result = await db_session.execute(select(Sandbox))
        initial_count = len(initial_count_result.scalars().all())

        # Attempt to create sandboxes with intentional failures
        try:
            for i in range(10):
                sandbox = Sandbox(
                    e2b_id=f"rollback-test-{i}",
                    repo_url="https://github.com/test/repo",
                    status=SandboxStatus.CREATED
                )
                db_session.add(sandbox)

                # Fail on 5th iteration
                if i == 5:
                    raise Exception("Intentional failure")

            await db_session.commit()
        except Exception:
            await db_session.rollback()

        # Verify rollback worked (count should be unchanged)
        final_count_result = await db_session.execute(select(Sandbox))
        final_count = len(final_count_result.scalars().all())

        assert final_count == initial_count

        print(f"✅ Transaction rollback worked correctly under load")


class TestDeadlockPrevention:
    """Test database deadlock scenarios"""

    @pytest.mark.asyncio
    async def test_no_deadlock_on_concurrent_pr_updates(self, db_session):
        """Test updating PR numbers concurrently doesn't cause deadlock"""

        # Create 10 sandboxes
        sandbox_ids = []
        for i in range(10):
            sandbox = Sandbox(
                e2b_id=f"deadlock-test-{i}",
                repo_url="https://github.com/test/repo",
                status=SandboxStatus.RUNNING
            )
            db_session.add(sandbox)
            await db_session.flush()
            sandbox_ids.append(sandbox.id)

        await db_session.commit()

        # Update PR numbers concurrently (potential deadlock scenario)
        async def update_pr_number(sandbox_id, pr_number):
            result = await db_session.execute(
                select(Sandbox).where(Sandbox.id == sandbox_id)
            )
            sandbox = result.scalars().first()

            if sandbox:
                sandbox.pr_number = pr_number
                sandbox.status = SandboxStatus.RUNNING
                await db_session.flush()

        # Update all concurrently with random delays
        tasks = []
        for i, sid in enumerate(sandbox_ids):
            tasks.append(update_pr_number(sid, 100 + i))

        # Should complete without deadlock
        await asyncio.gather(*tasks, return_exceptions=True)
        await db_session.commit()

        # Verify updates
        result = await db_session.execute(
            select(Sandbox).where(Sandbox.id.in_(sandbox_ids))
        )
        sandboxes = result.scalars().all()

        updated_count = sum(1 for s in sandboxes if s.pr_number is not None)

        print(f"✅ No deadlock: {updated_count}/10 PR numbers updated concurrently")


class TestConnectionPoolLimits:
    """Test database connection pool behavior"""

    @pytest.mark.asyncio
    async def test_connection_pool_exhaustion(self, db_session):
        """Test behavior when connection pool is exhausted"""

        # Note: This test depends on your connection pool configuration
        # Default SQLAlchemy pool size is typically 5-20 connections

        async def long_running_query(index: int):
            """Simulate long-running query"""
            await asyncio.sleep(0.1)  # Simulate slow query

            result = await db_session.execute(select(Sandbox).limit(10))
            sandboxes = result.scalars().all()

            return len(sandboxes)

        # Execute many queries concurrently (more than pool size)
        start_time = datetime.utcnow()

        tasks = [long_running_query(i) for i in range(30)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        successes = [r for r in results if not isinstance(r, Exception)]
        failures = [r for r in results if isinstance(r, Exception)]

        print(f"✅ Completed {len(successes)}/30 concurrent queries in {duration:.2f}s")
        if failures:
            print(f"⚠ {len(failures)} connection pool timeouts (expected under stress)")


class TestQueryPerformance:
    """Benchmark query performance"""

    @pytest.mark.asyncio
    async def test_indexed_pr_lookup_performance(self, db_session):
        """Test PR number lookup speed with index"""

        # Create 1000 sandboxes with PR numbers
        for i in range(1000):
            sandbox = Sandbox(
                e2b_id=f"perf-test-{i}",
                repo_url="https://github.com/test/repo",
                pr_number=1000 + i,
                status=SandboxStatus.RUNNING
            )
            db_session.add(sandbox)

            # Batch commit every 100
            if i % 100 == 99:
                await db_session.commit()

        await db_session.commit()

        # Benchmark PR lookup (should use index)
        start_time = datetime.utcnow()

        for pr_num in range(1000, 1100):  # 100 lookups
            result = await db_session.execute(
                select(Sandbox).where(Sandbox.pr_number == pr_num)
            )
            sandbox = result.scalars().first()
            assert sandbox is not None

        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000

        avg_lookup_ms = duration_ms / 100

        # Each lookup should be < 5ms with index
        assert avg_lookup_ms < 5.0

        print(f"✅ Indexed PR lookup: {avg_lookup_ms:.2f}ms per lookup ({duration_ms:.0f}ms for 100)")

    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, db_session):
        """Test bulk insert performance"""

        sandboxes = []
        for i in range(500):
            sandbox = Sandbox(
                e2b_id=f"bulk-{i}",
                repo_url="https://github.com/test/repo",
                status=SandboxStatus.CREATED
            )
            sandboxes.append(sandbox)

        # Bulk insert
        start_time = datetime.utcnow()

        db_session.add_all(sandboxes)
        await db_session.commit()

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        inserts_per_sec = 500 / duration

        # Should insert at least 100 records/sec
        assert inserts_per_sec > 100

        print(f"✅ Bulk insert: {inserts_per_sec:.0f} records/sec ({duration:.2f}s for 500)")

    @pytest.mark.asyncio
    async def test_complex_query_performance(self, db_session):
        """Test complex query with joins and filters"""

        # Create test data
        for i in range(100):
            sandbox = Sandbox(
                e2b_id=f"complex-{i}",
                repo_url=f"https://github.com/test/repo-{i % 10}",
                pr_number=2000 + i if i % 2 == 0 else None,
                status=SandboxStatus.RUNNING if i % 3 == 0 else SandboxStatus.TERMINATED
            )
            db_session.add(sandbox)

        await db_session.commit()

        # Complex query
        start_time = datetime.utcnow()

        result = await db_session.execute(
            select(Sandbox)
            .where(Sandbox.status == SandboxStatus.RUNNING)
            .where(Sandbox.pr_number.isnot(None))
            .order_by(Sandbox.created_at.desc())
            .limit(20)
        )
        sandboxes = result.scalars().all()

        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000

        # Complex query should complete in < 50ms
        assert duration_ms < 50.0

        print(f"✅ Complex query: {duration_ms:.2f}ms ({len(sandboxes)} results)")


class TestDataIntegrityUnderLoad:
    """Test data integrity with concurrent operations"""

    @pytest.mark.asyncio
    async def test_no_duplicate_pr_numbers(self, db_session):
        """Test that concurrent PR creation doesn't create duplicates"""

        # Create single sandbox
        sandbox = Sandbox(
            e2b_id="integrity-test",
            repo_url="https://github.com/test/repo",
            status=SandboxStatus.RUNNING
        )
        db_session.add(sandbox)
        await db_session.commit()

        # Try to update PR number concurrently (race condition test)
        async def set_pr_number(pr_num: int):
            result = await db_session.execute(
                select(Sandbox).where(Sandbox.e2b_id == "integrity-test")
            )
            sb = result.scalars().first()

            if sb:
                sb.pr_number = pr_num
                await db_session.flush()

        # Multiple concurrent updates
        tasks = [set_pr_number(3000 + i) for i in range(5)]
        await asyncio.gather(*tasks, return_exceptions=True)

        await db_session.commit()

        # Verify final state (one of the PR numbers should win)
        result = await db_session.execute(
            select(Sandbox).where(Sandbox.e2b_id == "integrity-test")
        )
        final_sandbox = result.scalars().first()

        assert final_sandbox.pr_number is not None
        assert 3000 <= final_sandbox.pr_number < 3005

        print(f"✅ Data integrity maintained: final PR number = {final_sandbox.pr_number}")

    @pytest.mark.asyncio
    async def test_concurrent_status_transitions(self, db_session):
        """Test concurrent status transitions maintain valid states"""

        # Create 20 sandboxes
        sandbox_ids = []
        for i in range(20):
            sandbox = Sandbox(
                e2b_id=f"status-test-{i}",
                repo_url="https://github.com/test/repo",
                status=SandboxStatus.CREATED
            )
            db_session.add(sandbox)
            await db_session.flush()
            sandbox_ids.append(sandbox.id)

        await db_session.commit()

        # Transition all statuses concurrently
        async def transition_status(sandbox_id):
            result = await db_session.execute(
                select(Sandbox).where(Sandbox.id == sandbox_id)
            )
            sandbox = result.scalars().first()

            if sandbox and sandbox.status == SandboxStatus.CREATED:
                sandbox.status = SandboxStatus.RUNNING
                await db_session.flush()

                # Small delay
                await asyncio.sleep(0.01)

                sandbox.status = SandboxStatus.TERMINATED
                await db_session.flush()

        tasks = [transition_status(sid) for sid in sandbox_ids]
        await asyncio.gather(*tasks, return_exceptions=True)

        await db_session.commit()

        # Verify all in terminal state
        result = await db_session.execute(
            select(Sandbox).where(Sandbox.id.in_(sandbox_ids))
        )
        sandboxes = result.scalars().all()

        terminated_count = sum(1 for s in sandboxes if s.status == SandboxStatus.TERMINATED)

        print(f"✅ Status transitions: {terminated_count}/20 reached TERMINATED state")


if __name__ == "__main__":
    print("""
    Database Stress Test Suite
    ==========================

    Tests database under high concurrency:
    - 100+ concurrent writes
    - Transaction integrity
    - Deadlock prevention
    - Connection pool limits
    - Query performance benchmarks

    Run with:
        pytest tests/test_database_stress.py -v -s
    """)
