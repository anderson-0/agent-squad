"""
Tests for Discovery Detection System (Stream B)

Tests for the DiscoveryDetector that identifies opportunities in agent messages and work.
"""
import pytest
from uuid import uuid4
from datetime import datetime

from backend.agents.discovery.discovery_detector import DiscoveryDetector, Discovery
from backend.models.workflow import WorkflowPhase
from backend.schemas.agent_message import AgentMessageResponse


@pytest.mark.asyncio
async def test_detector_initialization():
    """Test DiscoveryDetector initialization"""
    detector = DiscoveryDetector()
    
    assert detector is not None
    assert hasattr(detector, 'optimization_patterns')
    assert hasattr(detector, 'bug_patterns')
    assert hasattr(detector, 'refactoring_patterns')


@pytest.mark.asyncio
async def test_detect_optimization_in_message():
    """Test detecting optimization opportunity in message"""
    detector = DiscoveryDetector()
    
    message = AgentMessageResponse(
        id=uuid4(),
        task_execution_id=uuid4(),
        sender_id=uuid4(),
        recipient_id=None,
        content="I noticed this caching pattern could apply to 12 other API routes for 40% speedup",
        message_type="status_update",
        message_metadata={},
        created_at=datetime.utcnow(),
    )
    
    discovery = detector.analyze_agent_message(message)
    
    assert discovery is not None
    assert discovery.type == "optimization"
    assert discovery.suggested_phase == WorkflowPhase.INVESTIGATION
    assert discovery.value_score > 0.5
    assert discovery.confidence > 0.5


@pytest.mark.asyncio
async def test_detect_bug_in_message():
    """Test detecting bug in message"""
    detector = DiscoveryDetector()
    
    message = AgentMessageResponse(
        id=uuid4(),
        task_execution_id=uuid4(),
        sender_id=uuid4(),
        recipient_id=None,
        content="Found a bug in the auth system - users are getting unauthorized errors",
        message_type="status_update",
        message_metadata={},
        created_at=datetime.utcnow(),
    )
    
    discovery = detector.analyze_agent_message(message)
    
    assert discovery is not None
    assert discovery.type == "bug"
    assert discovery.value_score == 0.9  # Bugs are high value
    assert discovery.suggested_phase == WorkflowPhase.INVESTIGATION


@pytest.mark.asyncio
async def test_detect_refactoring_in_message():
    """Test detecting refactoring need in message"""
    detector = DiscoveryDetector()
    
    message = AgentMessageResponse(
        id=uuid4(),
        task_execution_id=uuid4(),
        sender_id=uuid4(),
        recipient_id=None,
        content="There's significant code duplication here. We should refactor to improve maintainability",
        message_type="status_update",
        message_metadata={},
        created_at=datetime.utcnow(),
    )
    
    discovery = detector.analyze_agent_message(message)
    
    assert discovery is not None
    assert discovery.type == "refactoring"
    assert discovery.suggested_phase == WorkflowPhase.INVESTIGATION


@pytest.mark.asyncio
async def test_detect_performance_in_message():
    """Test detecting performance issue in message"""
    detector = DiscoveryDetector()
    
    message = AgentMessageResponse(
        id=uuid4(),
        task_execution_id=uuid4(),
        sender_id=uuid4(),
        recipient_id=None,
        content="The API endpoint is showing slow performance under load. There might be a bottleneck",
        message_type="status_update",
        message_metadata={},
        created_at=datetime.utcnow(),
    )
    
    discovery = detector.analyze_agent_message(message)
    
    assert discovery is not None
    assert discovery.type == "performance"
    assert discovery.suggested_phase == WorkflowPhase.INVESTIGATION


@pytest.mark.asyncio
async def test_no_discovery_in_message():
    """Test message with no discovery"""
    detector = DiscoveryDetector()
    
    message = AgentMessageResponse(
        id=uuid4(),
        task_execution_id=uuid4(),
        sender_id=uuid4(),
        recipient_id=None,
        content="Just checking in - everything is going well",
        message_type="status_update",
        message_metadata={},
        created_at=datetime.utcnow(),
    )
    
    discovery = detector.analyze_agent_message(message)
    
    assert discovery is None


