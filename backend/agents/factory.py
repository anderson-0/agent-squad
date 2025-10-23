"""
Agent Factory for Creating AI Agents

This factory creates Agno-powered agents based on role, specialization, and configuration.
All agents use the Agno framework with enterprise-grade architecture.
"""
from typing import Optional, Type, Dict
from uuid import UUID

# Agno Base Imports
from backend.agents.agno_base import AgnoSquadAgent, AgentConfig, LLMProvider

# Agno Agent Imports
from backend.agents.specialized.agno_project_manager import AgnoProjectManagerAgent
from backend.agents.specialized.agno_tech_lead import AgnoTechLeadAgent
from backend.agents.specialized.agno_backend_developer import AgnoBackendDeveloperAgent
from backend.agents.specialized.agno_frontend_developer import AgnoFrontendDeveloperAgent
from backend.agents.specialized.agno_qa_tester import AgnoQATesterAgent
from backend.agents.specialized.agno_solution_architect import AgnoSolutionArchitectAgent
from backend.agents.specialized.agno_devops_engineer import AgnoDevOpsEngineerAgent
from backend.agents.specialized.agno_ai_engineer import AgnoAIEngineerAgent
from backend.agents.specialized.agno_designer import AgnoDesignerAgent


# Registry of agent classes by role
AGENT_REGISTRY: Dict[str, Type[AgnoSquadAgent]] = {
    "project_manager": AgnoProjectManagerAgent,
    "backend_developer": AgnoBackendDeveloperAgent,
    "frontend_developer": AgnoFrontendDeveloperAgent,
    "tester": AgnoQATesterAgent,
    "tech_lead": AgnoTechLeadAgent,
    "solution_architect": AgnoSolutionArchitectAgent,
    "devops_engineer": AgnoDevOpsEngineerAgent,
    "ai_engineer": AgnoAIEngineerAgent,
    "designer": AgnoDesignerAgent,
}


