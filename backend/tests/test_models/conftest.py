"""
Test fixtures for model tests
"""
import pytest
from uuid import uuid4

from backend.models import (
    User,
    Organization,
    Squad,
    SquadMember,
    AgentMessage,
    Project,
    Task,
    TaskExecution
)


@pytest.fixture
async def test_user(test_db):
    """Create a test user"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        password_hash="hashed_password_here"
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def test_organization(test_db, test_user):
    """Create a test organization"""
    org = Organization(
        id=uuid4(),
        name="Test Organization",
        owner_id=test_user.id
    )
    test_db.add(org)
    await test_db.commit()
    await test_db.refresh(org)
    return org


@pytest.fixture
async def test_squad(test_db, test_user, test_organization):
    """Create a test squad"""
    squad = Squad(
        id=uuid4(),
        name="Test Squad",
        user_id=test_user.id,
        org_id=test_organization.id
    )
    test_db.add(squad)
    await test_db.commit()
    await test_db.refresh(squad)
    return squad


@pytest.fixture
async def test_squad_member_backend(test_db, test_squad):
    """Create a backend developer squad member"""
    member = SquadMember(
        id=uuid4(),
        squad_id=test_squad.id,
        role="backend_developer",
        llm_provider="openai",
        llm_model="gpt-4",
        system_prompt="You are a backend developer"
    )
    test_db.add(member)
    await test_db.commit()
    await test_db.refresh(member)
    return member


@pytest.fixture
async def test_squad_member_tech_lead(test_db, test_squad):
    """Create a tech lead squad member"""
    member = SquadMember(
        id=uuid4(),
        squad_id=test_squad.id,
        role="tech_lead",
        llm_provider="openai",
        llm_model="gpt-4",
        system_prompt="You are a tech lead"
    )
    test_db.add(member)
    await test_db.commit()
    await test_db.refresh(member)
    return member


@pytest.fixture
async def test_squad_member_architect(test_db, test_squad):
    """Create a solution architect squad member"""
    member = SquadMember(
        id=uuid4(),
        squad_id=test_squad.id,
        role="solution_architect",
        llm_provider="openai",
        llm_model="gpt-4",
        system_prompt="You are a solution architect"
    )
    test_db.add(member)
    await test_db.commit()
    await test_db.refresh(member)
    return member


@pytest.fixture
async def test_squad_member_pm(test_db, test_squad):
    """Create a project manager squad member"""
    member = SquadMember(
        id=uuid4(),
        squad_id=test_squad.id,
        role="project_manager",
        llm_provider="openai",
        llm_model="gpt-4",
        system_prompt="You are a project manager"
    )
    test_db.add(member)
    await test_db.commit()
    await test_db.refresh(member)
    return member


@pytest.fixture
async def test_project(test_db, test_squad):
    """Create a test project"""
    project = Project(
        id=uuid4(),
        squad_id=test_squad.id,
        name="Test Project",
        description="Test project description"
    )
    test_db.add(project)
    await test_db.commit()
    await test_db.refresh(project)
    return project


@pytest.fixture
async def test_task(test_db, test_project):
    """Create a test task"""
    task = Task(
        id=uuid4(),
        project_id=test_project.id,
        title="Test Task",
        description="Test task description"
    )
    test_db.add(task)
    await test_db.commit()
    await test_db.refresh(task)
    return task


@pytest.fixture
async def test_task_execution(test_db, test_task, test_squad):
    """Create a test task execution"""
    execution = TaskExecution(
        id=uuid4(),
        task_id=test_task.id,
        squad_id=test_squad.id,
        status="in_progress"
    )
    test_db.add(execution)
    await test_db.commit()
    await test_db.refresh(execution)
    return execution


@pytest.fixture
async def test_message(test_db, test_squad_member_backend, test_squad_member_tech_lead, test_task_execution):
    """Create a test message"""
    message = AgentMessage(
        id=uuid4(),
        sender_id=test_squad_member_backend.id,
        recipient_id=test_squad_member_tech_lead.id,
        content="Test question",
        message_type="question",
        task_execution_id=test_task_execution.id
    )
    test_db.add(message)
    await test_db.commit()
    await test_db.refresh(message)
    return message
