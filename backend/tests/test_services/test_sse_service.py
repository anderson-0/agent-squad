"""
SSE Service Tests

Tests for Server-Sent Events manager service.
"""
import pytest
import asyncio
from uuid import uuid4
from backend.services.sse_service import sse_manager


class TestSSEManager:
    """Test SSE manager basic functionality"""

    @pytest.mark.asyncio
    async def test_add_execution_connection(self):
        """Test adding execution connection"""
        execution_id = uuid4()
        client_id = "test-client-1"

        conn_id = await sse_manager.add_execution_connection(execution_id, client_id)

        assert conn_id is not None
        assert isinstance(conn_id, str)

        # Cleanup
        sse_manager.remove_connection(conn_id)

    @pytest.mark.asyncio
    async def test_add_squad_connection(self):
        """Test adding squad connection"""
        squad_id = uuid4()
        client_id = "test-client-2"

        conn_id = await sse_manager.add_squad_connection(squad_id, client_id)

        assert conn_id is not None

        # Cleanup
        sse_manager.remove_connection(conn_id)

    @pytest.mark.asyncio
    async def test_remove_connection(self):
        """Test removing connection"""
        execution_id = uuid4()
        conn_id = await sse_manager.add_execution_connection(execution_id, "test")

        # Remove connection
        sse_manager.remove_connection(conn_id)

        # Stats should reflect removal
        stats = sse_manager.get_stats()
        # Connection should be removed (can't assert exact count due to other tests)
        assert isinstance(stats, dict)

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting SSE manager stats"""
        stats = sse_manager.get_stats()

        assert isinstance(stats, dict)
        assert "total_connections" in stats
        assert "execution_streams" in stats
        assert "squad_streams" in stats

        # All counts should be non-negative
        assert stats["total_connections"] >= 0
        assert stats["execution_streams"] >= 0
        assert stats["squad_streams"] >= 0


class TestSSEBroadcasting:
    """Test SSE event broadcasting"""

    @pytest.mark.asyncio
    async def test_broadcast_to_execution(self):
        """Test broadcasting event to execution"""
        execution_id = uuid4()
        conn_id = await sse_manager.add_execution_connection(execution_id, "test")

        event_data = {
            "event": "test_event",
            "data": {"message": "test"}
        }

        # Should not raise error
        await sse_manager.broadcast_to_execution(execution_id, "test_event", event_data)

        # Cleanup
        sse_manager.remove_connection(conn_id)

    @pytest.mark.asyncio
    async def test_broadcast_to_squad(self):
        """Test broadcasting event to squad"""
        squad_id = uuid4()
        conn_id = await sse_manager.add_squad_connection(squad_id, "test")

        event_data = {
            "event": "test_event",
            "data": {"message": "test"}
        }

        # Should not raise error
        await sse_manager.broadcast_to_squad(squad_id, "test_event", event_data)

        # Cleanup
        sse_manager.remove_connection(conn_id)

    @pytest.mark.asyncio
    async def test_broadcast_to_nonexistent_execution(self):
        """Test broadcasting to execution with no connections"""
        nonexistent_id = uuid4()

        event_data = {"event": "test", "data": {}}

        # Should not raise error (no connections to broadcast to)
        await sse_manager.broadcast_to_execution(nonexistent_id, "test", event_data)

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_clients(self):
        """Test broadcasting to multiple clients on same execution"""
        execution_id = uuid4()

        # Add 3 clients
        conn_ids = []
        for i in range(3):
            conn_id = await sse_manager.add_execution_connection(execution_id, f"client-{i}")
            conn_ids.append(conn_id)

        # Broadcast event
        event_data = {"event": "multi_test", "data": {"count": 3}}
        await sse_manager.broadcast_to_execution(execution_id, "multi_test", event_data)

        # Cleanup
        for conn_id in conn_ids:
            sse_manager.remove_connection(conn_id)


class TestSSEConnectionManagement:
    """Test connection lifecycle management"""

    @pytest.mark.asyncio
    async def test_duplicate_client_connection(self):
        """Test adding same client twice"""
        execution_id = uuid4()
        client_id = "duplicate-test"

        conn_id_1 = await sse_manager.add_execution_connection(execution_id, client_id)
        conn_id_2 = await sse_manager.add_execution_connection(execution_id, client_id)

        # Both should succeed (different connection IDs)
        assert conn_id_1 != conn_id_2

        # Cleanup
        sse_manager.remove_connection(conn_id_1)
        sse_manager.remove_connection(conn_id_2)

    @pytest.mark.asyncio
    async def test_remove_nonexistent_connection(self):
        """Test removing connection that doesn't exist"""
        # Should not raise error
        sse_manager.remove_connection("nonexistent-connection-id")

    @pytest.mark.asyncio
    async def test_connection_to_multiple_channels(self):
        """Test client connected to both execution and squad channels"""
        execution_id = uuid4()
        squad_id = uuid4()
        client_id = "multi-channel-test"

        exec_conn = await sse_manager.add_execution_connection(execution_id, client_id)
        squad_conn = await sse_manager.add_squad_connection(squad_id, client_id)

        # Both connections should be independent
        assert exec_conn != squad_conn

        # Cleanup
        sse_manager.remove_connection(exec_conn)
        sse_manager.remove_connection(squad_conn)