class AgentFactory:
    """
    Factory for creating Agno-powered AI agents.

    This factory:
    - Creates agents based on role and specialization
    - Loads appropriate system prompts from roles/ directory
    - Configures LLM providers (OpenAI, Anthropic, Groq)
    - Tracks agent instances
    - Supports session resumption for persistent conversations
    """

    _instances: Dict[UUID, AgnoSquadAgent] = {}

    @classmethod
    def create_agent(
        cls,
        agent_id: UUID,
        role: str,
        specialization: Optional[str] = None,
        llm_provider: LLMProvider = "openai",
        llm_model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AgnoSquadAgent:
        """
        Create an Agno-powered agent instance.

        Args:
            agent_id: Unique identifier for the agent
            role: Agent role (project_manager, backend_developer, tech_lead, etc.)
            specialization: Optional specialization (python_fastapi, react_nextjs, etc.)
            llm_provider: LLM provider to use (openai, anthropic, groq)
            llm_model: Specific model to use (gpt-4o, claude-3-5-sonnet, etc.)
            temperature: Temperature for LLM (0.0-2.0, default: 0.7)
            max_tokens: Maximum tokens for response
            system_prompt: Optional custom system prompt (overrides file-based prompt)
            session_id: Optional session ID for resuming conversations

        Returns:
            Configured Agno agent instance

        Raises:
            ValueError: If role is not supported
        """
        # Validate role
        if role not in AGENT_REGISTRY:
            raise ValueError(
                f"Unsupported role: {role}. "
                f"Supported roles: {', '.join(AGENT_REGISTRY.keys())}"
            )

        # Create config
        config = AgentConfig(
            role=role,
            specialization=specialization,
            llm_provider=llm_provider,
            llm_model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
        )

        # Get agent class and instantiate
        agent_class = AGENT_REGISTRY[role]
        agent = agent_class(
            config=config,
            agent_id=agent_id,
            session_id=session_id
        )

        # Store instance
        cls._instances[agent_id] = agent

        return agent

    @classmethod
    def get_agent(cls, agent_id: UUID) -> Optional[AgnoSquadAgent]:
        """
        Get an existing agent instance by ID.

        Args:
            agent_id: UUID of the agent

        Returns:
            Agent instance or None if not found
        """
        return cls._instances.get(agent_id)

    @classmethod
    def remove_agent(cls, agent_id: UUID) -> bool:
        """
        Remove an agent instance from the registry.

        Args:
            agent_id: UUID of the agent

        Returns:
            True if agent was removed, False if not found
        """
        if agent_id in cls._instances:
            del cls._instances[agent_id]
            return True
        return False

    @classmethod
    def get_all_agents(cls) -> Dict[UUID, AgnoSquadAgent]:
        """Get all active agent instances."""
        return cls._instances.copy()

    @classmethod
    def clear_all_agents(cls):
        """Clear all agent instances (useful for testing)."""
        cls._instances.clear()

    @classmethod
    def get_supported_roles(cls) -> list[str]:
        """Get list of all supported roles."""
        return list(AGENT_REGISTRY.keys())

    @classmethod
    def get_available_specializations(cls, role: str) -> list[str]:
        """
        Get list of available specializations for a role.

        This reads the filesystem to find all prompt files in the roles/ directory.

        Args:
            role: Agent role

        Returns:
            List of specialization names (filenames without .md extension)
        """
        from pathlib import Path

        base_path = Path(__file__).parent.parent.parent / "roles" / role
        if not base_path.exists():
            return []

        specializations = []
        for prompt_file in base_path.glob("*.md"):
            if prompt_file.stem != "default_prompt":
                specializations.append(prompt_file.stem)

        return specializations


# ============================================================================
# Convenience Functions
# ============================================================================

def create_project_manager(
    agent_id: UUID,
    llm_provider: LLMProvider = "openai",
    llm_model: str = "gpt-4o",
    session_id: Optional[str] = None,
) -> AgnoProjectManagerAgent:
    """
    Create a Project Manager agent.

    Args:
        agent_id: Unique agent identifier
        llm_provider: LLM provider (openai, anthropic, groq)
        llm_model: Model to use
        session_id: Optional session ID for resuming conversations

    Returns:
        Agno Project Manager agent
    """
    return AgentFactory.create_agent(
        agent_id=agent_id,
        role="project_manager",
        llm_provider=llm_provider,
        llm_model=llm_model,
        session_id=session_id,
    )


def create_backend_developer(
    agent_id: UUID,
    specialization: str = "python_fastapi",
    llm_provider: LLMProvider = "openai",
    llm_model: str = "gpt-4o",
    session_id: Optional[str] = None,
) -> AgnoBackendDeveloperAgent:
    """
    Create a Backend Developer agent.

    Args:
        agent_id: Unique agent identifier
        specialization: Backend specialization (python_fastapi, node_express, etc.)
        llm_provider: LLM provider (openai, anthropic, groq)
        llm_model: Model to use
        session_id: Optional session ID for resuming conversations

    Returns:
        Agno Backend Developer agent
    """
    return AgentFactory.create_agent(
        agent_id=agent_id,
        role="backend_developer",
        specialization=specialization,
        llm_provider=llm_provider,
        llm_model=llm_model,
        session_id=session_id,
    )


def create_frontend_developer(
    agent_id: UUID,
    specialization: str = "react_nextjs",
    llm_provider: LLMProvider = "openai",
    llm_model: str = "gpt-4o",
    session_id: Optional[str] = None,
) -> AgnoFrontendDeveloperAgent:
    """
    Create a Frontend Developer agent.

    Args:
        agent_id: Unique agent identifier
        specialization: Frontend specialization (react_nextjs, vue_nuxt, etc.)
        llm_provider: LLM provider (openai, anthropic, groq)
        llm_model: Model to use
        session_id: Optional session ID for resuming conversations

    Returns:
        Agno Frontend Developer agent
    """
    return AgentFactory.create_agent(
        agent_id=agent_id,
        role="frontend_developer",
        specialization=specialization,
        llm_provider=llm_provider,
        llm_model=llm_model,
        session_id=session_id,
    )


def create_qa_tester(
    agent_id: UUID,
    llm_provider: LLMProvider = "openai",
    llm_model: str = "gpt-4o",
    session_id: Optional[str] = None,
) -> AgnoQATesterAgent:
    """
    Create a QA Tester agent.

    Args:
        agent_id: Unique agent identifier
        llm_provider: LLM provider (openai, anthropic, groq)
        llm_model: Model to use
        session_id: Optional session ID for resuming conversations

    Returns:
        Agno QA Tester agent
    """
    return AgentFactory.create_agent(
        agent_id=agent_id,
        role="tester",
        llm_provider=llm_provider,
        llm_model=llm_model,
        session_id=session_id,
    )


def create_tech_lead(
    agent_id: UUID,
    llm_provider: LLMProvider = "openai",
    llm_model: str = "gpt-4o",
    session_id: Optional[str] = None,
) -> AgnoTechLeadAgent:
    """
    Create a Tech Lead agent.

    Args:
        agent_id: Unique agent identifier
        llm_provider: LLM provider (openai, anthropic, groq)
        llm_model: Model to use
        session_id: Optional session ID for resuming conversations

    Returns:
        Agno Tech Lead agent
    """
    return AgentFactory.create_agent(
        agent_id=agent_id,
        role="tech_lead",
        llm_provider=llm_provider,
        llm_model=llm_model,
        session_id=session_id,
    )
