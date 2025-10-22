"""
Message Utilities

Helper functions for message handling and metadata enrichment.
"""
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.squad import SquadMember


class AgentDetails:
    """Simple data class for agent details"""
    def __init__(
        self,
        agent_id: UUID,
        role: str,
        name: str,
        specialization: Optional[str] = None,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
    ):
        self.agent_id = agent_id
        self.role = role
        self.name = name
        self.specialization = specialization
        self.llm_provider = llm_provider
        self.llm_model = llm_model

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "agent_id": str(self.agent_id),
            "role": self.role,
            "name": self.name,
            "specialization": self.specialization,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
        }


# In-memory cache for agent details (avoid repeated DB queries)
_agent_details_cache: Dict[UUID, AgentDetails] = {}


async def get_agent_details(
    db: AsyncSession,
    agent_id: UUID,
    use_cache: bool = True,
) -> Optional[AgentDetails]:
    """
    Get agent details by ID.

    This function retrieves agent information from the database and creates
    a user-friendly name based on the role and a counter.

    Args:
        db: Database session
        agent_id: Agent (SquadMember) UUID
        use_cache: Whether to use in-memory cache (default: True)

    Returns:
        AgentDetails if found, None otherwise

    Examples:
        >>> details = await get_agent_details(db, agent_id)
        >>> print(details.name)  # "Backend Dev #1"
        >>> print(details.role)  # "backend_developer"
    """
    # Check cache first
    if use_cache and agent_id in _agent_details_cache:
        return _agent_details_cache[agent_id]

    # Query database
    result = await db.execute(
        select(SquadMember).where(SquadMember.id == agent_id)
    )
    squad_member = result.scalar_one_or_none()

    if not squad_member:
        return None

    # Generate user-friendly name
    name = _generate_agent_name(squad_member.role, squad_member.specialization)

    # Create agent details
    details = AgentDetails(
        agent_id=agent_id,
        role=squad_member.role,
        name=name,
        specialization=squad_member.specialization,
        llm_provider=squad_member.llm_provider,
        llm_model=squad_member.llm_model,
    )

    # Cache it
    if use_cache:
        _agent_details_cache[agent_id] = details

    return details


def _generate_agent_name(role: str, specialization: Optional[str] = None) -> str:
    """
    Generate a user-friendly agent name.

    Args:
        role: Agent role (e.g., "backend_developer")
        specialization: Optional specialization (e.g., "python_fastapi")

    Returns:
        Formatted name (e.g., "Backend Dev #1", "Frontend Dev (React)")

    Examples:
        >>> _generate_agent_name("backend_developer")
        "Backend Developer"
        >>> _generate_agent_name("backend_developer", "python_fastapi")
        "Backend Dev (FastAPI)"
        >>> _generate_agent_name("project_manager")
        "Project Manager"
    """
    # Map roles to display names
    role_display_names = {
        "project_manager": "Project Manager",
        "tech_lead": "Tech Lead",
        "backend_developer": "Backend Dev",
        "frontend_developer": "Frontend Dev",
        "qa_tester": "QA Tester",
        "solution_architect": "Solution Architect",
        "devops_engineer": "DevOps Engineer",
        "ai_engineer": "AI Engineer",
        "designer": "Designer",
    }

    # Map specializations to short names
    specialization_display_names = {
        # Backend
        "python_fastapi": "FastAPI",
        "python_django": "Django",
        "python_flask": "Flask",
        "nodejs_express": "Express",
        "nodejs_nestjs": "NestJS",
        "ruby_rails": "Rails",
        "go_gin": "Gin",
        "java_spring": "Spring",
        # Frontend
        "react_nextjs": "Next.js",
        "react": "React",
        "vue_nuxt": "Nuxt",
        "vue": "Vue",
        "angular": "Angular",
        "svelte": "Svelte",
        # DevOps
        "kubernetes": "K8s",
        "docker": "Docker",
        "terraform": "Terraform",
        "aws": "AWS",
        "gcp": "GCP",
        "azure": "Azure",
    }

    # Get base name
    base_name = role_display_names.get(role, role.replace("_", " ").title())

    # Add specialization if present
    if specialization:
        spec_name = specialization_display_names.get(
            specialization,
            specialization.replace("_", " ").title()
        )
        return f"{base_name} ({spec_name})"

    return base_name


async def get_agent_details_bulk(
    db: AsyncSession,
    agent_ids: list[UUID],
    use_cache: bool = True,
) -> Dict[UUID, AgentDetails]:
    """
    Get details for multiple agents in one query.

    More efficient than calling get_agent_details multiple times.

    Args:
        db: Database session
        agent_ids: List of agent UUIDs
        use_cache: Whether to use in-memory cache

    Returns:
        Dictionary mapping agent_id to AgentDetails
    """
    results = {}
    uncached_ids = []

    # Check cache first
    if use_cache:
        for agent_id in agent_ids:
            if agent_id in _agent_details_cache:
                results[agent_id] = _agent_details_cache[agent_id]
            else:
                uncached_ids.append(agent_id)
    else:
        uncached_ids = agent_ids

    # Query database for uncached agents
    if uncached_ids:
        result = await db.execute(
            select(SquadMember).where(SquadMember.id.in_(uncached_ids))
        )
        squad_members = result.scalars().all()

        for squad_member in squad_members:
            name = _generate_agent_name(squad_member.role, squad_member.specialization)

            details = AgentDetails(
                agent_id=squad_member.id,
                role=squad_member.role,
                name=name,
                specialization=squad_member.specialization,
                llm_provider=squad_member.llm_provider,
                llm_model=squad_member.llm_model,
            )

            results[squad_member.id] = details

            # Cache it
            if use_cache:
                _agent_details_cache[squad_member.id] = details

    return results


def clear_agent_cache(agent_id: Optional[UUID] = None):
    """
    Clear agent details cache.

    Args:
        agent_id: Specific agent to clear, or None to clear all
    """
    global _agent_details_cache

    if agent_id is None:
        _agent_details_cache.clear()
    elif agent_id in _agent_details_cache:
        del _agent_details_cache[agent_id]


def get_conversation_thread_id(metadata: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Extract or generate conversation thread ID from metadata.

    Thread IDs help group related messages together.

    Args:
        metadata: Message metadata

    Returns:
        Thread ID if present, None otherwise
    """
    if not metadata:
        return None

    # Check for explicit thread_id
    if "thread_id" in metadata:
        return metadata["thread_id"]

    # Check for related message ID (reply)
    if "reply_to_message_id" in metadata:
        return metadata["reply_to_message_id"]

    # Check for related task/ticket
    if "task_id" in metadata:
        return f"task_{metadata['task_id']}"

    return None
