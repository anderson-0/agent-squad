"""
Tests for Message Utilities

Tests for helper functions that enrich message metadata.
"""
import pytest
from uuid import uuid4, UUID

from backend.agents.communication.message_utils import (
    _generate_agent_name,
    get_agent_details,
    get_agent_details_bulk,
    get_conversation_thread_id,
    clear_agent_cache,
)
from backend.models.squad import SquadMember


class TestGenerateAgentName:
    """Tests for _generate_agent_name function"""

    def test_generate_name_without_specialization(self):
        """Test generating name without specialization"""
        name = _generate_agent_name("backend_developer")
        assert name == "Backend Dev"

    def test_generate_name_with_specialization(self):
        """Test generating name with specialization"""
        name = _generate_agent_name("backend_developer", "python_fastapi")
        assert name == "Backend Dev (FastAPI)"

    def test_generate_name_project_manager(self):
        """Test PM name generation"""
        name = _generate_agent_name("project_manager")
        assert name == "Project Manager"

    def test_generate_name_tech_lead(self):
        """Test TL name generation"""
        name = _generate_agent_name("tech_lead")
        assert name == "Tech Lead"

    def test_generate_name_frontend_with_react(self):
        """Test frontend dev with React"""
        name = _generate_agent_name("frontend_developer", "react_nextjs")
        assert name == "Frontend Dev (Next.js)"

    def test_generate_name_devops_with_k8s(self):
        """Test DevOps with Kubernetes"""
        name = _generate_agent_name("devops_engineer", "kubernetes")
        assert name == "DevOps Engineer (K8s)"

    def test_generate_name_unknown_role(self):
        """Test unknown role"""
        name = _generate_agent_name("custom_role")
        assert name == "Custom Role"  # Title case fallback

    def test_generate_name_unknown_specialization(self):
        """Test unknown specialization"""
        name = _generate_agent_name("backend_developer", "unknown_spec")
        assert name == "Backend Dev (Unknown Spec)"


@pytest.mark.asyncio
class TestGetAgentDetails:
    """Tests for get_agent_details function"""

    async def test_get_agent_details_success(self, db_session, sample_squad):
        """Test getting agent details successfully"""
        # Create a squad member
        member = SquadMember(
            id=uuid4(),
            squad_id=sample_squad.id,
            role="backend_developer",
            specialization="python_fastapi",
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt="Test prompt",
            is_active=True,
        )
        db_session.add(member)
        await db_session.commit()

        # Get details
        details = await get_agent_details(db_session, member.id)

        assert details is not None
        assert details.agent_id == member.id
        assert details.role == "backend_developer"
        assert details.name == "Backend Dev (FastAPI)"
        assert details.specialization == "python_fastapi"
        assert details.llm_provider == "openai"
        assert details.llm_model == "gpt-4"

    async def test_get_agent_details_not_found(self, db_session):
        """Test getting details for non-existent agent"""
        details = await get_agent_details(db_session, uuid4())
        assert details is None

    async def test_get_agent_details_caching(self, db_session, sample_squad):
        """Test that agent details are cached"""
        # Create a squad member
        member = SquadMember(
            id=uuid4(),
            squad_id=sample_squad.id,
            role="tech_lead",
            specialization=None,
            llm_provider="anthropic",
            llm_model="claude-3-sonnet-20240229",
            system_prompt="Test prompt",
            is_active=True,
        )
        db_session.add(member)
        await db_session.commit()

        # Clear cache first
        clear_agent_cache()

        # First call - should hit database
        details1 = await get_agent_details(db_session, member.id, use_cache=True)

        # Second call - should use cache
        details2 = await get_agent_details(db_session, member.id, use_cache=True)

        # Should be the same object (from cache)
        assert details1 is details2

    async def test_get_agent_details_no_cache(self, db_session, sample_squad):
        """Test getting details without caching"""
        member = SquadMember(
            id=uuid4(),
            squad_id=sample_squad.id,
            role="qa_tester",
            specialization=None,
            llm_provider="openai",
            llm_model="gpt-3.5-turbo",
            system_prompt="Test prompt",
            is_active=True,
        )
        db_session.add(member)
        await db_session.commit()

        # Clear cache
        clear_agent_cache()

        # Get without cache
        details1 = await get_agent_details(db_session, member.id, use_cache=False)
        details2 = await get_agent_details(db_session, member.id, use_cache=False)

        # Should be different objects (not cached)
        assert details1 is not details2
        assert details1.agent_id == details2.agent_id


