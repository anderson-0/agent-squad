"""
SSE Broadcasting Stress Tests

Tests SSE manager under high load conditions:
- 100+ concurrent connections
- Rapid event broadcasting
- Connection lifecycle (connect, disconnect, reconnect)
- Memory leaks and resource cleanup
- Event queue handling
"""
import pytest
import asyncio
from uuid import uuid4
from datetime import datetime
from typing import List, Dict, Any


class TestSSEConnectionStress:
    """Test SSE manager with many concurrent connections"""

    @pytest.mark.asyncio
    async def test_100_concurrent_connections(self):
        """Test SSE manager with 100 concurrent connections"""
        from backend.services.sse_service import sse_manager

        execution_id = uuid4()
        connection_ids = []

        # Create 100 concurrent connections
        for i in range(100):
            conn_id = await sse_manager.add_execution_connection(execution_id, f"client-{i}")
            connection_ids.append(conn_id)

        # Verify all connections registered
        stats = sse_manager.get_stats()
        assert stats["execution_streams"] >= 100

        # Broadcast event to all connections
        test_event = {
            "event": "test",
            "data": {"message": "stress test"}
        }

        await sse_manager.broadcast_to_execution(execution_id, "test", test_event)

        # Cleanup
        for conn_id in connection_ids:
            sse_manager.remove_connection(conn_id)

        print(f"✅ Successfully handled 100 concurrent connections")

    @pytest.mark.asyncio
    async def test_rapid_connect_disconnect(self):
        """Test rapid connection/disconnection cycles"""
        from backend.services.sse_service import sse_manager

        execution_id = uuid4()

        # Simulate 50 rapid connect/disconnect cycles
        for i in range(50):
            conn_id = await sse_manager.add_execution_connection(execution_id, f"client-{i}")
            await asyncio.sleep(0.01)  # Small delay
            sse_manager.remove_connection(conn_id)

        # Verify no memory leaks (all connections cleaned up)
        stats = sse_manager.get_stats()

        # There may be some active test connections, but not 50
        assert stats["total_connections"] < 50

        print(f"✅ Handled 50 rapid connect/disconnect cycles")

    @pytest.mark.asyncio
    async def test_connection_lifecycle_management(self):
        """Test connection cleanup on client disconnect"""
        from backend.services.sse_service import sse_manager

        execution_id = uuid4()

        # Create connections
        conn_id_1 = await sse_manager.add_execution_connection(execution_id, "client-1")
        conn_id_2 = await sse_manager.add_execution_connection(execution_id, "client-2")
        conn_id_3 = await sse_manager.add_execution_connection(execution_id, "client-3")

        initial_stats = sse_manager.get_stats()
        initial_count = initial_stats["total_connections"]

        # Disconnect client-2
        sse_manager.remove_connection(conn_id_2)

        after_disconnect = sse_manager.get_stats()
        assert after_disconnect["total_connections"] == initial_count - 1

        # Reconnect client-2
        conn_id_4 = await sse_manager.add_execution_connection(execution_id, "client-2")

        after_reconnect = sse_manager.get_stats()
        assert after_reconnect["total_connections"] == initial_count

        # Cleanup
        for conn_id in [conn_id_1, conn_id_3, conn_id_4]:
            sse_manager.remove_connection(conn_id)

        print(f"✅ Connection lifecycle managed correctly")


