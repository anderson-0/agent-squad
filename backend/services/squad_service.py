"""
Squad Service

Business logic for squad operations.
Handles squad creation, validation, member management, and cost calculation.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException
from fastapi import status as http_status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.user import User
from backend.models.squad import Squad, SquadMember
from backend.models.project import Project


class SquadService:
    """Service for handling squad operations"""

    # Squad size limits by plan tier
    SQUAD_LIMITS = {
        "starter": 3,      # Max 3 agents
        "pro": 10,         # Max 10 agents
        "enterprise": 50,  # Max 50 agents
    }

    @staticmethod
    async def create_squad(
        db: AsyncSession,
        user_id: UUID,
        name: str,
        description: Optional[str] = None,
        org_id: Optional[UUID] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Squad:
        """
        Create a new squad.

        Args:
            db: Database session
            user_id: User UUID
            name: Squad name
            description: Optional squad description
            org_id: Optional organization UUID
            config: Optional squad configuration

        Returns:
            Created squad

        Raises:
            HTTPException: If user not found or validation fails
        """
        # Validate user exists
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="User account is not active"
            )

        # Create squad
        squad = Squad(
            user_id=user_id,
            org_id=org_id,
            name=name,
            description=description,
            status="active",
            config=config or {},
        )

        db.add(squad)
        await db.commit()
        await db.refresh(squad)

        return squad

    @staticmethod
    async def get_squad(
        db: AsyncSession,
        squad_id: UUID,
        load_members: bool = False,
        load_projects: bool = False,
    ) -> Optional[Squad]:
        """
        Get squad by ID.

        Args:
            db: Database session
            squad_id: Squad UUID
            load_members: Load squad members
            load_projects: Load squad projects

        Returns:
            Squad if found, None otherwise
        """
        query = select(Squad).where(Squad.id == squad_id)

        if load_members:
            query = query.options(selectinload(Squad.members))

        if load_projects:
            query = query.options(selectinload(Squad.projects))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_squads(
        db: AsyncSession,
        user_id: UUID,
        status: Optional[str] = None,
    ) -> List[Squad]:
        """
        Get all squads for a user.

        Args:
            db: Database session
            user_id: User UUID
            status: Optional status filter (active, paused, archived)

        Returns:
            List of squads
        """
        query = select(Squad).where(Squad.user_id == user_id)

        if status:
            query = query.where(Squad.status == status)

        result = await db.execute(
            query.order_by(Squad.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_squad(
        db: AsyncSession,
        squad_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Squad:
        """
        Update squad details.

        Args:
            db: Database session
            squad_id: Squad UUID
            name: Optional new name
            description: Optional new description
            status: Optional new status
            config: Optional new config (will merge with existing)

        Returns:
            Updated squad

        Raises:
            HTTPException: If squad not found
        """
        squad = await SquadService.get_squad(db, squad_id)

        if not squad:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Squad {squad_id} not found"
            )

        if name is not None:
            squad.name = name

        if description is not None:
            squad.description = description

        if status is not None:
            valid_statuses = ["active", "paused", "archived"]
            if status not in valid_statuses:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}. Valid: {', '.join(valid_statuses)}"
                )
            squad.status = status

        if config is not None:
            # Merge with existing config
            current_config = squad.config or {}
            squad.config = {**current_config, **config}

        await db.commit()
        await db.refresh(squad)

        return squad

    @staticmethod
    async def update_squad_status(
        db: AsyncSession,
        squad_id: UUID,
        status: str,
    ) -> Squad:
        """
        Update squad status.

        Args:
            db: Database session
            squad_id: Squad UUID
            status: New status (active, paused, archived)

        Returns:
            Updated squad

        Raises:
            HTTPException: If squad not found or invalid status
        """
        valid_statuses = ["active", "paused", "archived"]

        if status not in valid_statuses:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}. Valid: {', '.join(valid_statuses)}"
            )

        squad = await SquadService.get_squad(db, squad_id)

        if not squad:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Squad {squad_id} not found"
            )

        squad.status = status
        await db.commit()
        await db.refresh(squad)

        return squad

    @staticmethod
    async def delete_squad(
        db: AsyncSession,
        squad_id: UUID,
    ) -> None:
        """
        Permanently delete a squad.

        This will cascade delete all members, projects, and task executions.

        Args:
            db: Database session
            squad_id: Squad UUID

        Raises:
            HTTPException: If squad not found
        """
        squad = await SquadService.get_squad(db, squad_id)

        if not squad:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Squad {squad_id} not found"
            )

        await db.delete(squad)
        await db.commit()

    @staticmethod
    async def validate_squad_size(
        db: AsyncSession,
        squad_id: UUID,
        user_id: UUID,
        new_member_count: int = 1,
    ) -> bool:
        """
        Validate if squad can add more members based on plan tier.

        Args:
            db: Database session
            squad_id: Squad UUID
            user_id: User UUID
            new_member_count: Number of new members to add

        Returns:
            True if valid, False otherwise

        Raises:
            HTTPException: If limit exceeded
        """
        # Get user's plan tier
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Get current member count
        result = await db.execute(
            select(func.count(SquadMember.id))
            .where(
                SquadMember.squad_id == squad_id,
                SquadMember.is_active == True
            )
        )
        current_count = result.scalar()

        # Check limit
        limit = SquadService.SQUAD_LIMITS.get(user.plan_tier, 3)

        if current_count + new_member_count > limit:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Squad size limit reached. {user.plan_tier} plan allows max {limit} agents. "
                       f"Current: {current_count}, Attempting to add: {new_member_count}"
            )

        return True

    @staticmethod
    async def get_squad_with_agents(
        db: AsyncSession,
        squad_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get squad with full agent details.

        Args:
            db: Database session
            squad_id: Squad UUID

        Returns:
            Dictionary with squad and agent details

        Raises:
            HTTPException: If squad not found
        """
        squad = await SquadService.get_squad(db, squad_id, load_members=True)

        if not squad:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Squad {squad_id} not found"
            )

        # Get active members
        active_members = [m for m in squad.members if m.is_active]

        return {
            "member_count": len(active_members),
            "active_member_count": len(active_members),
            "squad": {
                "id": str(squad.id),
                "name": squad.name,
                "description": squad.description,
                "status": squad.status,
                "user_id": str(squad.user_id),
                "org_id": str(squad.org_id) if squad.org_id else None,
                "config": squad.config,
                "created_at": squad.created_at.isoformat(),
                "updated_at": squad.updated_at.isoformat(),
            },
            "members": [
                {
                    "id": str(m.id),
                    "role": m.role,
                    "specialization": m.specialization,
                    "llm_provider": m.llm_provider,
                    "llm_model": m.llm_model,
                    "is_active": m.is_active,
                    "created_at": m.created_at.isoformat(),
                }
                for m in active_members
            ],
        }

    @staticmethod
    async def calculate_squad_cost(
        db: AsyncSession,
        squad_id: UUID,
    ) -> Dict[str, Any]:
        """
        Calculate estimated monthly cost for a squad.

        Based on agent count, LLM providers, and expected token usage.

        Args:
            db: Database session
            squad_id: Squad UUID

        Returns:
            Dictionary with cost breakdown

        Raises:
            HTTPException: If squad not found
        """
        squad = await SquadService.get_squad(db, squad_id, load_members=True)

        if not squad:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Squad {squad_id} not found"
            )

        # Estimated costs per model (per 1M tokens)
        # These are rough estimates - actual costs vary
        MODEL_COSTS = {
            "gpt-4": 0.03,
            "gpt-4-turbo": 0.01,
            "gpt-3.5-turbo": 0.002,
            "claude-3-opus": 0.015,
            "claude-3-sonnet": 0.003,
            "claude-3-haiku": 0.00025,
            "groq/mixtral": 0.0002,
        }

        # Estimated tokens per agent per month
        TOKENS_PER_AGENT_MONTHLY = 1_000_000  # 1M tokens/month per agent

        total_cost = 0.0
        cost_breakdown = []

        active_members = [m for m in squad.members if m.is_active]

        for member in active_members:
            model_key = member.llm_model
            if member.llm_provider == "groq":
                model_key = f"groq/{member.llm_model}"

            cost_per_token = MODEL_COSTS.get(model_key, 0.01)  # Default to $0.01
            member_cost = (TOKENS_PER_AGENT_MONTHLY / 1_000_000) * cost_per_token

            total_cost += member_cost

            cost_breakdown.append({
                "role": member.role,
                "llm_provider": member.llm_provider,
                "llm_model": member.llm_model,
                "estimated_monthly_cost": round(member_cost, 2),
            })

        return {
            "squad_id": str(squad_id),
            "member_count": len(active_members),
            "total_monthly_cost": round(total_cost, 2),
            "cost_by_model": cost_breakdown,
            "note": "Costs are estimates based on average usage. Actual costs may vary.",
        }

    @staticmethod
    async def verify_squad_ownership(
        db: AsyncSession,
        squad_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Verify that a user owns a squad.

        Args:
            db: Database session
            squad_id: Squad UUID
            user_id: User UUID

        Returns:
            True if user owns squad

        Raises:
            HTTPException: If squad not found or user doesn't own it
        """
        squad = await SquadService.get_squad(db, squad_id)

        if not squad:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Squad {squad_id} not found"
            )

        if squad.user_id != user_id:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this squad"
            )

        return True