@pytest.mark.asyncio
class TestGetAgentDetailsBulk:
    """Tests for get_agent_details_bulk function"""

    async def test_get_bulk_details(self, db_session, sample_squad):
        """Test getting multiple agent details"""
        # Create multiple members
        member1 = SquadMember(
            id=uuid4(),
            squad_id=sample_squad.id,
            role="backend_developer",
            specialization="python_fastapi",
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt="Test",
            is_active=True,
        )
        member2 = SquadMember(
            id=uuid4(),
            squad_id=sample_squad.id,
            role="frontend_developer",
            specialization="react_nextjs",
            llm_provider="anthropic",
            llm_model="claude-3-sonnet",
            system_prompt="Test",
            is_active=True,
        )
        db_session.add_all([member1, member2])
        await db_session.commit()

        # Clear cache
        clear_agent_cache()

        # Get bulk details
        details_map = await get_agent_details_bulk(
            db_session,
            [member1.id, member2.id],
            use_cache=True
        )

        assert len(details_map) == 2
        assert member1.id in details_map
        assert member2.id in details_map

        assert details_map[member1.id].name == "Backend Dev (FastAPI)"
        assert details_map[member2.id].name == "Frontend Dev (Next.js)"

    async def test_get_bulk_details_partial_cache(self, db_session, sample_squad):
        """Test bulk get with some agents already cached"""
        # Create members
        member1 = SquadMember(
            id=uuid4(),
            squad_id=sample_squad.id,
            role="backend_developer",
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt="Test",
            is_active=True,
        )
        member2 = SquadMember(
            id=uuid4(),
            squad_id=sample_squad.id,
            role="frontend_developer",
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt="Test",
            is_active=True,
        )
        db_session.add_all([member1, member2])
        await db_session.commit()

        # Clear cache
        clear_agent_cache()

        # Cache member1
        await get_agent_details(db_session, member1.id, use_cache=True)

        # Get bulk (member1 from cache, member2 from DB)
        details_map = await get_agent_details_bulk(
            db_session,
            [member1.id, member2.id],
            use_cache=True
        )

        assert len(details_map) == 2
        assert member1.id in details_map
        assert member2.id in details_map


class TestGetConversationThreadId:
    """Tests for get_conversation_thread_id function"""

    def test_get_thread_id_explicit(self):
        """Test extracting explicit thread_id"""
        metadata = {"thread_id": "thread-123"}
        thread_id = get_conversation_thread_id(metadata)
        assert thread_id == "thread-123"

    def test_get_thread_id_from_reply(self):
        """Test extracting thread_id from reply_to_message_id"""
        metadata = {"reply_to_message_id": "msg-456"}
        thread_id = get_conversation_thread_id(metadata)
        assert thread_id == "msg-456"

    def test_get_thread_id_from_task(self):
        """Test generating thread_id from task_id"""
        metadata = {"task_id": "PROJ-123"}
        thread_id = get_conversation_thread_id(metadata)
        assert thread_id == "task_PROJ-123"

    def test_get_thread_id_priority(self):
        """Test thread_id takes priority over reply_to_message_id"""
        metadata = {
            "thread_id": "thread-123",
            "reply_to_message_id": "msg-456"
        }
        thread_id = get_conversation_thread_id(metadata)
        assert thread_id == "thread-123"

    def test_get_thread_id_no_metadata(self):
        """Test with no metadata"""
        thread_id = get_conversation_thread_id(None)
        assert thread_id is None

    def test_get_thread_id_empty_metadata(self):
        """Test with empty metadata"""
        thread_id = get_conversation_thread_id({})
        assert thread_id is None


class TestClearAgentCache:
    """Tests for clear_agent_cache function"""

    def test_clear_specific_agent(self):
        """Test clearing specific agent from cache"""
        from backend.agents.communication.message_utils import _agent_details_cache
        from backend.agents.communication.message_utils import AgentDetails

        # Add to cache
        agent_id = uuid4()
        _agent_details_cache[agent_id] = AgentDetails(
            agent_id=agent_id,
            role="backend_developer",
            name="Test Agent"
        )

        # Clear specific agent
        clear_agent_cache(agent_id)

        assert agent_id not in _agent_details_cache

    def test_clear_all_cache(self):
        """Test clearing all agents from cache"""
        from backend.agents.communication.message_utils import _agent_details_cache
        from backend.agents.communication.message_utils import AgentDetails

        # Add multiple to cache
        for i in range(3):
            agent_id = uuid4()
            _agent_details_cache[agent_id] = AgentDetails(
                agent_id=agent_id,
                role="backend_developer",
                name=f"Test Agent {i}"
            )

        # Clear all
        clear_agent_cache()

        assert len(_agent_details_cache) == 0


class TestAgentDetailsToDict:
    """Tests for AgentDetails.to_dict method"""

    def test_to_dict_full(self):
        """Test converting full AgentDetails to dict"""
        from backend.agents.communication.message_utils import AgentDetails

        agent_id = uuid4()
        details = AgentDetails(
            agent_id=agent_id,
            role="backend_developer",
            name="Backend Dev (FastAPI)",
            specialization="python_fastapi",
            llm_provider="openai",
            llm_model="gpt-4",
        )

        result = details.to_dict()

        assert result["agent_id"] == str(agent_id)
        assert result["role"] == "backend_developer"
        assert result["name"] == "Backend Dev (FastAPI)"
        assert result["specialization"] == "python_fastapi"
        assert result["llm_provider"] == "openai"
        assert result["llm_model"] == "gpt-4"

    def test_to_dict_minimal(self):
        """Test converting minimal AgentDetails to dict"""
        from backend.agents.communication.message_utils import AgentDetails

        agent_id = uuid4()
        details = AgentDetails(
            agent_id=agent_id,
            role="qa_tester",
            name="QA Tester",
        )

        result = details.to_dict()

        assert result["agent_id"] == str(agent_id)
        assert result["role"] == "qa_tester"
        assert result["name"] == "QA Tester"
        assert result["specialization"] is None
        assert result["llm_provider"] is None
        assert result["llm_model"] is None