class TestSSEEventBroadcastingStress:
    """Test SSE event broadcasting under load"""

    @pytest.mark.asyncio
    async def test_rapid_event_broadcasting(self):
        """Test broadcasting 1000 events rapidly"""
        from backend.services.sse_service import sse_manager

        execution_id = uuid4()
        conn_id = await sse_manager.add_execution_connection(execution_id, "stress-client")

        # Broadcast 1000 events rapidly
        start_time = datetime.utcnow()

        for i in range(1000):
            event = {
                "event": "test",
                "sequence": i,
                "timestamp": datetime.utcnow().isoformat()
            }
            await sse_manager.broadcast_to_execution(execution_id, "test", event)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Cleanup
        sse_manager.remove_connection(conn_id)

        # Should complete in under 2 seconds (500 events/sec)
        assert duration < 2.0

        print(f"✅ Broadcast 1000 events in {duration:.2f}s ({1000/duration:.0f} events/sec)")

    @pytest.mark.asyncio
    async def test_dual_channel_stress(self):
        """Test broadcasting to both execution and squad channels simultaneously"""
        from backend.services.sse_service import sse_manager

        execution_id = uuid4()
        squad_id = uuid4()

        # Create connections on both channels
        exec_conn = await sse_manager.add_execution_connection(execution_id, "exec-client")
        squad_conn = await sse_manager.add_squad_connection(squad_id, "squad-client")

        # Broadcast 100 events to both channels concurrently
        tasks = []
        for i in range(100):
            event = {"event": "test", "sequence": i}

            # Broadcast to both channels
            tasks.append(sse_manager.broadcast_to_execution(execution_id, "test", event))
            tasks.append(sse_manager.broadcast_to_squad(squad_id, "test", event))

        await asyncio.gather(*tasks)

        # Cleanup
        sse_manager.remove_connection(exec_conn)
        sse_manager.remove_connection(squad_conn)

        print(f"✅ Successfully broadcast to dual channels under stress")

    @pytest.mark.asyncio
    async def test_large_event_payload(self):
        """Test broadcasting large event payloads"""
        from backend.services.sse_service import sse_manager

        execution_id = uuid4()
        conn_id = await sse_manager.add_execution_connection(execution_id, "large-payload-client")

        # Create large payload (10KB)
        large_data = {
            "event": "test",
            "large_field": "x" * 10000,  # 10KB string
            "nested": {
                "data": ["item"] * 1000
            }
        }

        # Should handle large payload without errors
        await sse_manager.broadcast_to_execution(execution_id, "test", large_data)

        # Cleanup
        sse_manager.remove_connection(conn_id)

        print(f"✅ Successfully broadcast large payload (>10KB)")


class TestSSEErrorRecovery:
    """Test SSE manager error handling and recovery"""

    @pytest.mark.asyncio
    async def test_broadcast_to_disconnected_client(self):
        """Test broadcasting to a client that disconnected"""
        from backend.services.sse_service import sse_manager

        execution_id = uuid4()

        # Create connection then immediately disconnect
        conn_id = await sse_manager.add_execution_connection(execution_id, "temp-client")
        sse_manager.remove_connection(conn_id)

        # Try broadcasting (should not raise error)
        event = {"event": "test", "data": "message"}

        # Should succeed without error (no clients to broadcast to)
        await sse_manager.broadcast_to_execution(execution_id, "test", event)

        print(f"✅ Broadcasting to disconnected client handled gracefully")

    @pytest.mark.asyncio
    async def test_concurrent_broadcast_and_disconnect(self):
        """Test broadcasting while clients are disconnecting"""
        from backend.services.sse_service import sse_manager

        execution_id = uuid4()

        # Create 10 connections
        conn_ids = []
        for i in range(10):
            conn_id = await sse_manager.add_execution_connection(execution_id, f"client-{i}")
            conn_ids.append(conn_id)

        # Concurrently broadcast events and disconnect clients
        async def broadcast_events():
            for i in range(50):
                event = {"event": "test", "sequence": i}
                await sse_manager.broadcast_to_execution(execution_id, "test", event)
                await asyncio.sleep(0.01)

        async def disconnect_clients():
            for conn_id in conn_ids:
                await asyncio.sleep(0.05)
                sse_manager.remove_connection(conn_id)

        # Run concurrently
        await asyncio.gather(
            broadcast_events(),
            disconnect_clients()
        )

        print(f"✅ Handled concurrent broadcast and disconnections")

    @pytest.mark.asyncio
    async def test_memory_leak_prevention(self):
        """Test that connections are properly cleaned up to prevent memory leaks"""
        from backend.services.sse_service import sse_manager

        initial_stats = sse_manager.get_stats()
        initial_count = initial_stats["total_connections"]

        # Create and destroy 100 connections
        for i in range(100):
            execution_id = uuid4()
            conn_id = await sse_manager.add_execution_connection(execution_id, f"temp-{i}")
            sse_manager.remove_connection(conn_id)

        # Check final stats
        final_stats = sse_manager.get_stats()
        final_count = final_stats["total_connections"]

        # Should return to approximately initial count (allow some variance for other tests)
        assert abs(final_count - initial_count) < 10

        print(f"✅ No memory leaks detected (initial: {initial_count}, final: {final_count})")


