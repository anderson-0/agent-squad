"""
Agent Service

Business logic for agent (SquadMember) operations.
Handles CRUD operations, agent initialization, and configuration management.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.squad import Squad, SquadMember
from backend.agents.agno_base import AgnoSquadAgent
from backend.agents.factory import AgentFactory


class AgentService:
    """Service for handling agent operations"""

    @staticmethod
    async def create_squad_member(
        db: AsyncSession,
        squad_id: UUID,
        role: str,
        specialization: Optional[str] = None,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4",
        config: Optional[Dict[str, Any]] = None,
    ) -> SquadMember:
        """
        Create a new squad member (agent).

        Args:
            db: Database session
            squad_id: Squad UUID
            role: Agent role (project_manager, backend_developer, etc.)
            specialization: Optional specialization (nodejs_express, python_fastapi, etc.)
            llm_provider: LLM provider (openai, anthropic, groq)
            llm_model: LLM model name
            config: Optional additional configuration

        Returns:
            Created squad member

        Raises:
            HTTPException: If squad not found or validation fails
        """
        # Validate squad exists
        result = await db.execute(
            select(Squad).where(Squad.id == squad_id)
        )
        squad = result.scalar_one_or_none()

        if not squad:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Squad {squad_id} not found"
            )

        # Validate role
        valid_roles = [
            "project_manager",
            "tech_lead",
            "backend_developer",
            "frontend_developer",
            "qa_tester",
            "solution_architect",
            "devops_engineer",
            "ai_engineer",
            "designer"
        ]

        if role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}. Valid roles: {', '.join(valid_roles)}"
            )

        # Load system prompt for role
        system_prompt = AgentFactory.load_system_prompt(role)

        # Create squad member
        squad_member = SquadMember(
            squad_id=squad_id,
            role=role,
            specialization=specialization,
            llm_provider=llm_provider,
            llm_model=llm_model,
            system_prompt=system_prompt,
            config=config or {},
            is_active=True,
        )

        db.add(squad_member)
        await db.commit()
        await db.refresh(squad_member)

        return squad_member

    @staticmethod
    async def get_squad_member(
        db: AsyncSession,
        member_id: UUID,
    ) -> Optional[SquadMember]:
        """
        Get squad member by ID.

        Args:
            db: Database session
            member_id: Squad member UUID

        Returns:
            Squad member if found, None otherwise
        """
        result = await db.execute(
            select(SquadMember)
            .options(selectinload(SquadMember.squad))
            .where(SquadMember.id == member_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_squad_members(
        db: AsyncSession,
        squad_id: UUID,
        active_only: bool = True,
    ) -> List[SquadMember]:
        """
        Get all members of a squad.

        Args:
            db: Database session
            squad_id: Squad UUID
            active_only: Only return active members

        Returns:
            List of squad members
        """
        query = select(SquadMember).where(SquadMember.squad_id == squad_id)

        if active_only:
            query = query.where(SquadMember.is_active == True)

        result = await db.execute(query.order_by(SquadMember.created_at))
        return list(result.scalars().all())

    @staticmethod
    async def get_squad_member_by_role(
        db: AsyncSession,
        squad_id: UUID,
        role: str,
    ) -> Optional[SquadMember]:
        """
        Get squad member by role within a squad.

        Args:
            db: Database session
            squad_id: Squad UUID
            role: Agent role

        Returns:
            Squad member if found, None otherwise
        """
        result = await db.execute(
            select(SquadMember)
            .where(
                SquadMember.squad_id == squad_id,
                SquadMember.role == role,
                SquadMember.is_active == True
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_agent(
        db: AsyncSession,
        squad_member_id: UUID,
    ) -> AgnoSquadAgent:
        """
        Get or create an agent instance for a squad member.

        This initializes the AgnoSquadAgent with the member's configuration.

        Args:
            db: Database session
            squad_member_id: Squad member UUID

        Returns:
            Initialized Agno agent instance

        Raises:
            HTTPException: If squad member not found
        """
        # Get squad member
        squad_member = await AgentService.get_squad_member(db, squad_member_id)

        if not squad_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Squad member {squad_member_id} not found"
            )

        if not squad_member.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Squad member {squad_member_id} is not active"
            )

        # Extract temperature from config (default: 0.7)
        temperature = squad_member.config.get("temperature", 0.7) if squad_member.config else 0.7
        max_tokens = squad_member.config.get("max_tokens") if squad_member.config else None

        # Create agent using factory (Agno-based)
        agent = AgentFactory.create_agent(
            agent_id=squad_member.id,
            role=squad_member.role,
            specialization=squad_member.specialization,
            llm_provider=squad_member.llm_provider,
            llm_model=squad_member.llm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=squad_member.system_prompt,
            session_id=None,  # New session for each creation
        )

        return agent

    @staticmethod
    async def update_squad_member(
        db: AsyncSession,
        member_id: UUID,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        specialization: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> SquadMember:
        """
        Update squad member configuration.

        Args:
            db: Database session
            member_id: Squad member UUID
            llm_provider: Optional new LLM provider
            llm_model: Optional new LLM model
            specialization: Optional new specialization
            config: Optional new config (will merge with existing)

        Returns:
            Updated squad member

        Raises:
            HTTPException: If squad member not found
        """
        squad_member = await AgentService.get_squad_member(db, member_id)

        if not squad_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Squad member {member_id} not found"
            )

        # Update fields if provided
        if llm_provider is not None:
            squad_member.llm_provider = llm_provider

        if llm_model is not None:
            squad_member.llm_model = llm_model

        if specialization is not None:
            squad_member.specialization = specialization

        if config is not None:
            # Merge with existing config
            current_config = squad_member.config or {}
            squad_member.config = {**current_config, **config}

        await db.commit()
        await db.refresh(squad_member)

        return squad_member

    @staticmethod
    async def deactivate_squad_member(
        db: AsyncSession,
        member_id: UUID,
    ) -> SquadMember:
        """
        Deactivate a squad member.

        Args:
            db: Database session
            member_id: Squad member UUID

        Returns:
            Updated squad member

        Raises:
            HTTPException: If squad member not found
        """
        squad_member = await AgentService.get_squad_member(db, member_id)

        if not squad_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Squad member {member_id} not found"
            )

        squad_member.is_active = False
        await db.commit()
        await db.refresh(squad_member)

        return squad_member

    @staticmethod
    async def reactivate_squad_member(
        db: AsyncSession,
        member_id: UUID,
    ) -> SquadMember:
        """
        Reactivate a squad member.

        Args:
            db: Database session
            member_id: Squad member UUID

        Returns:
            Updated squad member

        Raises:
            HTTPException: If squad member not found
        """
        squad_member = await AgentService.get_squad_member(db, member_id)

        if not squad_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Squad member {member_id} not found"
            )

        squad_member.is_active = True
        await db.commit()
        await db.refresh(squad_member)

        return squad_member

    @staticmethod
    async def delete_squad_member(
        db: AsyncSession,
        member_id: UUID,
    ) -> bool:
        """
        Permanently delete a squad member.

        Args:
            db: Database session
            member_id: Squad member UUID

        Returns:
            True if deleted successfully

        Raises:
            HTTPException: If squad member not found
        """
        squad_member = await AgentService.get_squad_member(db, member_id)

        if not squad_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Squad member {member_id} not found"
            )

        await db.delete(squad_member)
        await db.commit()
        return True

    @staticmethod
    async def get_squad_composition(
        db: AsyncSession,
        squad_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get squad composition summary.

        Args:
            db: Database session
            squad_id: Squad UUID

        Returns:
            Dictionary with squad composition details
        """
        members = await AgentService.get_squad_members(db, squad_id, active_only=True)

        composition = {
            "squad_id": str(squad_id),
            "total_members": len(members),
            "active_members": len(members),
            "roles": {},
            "llm_providers": {},
            "members": []
        }

        for member in members:
            # Count by role
            composition["roles"][member.role] = composition["roles"].get(member.role, 0) + 1

            # Count by LLM provider
            composition["llm_providers"][member.llm_provider] = \
                composition["llm_providers"].get(member.llm_provider, 0) + 1

            # Add member summary
            composition["members"].append({
                "id": str(member.id),
                "role": member.role,
                "specialization": member.specialization,
                "llm_provider": member.llm_provider,
                "llm_model": member.llm_model,
            })

        return composition