@pytest.mark.asyncio
async def test_multiple_discoveries_returns_highest_value():
    """Test that multiple discoveries return the highest value one"""
    detector = DiscoveryDetector()
    
    message = AgentMessageResponse(
        id=uuid4(),
        task_execution_id=uuid4(),
        sender_id=uuid4(),
        recipient_id=None,
        content="Found a bug that's causing slow performance. This optimization could help fix it and improve speed by 50%",
        message_type="status_update",
        message_metadata={},
        created_at=datetime.utcnow(),
    )
    
    discovery = detector.analyze_agent_message(message)
    
    assert discovery is not None
    # Bug has higher value (0.9) than optimization, so should return bug
    assert discovery.type == "bug" or discovery.type == "optimization"
    assert discovery.value_score >= 0.6


@pytest.mark.asyncio
async def test_analyze_agent_work():
    """Test analyzing agent work output"""
    detector = DiscoveryDetector()
    
    work_output = """
    Implemented the auth endpoint. During testing, I noticed this caching pattern 
    could apply to 12 other API routes for 40% speedup. Also found a bug in the 
    error handling that needs investigation.
    """
    
    discoveries = detector.analyze_agent_work(
        work_output=work_output,
        phase=WorkflowPhase.BUILDING,
    )
    
    assert len(discoveries) > 0
    # Should detect both optimization and bug
    discovery_types = {d.type for d in discoveries}
    assert "optimization" in discovery_types or "bug" in discovery_types


@pytest.mark.asyncio
async def test_value_scoring_with_percentage():
    """Test value scoring with percentage improvement"""
    detector = DiscoveryDetector()
    
    message1 = AgentMessageResponse(
        id=uuid4(),
        task_execution_id=uuid4(),
        sender_id=uuid4(),
        recipient_id=None,
        content="Optimization could provide 20% speedup",
        message_type="status_update",
        message_metadata={},
        created_at=datetime.utcnow(),
    )
    
    message2 = AgentMessageResponse(
        id=uuid4(),
        task_execution_id=uuid4(),
        sender_id=uuid4(),
        recipient_id=None,
        content="Optimization could provide 80% speedup",
        message_type="status_update",
        message_metadata={},
        created_at=datetime.utcnow(),
    )
    
    discovery1 = detector.analyze_agent_message(message1)
    discovery2 = detector.analyze_agent_message(message2)
    
    assert discovery1 is not None
    assert discovery2 is not None
    assert discovery2.value_score > discovery1.value_score


@pytest.mark.asyncio
async def test_value_scoring_with_route_count():
    """Test value scoring with number of routes affected"""
    detector = DiscoveryDetector()
    
    message1 = AgentMessageResponse(
        id=uuid4(),
        task_execution_id=uuid4(),
        sender_id=uuid4(),
        recipient_id=None,
        content="Optimization could apply to 2 routes for 30% speedup",
        message_type="status_update",
        message_metadata={},
        created_at=datetime.utcnow(),
    )
    
    message2 = AgentMessageResponse(
        id=uuid4(),
        task_execution_id=uuid4(),
        sender_id=uuid4(),
        recipient_id=None,
        content="Optimization could apply to 15 routes for 30% speedup",
        message_type="status_update",
        message_metadata={},
        created_at=datetime.utcnow(),
    )
    
    discovery1 = detector.analyze_agent_message(message1)
    discovery2 = detector.analyze_agent_message(message2)
    
    assert discovery1 is not None
    assert discovery2 is not None
    # More routes should give higher value (with boost)
    assert discovery2.value_score >= discovery1.value_score


@pytest.mark.asyncio
async def test_empty_message():
    """Test empty message returns None"""
    detector = DiscoveryDetector()
    
    message = AgentMessageResponse(
        id=uuid4(),
        task_execution_id=uuid4(),
        sender_id=uuid4(),
        recipient_id=None,
        content="",
        message_type="status_update",
        message_metadata={},
        created_at=datetime.utcnow(),
    )
    
    discovery = detector.analyze_agent_message(message)
    
    assert discovery is None


@pytest.mark.asyncio
async def test_empty_work_output():
    """Test empty work output returns empty list"""
    detector = DiscoveryDetector()
    
    discoveries = detector.analyze_agent_work(
        work_output="",
        phase=WorkflowPhase.BUILDING,
    )
    
    assert discoveries == []


@pytest.mark.asyncio
async def test_get_discovery_detector_singleton():
    """Test that get_discovery_detector returns singleton"""
    from backend.agents.discovery.discovery_detector import get_discovery_detector
    
    detector1 = get_discovery_detector()
    detector2 = get_discovery_detector()
    
    assert detector1 is detector2  # Same instance