class TestSSEPerformanceBenchmarks:
    """Benchmark SSE manager performance"""

    @pytest.mark.asyncio
    async def test_connection_creation_performance(self):
        """Benchmark connection creation speed"""
        from backend.services.sse_service import sse_manager

        execution_id = uuid4()

        start_time = datetime.utcnow()
        conn_ids = []

        # Create 100 connections
        for i in range(100):
            conn_id = await sse_manager.add_execution_connection(execution_id, f"perf-{i}")
            conn_ids.append(conn_id)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Cleanup
        for conn_id in conn_ids:
            sse_manager.remove_connection(conn_id)

        connections_per_sec = 100 / duration

        # Should create at least 100 connections/sec
        assert connections_per_sec > 100

        print(f"✅ Connection creation: {connections_per_sec:.0f} connections/sec ({duration:.2f}s for 100)")

    @pytest.mark.asyncio
    async def test_broadcast_latency(self):
        """Measure broadcast latency"""
        from backend.services.sse_service import sse_manager

        execution_id = uuid4()
        conn_id = await sse_manager.add_execution_connection(execution_id, "latency-client")

        # Measure single broadcast latency
        latencies = []

        for _ in range(100):
            start = datetime.utcnow()

            event = {"event": "test", "timestamp": start.isoformat()}
            await sse_manager.broadcast_to_execution(execution_id, "test", event)

            end = datetime.utcnow()
            latency_ms = (end - start).total_seconds() * 1000
            latencies.append(latency_ms)

        # Cleanup
        sse_manager.remove_connection(conn_id)

        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)

        # Average latency should be < 10ms
        assert avg_latency < 10.0

        print(f"✅ Broadcast latency: avg={avg_latency:.2f}ms, max={max_latency:.2f}ms")

    @pytest.mark.asyncio
    async def test_fanout_performance(self):
        """Test broadcast performance with many recipients"""
        from backend.services.sse_service import sse_manager

        execution_id = uuid4()

        # Create 50 connections
        conn_ids = []
        for i in range(50):
            conn_id = await sse_manager.add_execution_connection(execution_id, f"fanout-{i}")
            conn_ids.append(conn_id)

        # Broadcast single event to all 50 clients
        start_time = datetime.utcnow()

        event = {"event": "test", "data": "fanout test"}
        await sse_manager.broadcast_to_execution(execution_id, "test", event)

        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000

        # Cleanup
        for conn_id in conn_ids:
            sse_manager.remove_connection(conn_id)

        # Fanout to 50 clients should complete in < 100ms
        assert duration_ms < 100.0

        print(f"✅ Fanout to 50 clients: {duration_ms:.2f}ms")


if __name__ == "__main__":
    print("""
    SSE Broadcasting Stress Test Suite
    ===================================

    Tests SSE manager under high load:
    - 100+ concurrent connections
    - 1000+ rapid events
    - Connection lifecycle
    - Error recovery
    - Performance benchmarks

    Run with:
        pytest tests/test_sse_stress.py -v -s
    """)
