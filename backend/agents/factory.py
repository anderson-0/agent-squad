"""
Agent Factory for Creating AI Agents

This factory creates agents based on role, specialization, and configuration.
It handles prompt loading and agent instantiation.

Supports both Custom (legacy) and Agno (enterprise-grade) agent implementations
with feature flags for gradual rollout.
"""
from typing import Optional, Type, Dict, Union
from uuid import UUID
import os

from backend.agents.base_agent import BaseSquadAgent, AgentConfig, LLMProvider

# Custom (Legacy) Agent Imports
from backend.agents.specialized.project_manager import ProjectManagerAgent
from backend.agents.specialized.backend_developer import BackendDeveloperAgent
from backend.agents.specialized.frontend_developer import FrontendDeveloperAgent
from backend.agents.specialized.qa_tester import QATesterAgent
from backend.agents.specialized.tech_lead import TechLeadAgent
from backend.agents.specialized.solution_architect import SolutionArchitectAgent
from backend.agents.specialized.devops_engineer import DevOpsEngineerAgent
from backend.agents.specialized.ai_engineer import AIEngineerAgent
from backend.agents.specialized.designer import DesignerAgent

# Agno (Enterprise) Agent Imports
from backend.agents.agno_base import AgnoSquadAgent, AgentConfig as AgnoAgentConfig, LLMProvider as AgnoLLMProvider
from backend.agents.specialized.agno_project_manager import AgnoProjectManagerAgent
from backend.agents.specialized.agno_tech_lead import AgnoTechLeadAgent
from backend.agents.specialized.agno_backend_developer import AgnoBackendDeveloperAgent
from backend.agents.specialized.agno_frontend_developer import AgnoFrontendDeveloperAgent
from backend.agents.specialized.agno_qa_tester import AgnoQATesterAgent
from backend.agents.specialized.agno_solution_architect import AgnoSolutionArchitectAgent
from backend.agents.specialized.agno_devops_engineer import AgnoDevOpsEngineerAgent
from backend.agents.specialized.agno_ai_engineer import AgnoAIEngineerAgent
from backend.agents.specialized.agno_designer import AgnoDesignerAgent


# Registry of Custom agent classes by role
AGENT_REGISTRY: Dict[str, Type[BaseSquadAgent]] = {
    "project_manager": ProjectManagerAgent,
    "backend_developer": BackendDeveloperAgent,
    "frontend_developer": FrontendDeveloperAgent,
    "tester": QATesterAgent,
    "tech_lead": TechLeadAgent,
    "solution_architect": SolutionArchitectAgent,
    "devops_engineer": DevOpsEngineerAgent,
    "ai_engineer": AIEngineerAgent,
    "designer": DesignerAgent,
}