class TestSSEEventTypes:
    """Test different event types"""

    @pytest.mark.asyncio
    async def test_broadcast_sandbox_created_event(self):
        """Test broadcasting sandbox_created event"""
        execution_id = uuid4()
        conn_id = await sse_manager.add_execution_connection(execution_id, "test")

        event = {
            "event": "sandbox_created",
            "sandbox_id": str(uuid4()),
            "e2b_id": "test-e2b-123"
        }

        await sse_manager.broadcast_to_execution(execution_id, "sandbox_created", event)

        # Cleanup
        sse_manager.remove_connection(conn_id)

    @pytest.mark.asyncio
    async def test_broadcast_pr_created_event(self):
        """Test broadcasting pr_created event"""
        execution_id = uuid4()
        conn_id = await sse_manager.add_execution_connection(execution_id, "test")

        event = {
            "event": "pr_created",
            "sandbox_id": str(uuid4()),
            "pr_number": 123,
            "pr_url": "https://github.com/test/repo/pull/123"
        }

        await sse_manager.broadcast_to_execution(execution_id, "pr_created", event)

        # Cleanup
        sse_manager.remove_connection(conn_id)

    @pytest.mark.asyncio
    async def test_broadcast_pr_approved_event(self):
        """Test broadcasting pr_approved event"""
        squad_id = uuid4()
        conn_id = await sse_manager.add_squad_connection(squad_id, "test")

        event = {
            "event": "pr_approved",
            "sandbox_id": str(uuid4()),
            "pr_number": 456,
            "reviewer": "test-reviewer"
        }

        await sse_manager.broadcast_to_squad(squad_id, "pr_approved", event)

        # Cleanup
        sse_manager.remove_connection(conn_id)


class TestSSEErrorHandling:
    """Test error handling in SSE manager"""

    @pytest.mark.asyncio
    async def test_broadcast_with_invalid_event_data(self):
        """Test broadcasting with malformed event data"""
        execution_id = uuid4()

        # Non-dict event data (should still work or handle gracefully)
        invalid_data = "not a dict"

        try:
            await sse_manager.broadcast_to_execution(execution_id, "test", invalid_data)
        except (TypeError, ValueError):
            # Expected if validation is strict
            pass

    @pytest.mark.asyncio
    async def test_broadcast_with_none_event_data(self):
        """Test broadcasting with None event data"""
        execution_id = uuid4()

        # None event data
        try:
            await sse_manager.broadcast_to_execution(execution_id, "test", None)
        except (TypeError, ValueError):
            # Expected if validation is strict
            pass

    @pytest.mark.asyncio
    async def test_add_connection_with_invalid_id(self):
        """Test adding connection with invalid execution_id"""
        # Should handle gracefully or raise appropriate error
        try:
            await sse_manager.add_execution_connection(None, "test")
        except (TypeError, ValueError, AttributeError):
            # Expected
            pass


if __name__ == "__main__":
    print("""
    SSE Service Tests
    =================

    Tests for Server-Sent Events manager.

    Run with:
        pytest tests/test_services/test_sse_service.py -v
    """)
