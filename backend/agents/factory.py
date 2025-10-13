"""
Agent Factory for Creating AI Agents

This factory creates agents based on role, specialization, and configuration.
It handles prompt loading and agent instantiation.
"""
from typing import Optional, Type, Dict
from uuid import UUID

from backend.agents.base_agent import BaseSquadAgent, AgentConfig, LLMProvider
from backend.agents.specialized.project_manager import ProjectManagerAgent
from backend.agents.specialized.backend_developer import BackendDeveloperAgent
from backend.agents.specialized.frontend_developer import FrontendDeveloperAgent
from backend.agents.specialized.qa_tester import QATesterAgent
from backend.agents.specialized.tech_lead import TechLeadAgent
from backend.agents.specialized.solution_architect import SolutionArchitectAgent
from backend.agents.specialized.devops_engineer import DevOpsEngineerAgent
from backend.agents.specialized.ai_engineer import AIEngineerAgent
from backend.agents.specialized.designer import DesignerAgent


# Registry of agent classes by role
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


class AgentFactory:
    """
    Factory for creating AI agents dynamically.

    This factory:
    - Creates agents based on role and specialization
    - Loads appropriate system prompts
    - Configures LLM providers
    - Tracks agent instances
    """

    _instances: Dict[UUID, BaseSquadAgent] = {}

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
    ) -> BaseSquadAgent:
        """
        Create an agent instance.

        Args:
            agent_id: Unique identifier for the agent
            role: Agent role (project_manager, backend_developer, etc.)
            specialization: Optional specialization (python_fastapi, react_nextjs, etc.)
            llm_provider: LLM provider to use (openai, anthropic, groq)
            llm_model: Specific model to use
            temperature: Temperature for LLM (0.0-1.0)
            max_tokens: Maximum tokens for response
            system_prompt: Optional custom system prompt (overrides file-based prompt)

        Returns:
            Configured agent instance

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
        agent = agent_class(config)

        # Store instance
        cls._instances[agent_id] = agent

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
) -> ProjectManagerAgent:
    """Create a Project Manager agent"""
    return AgentFactory.create_agent(
        agent_id=agent_id,
        role="project_manager",
        llm_provider=llm_provider,
        llm_model=llm_model,
    )


def create_backend_developer(
    agent_id: UUID,
    specialization: str = "python_fastapi",
    llm_provider: LLMProvider = "openai",
    llm_model: str = "gpt-4",
) -> BackendDeveloperAgent:
    """Create a Backend Developer agent"""
    return AgentFactory.create_agent(
        agent_id=agent_id,
        role="backend_developer",
        specialization=specialization,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )


def create_frontend_developer(
    agent_id: UUID,
    specialization: str = "react_nextjs",
    llm_provider: LLMProvider = "openai",
    llm_model: str = "gpt-4",
) -> FrontendDeveloperAgent:
    """Create a Frontend Developer agent"""
    return AgentFactory.create_agent(
        agent_id=agent_id,
        role="frontend_developer",
        specialization=specialization,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )


def create_qa_tester(
    agent_id: UUID,
    llm_provider: LLMProvider = "openai",
    llm_model: str = "gpt-4",
) -> QATesterAgent:
    """Create a QA Tester agent"""
    return AgentFactory.create_agent(
        agent_id=agent_id,
        role="tester",
        llm_provider=llm_provider,
        llm_model=llm_model,
    )