# Registry of Agno agent classes by role
AGNO_AGENT_REGISTRY: Dict[str, Type[AgnoSquadAgent]] = {
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

# Feature Flags for Agno Rollout
# Set USE_AGNO_AGENTS=false to disable Agno agents globally (use custom agents)
# Or set AGNO_ENABLED_ROLES to comma-separated list of roles
USE_AGNO_AGENTS = os.getenv("USE_AGNO_AGENTS", "true").lower() == "true"
AGNO_ENABLED_ROLES = set(
    role.strip()
    for role in os.getenv("AGNO_ENABLED_ROLES", "").split(",")
    if role.strip()
)


class AgentFactory:
    """
    Factory for creating AI agents dynamically.

    This factory:
    - Creates agents based on role and specialization
    - Loads appropriate system prompts
    - Configures LLM providers
    - Tracks agent instances
    - Supports both Custom and Agno agent implementations
    - Provides feature flags for gradual Agno rollout
    """

    _instances: Dict[UUID, Union[BaseSquadAgent, AgnoSquadAgent]] = {}

    @classmethod
    def create_agent(
        cls,
        agent_id: UUID,
        role: str,
        specialization: Optional[str] = None,
        llm_provider: LLMProvider = "openai",
        llm_model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        force_agno: Optional[bool] = None,
        session_id: Optional[str] = None,
    ) -> Union[BaseSquadAgent, AgnoSquadAgent]:
        """
        Create an agent instance (Custom or Agno based on feature flags).

        Args:
            agent_id: Unique identifier for the agent
            role: Agent role (project_manager, backend_developer, etc.)
            specialization: Optional specialization (python_fastapi, react_nextjs, etc.)
            llm_provider: LLM provider to use (openai, anthropic, groq)
            llm_model: Specific model to use
            temperature: Temperature for LLM (0.0-1.0)
            max_tokens: Maximum tokens for response
            system_prompt: Optional custom system prompt (overrides file-based prompt)
            force_agno: Force Agno implementation (overrides feature flags)
            session_id: Session ID for Agno agents (enables session resumption)

        Returns:
            Configured agent instance (Custom or Agno)

        Raises:
            ValueError: If role is not supported
        """
        # Validate role
        if role not in AGENT_REGISTRY and role not in AGNO_AGENT_REGISTRY:
            raise ValueError(
                f"Unsupported role: {role}. "
                f"Supported roles: {', '.join(AGENT_REGISTRY.keys())}"
            )

        # Determine whether to use Agno or Custom
        use_agno = cls._should_use_agno(role, force_agno)

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

        # Create agent based on implementation type
        if use_agno:
            agent = cls._create_agno_agent(role, config, agent_id, session_id)
        else:
            agent = cls._create_custom_agent(role, config)

        # Store instance
        cls._instances[agent_id] = agent

        return agent

    @classmethod
    def _should_use_agno(cls, role: str, force_agno: Optional[bool]) -> bool:
        """
        Determine whether to use Agno implementation for this agent.

        Decision logic:
        1. If force_agno is explicitly set, use that value
        2. If USE_AGNO_AGENTS is true globally, use Agno
        3. If role is in AGNO_ENABLED_ROLES, use Agno
        4. Otherwise, use Custom

        Args:
            role: Agent role
            force_agno: Explicit override

        Returns:
            True if should use Agno, False for Custom
        """
        if force_agno is not None:
            return force_agno

        if USE_AGNO_AGENTS:
            return True

        if role in AGNO_ENABLED_ROLES:
            return True

        return False

    @classmethod
    def _create_agno_agent(
        cls,
        role: str,
        config: AgentConfig,
        agent_id: UUID,
        session_id: Optional[str] = None,
    ) -> AgnoSquadAgent:
        """
        Create an Agno-powered agent.

        Args:
            role: Agent role
            config: Agent configuration
            agent_id: Agent UUID for message bus identification
            session_id: Optional session ID for resuming sessions

        Returns:
            Agno agent instance
        """
        # Get Agno agent class
        agent_class = AGNO_AGENT_REGISTRY[role]

        # Map LLM provider string to Agno enum
        # Both Custom and Agno use lowercase enum values
        provider_str = config.llm_provider.lower() if isinstance(config.llm_provider, str) else config.llm_provider

        # Convert config to Agno format
        agno_config = AgnoAgentConfig(
            role=config.role,
            specialization=config.specialization,
            llm_provider=AgnoLLMProvider(provider_str),
            llm_model=config.llm_model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            system_prompt=config.system_prompt,
        )

        # Instantiate Agno agent with agent_id for message bus
        agent = agent_class(config=agno_config, agent_id=agent_id, session_id=session_id)

        return agent

    @classmethod
    def _create_custom_agent(
        cls,
        role: str,
        config: AgentConfig,
    ) -> BaseSquadAgent:
        """
        Create a Custom (legacy) agent.

        Args:
            role: Agent role
            config: Agent configuration

        Returns:
            Custom agent instance
        """
        # Get Custom agent class
        agent_class = AGENT_REGISTRY[role]

        # Instantiate Custom agent
        agent = agent_class(config)

        return agent

    @classmethod
    def get_agent(cls, agent_id: UUID) -> Optional[BaseSquadAgent]:
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
    def get_all_agents(cls) -> Dict[UUID, BaseSquadAgent]:
        """Get all active agent instances"""
        return cls._instances.copy()

    @classmethod
    def clear_all_agents(cls):
        """Clear all agent instances (useful for testing)"""
        cls._instances.clear()

    @classmethod
    def get_supported_roles(cls) -> list[str]:
        """Get list of all supported roles"""
        return list(AGENT_REGISTRY.keys())

    @classmethod
    def get_available_specializations(cls, role: str) -> list[str]:
        """
        Get list of available specializations for a role.

        This reads the filesystem to find all prompt files.
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

    @classmethod
    def load_system_prompt(cls, role: str, specialization: Optional[str] = None) -> str:
        """
        Load system prompt for a role/specialization.

        Args:
            role: Agent role
            specialization: Optional specialization

        Returns:
            System prompt string
        """
        # For now, return a default prompt
        # In the future, this will load from files in the roles/ directory
        return f"You are a {role} agent. Your role is to assist with {role.replace('_', ' ')} tasks."


# Convenience functions for common operations

def create_project_manager(
    agent_id: UUID,
    llm_provider: LLMProvider = "openai",
    llm_model: str = "gpt-4",
    force_agno: Optional[bool] = None,
    session_id: Optional[str] = None,
) -> Union[ProjectManagerAgent, AgnoProjectManagerAgent]:
    """Create a Project Manager agent (Custom or Agno)"""
    return AgentFactory.create_agent(
        agent_id=agent_id,
        role="project_manager",
        llm_provider=llm_provider,
        llm_model=llm_model,
        force_agno=force_agno,
        session_id=session_id,
    )


def create_backend_developer(
    agent_id: UUID,
    specialization: str = "python_fastapi",
    llm_provider: LLMProvider = "openai",
    llm_model: str = "gpt-4",
    force_agno: Optional[bool] = None,
    session_id: Optional[str] = None,
) -> Union[BackendDeveloperAgent, AgnoBackendDeveloperAgent]:
    """Create a Backend Developer agent (Custom or Agno)"""
    return AgentFactory.create_agent(
        agent_id=agent_id,
        role="backend_developer",
        specialization=specialization,
        llm_provider=llm_provider,
        llm_model=llm_model,
        force_agno=force_agno,
        session_id=session_id,
    )


def create_frontend_developer(
    agent_id: UUID,
    specialization: str = "react_nextjs",
    llm_provider: LLMProvider = "openai",
    llm_model: str = "gpt-4",
    force_agno: Optional[bool] = None,
    session_id: Optional[str] = None,
) -> Union[FrontendDeveloperAgent, AgnoFrontendDeveloperAgent]:
    """Create a Frontend Developer agent (Custom or Agno)"""
    return AgentFactory.create_agent(
        agent_id=agent_id,
        role="frontend_developer",
        specialization=specialization,
        llm_provider=llm_provider,
        llm_model=llm_model,
        force_agno=force_agno,
        session_id=session_id,
    )


def create_qa_tester(
    agent_id: UUID,
    llm_provider: LLMProvider = "openai",
    llm_model: str = "gpt-4",
    force_agno: Optional[bool] = None,
    session_id: Optional[str] = None,
) -> Union[QATesterAgent, AgnoQATesterAgent]:
    """Create a QA Tester agent (Custom or Agno)"""
    return AgentFactory.create_agent(
        agent_id=agent_id,
        role="tester",
        llm_provider=llm_provider,
        llm_model=llm_model,
        force_agno=force_agno,
        session_id=session_id,
    )
