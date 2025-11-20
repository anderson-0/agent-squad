"""
Agent Pool API Endpoints

Provides monitoring and management endpoints for the agent pool.
These endpoints help track agent pool performance, cache hit rates,
and memory usage for optimization insights.

Phase 2 Optimization Feature
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from backend.core.auth import get_current_user
from backend.models import User
from backend.services.agent_pool import get_agent_pool
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-pool", tags=["Agent Pool"])


@router.get(
    "/stats",
    response_model=Dict[str, Any],
    summary="Get agent pool statistics"
)
async def get_agent_pool_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get agent pool performance statistics.

    Returns metrics including:
    - Pool size (current number of cached agents)
    - Cache hits (agents reused from pool)
    - Cache misses (new agents created)
    - Hit rate percentage
    - Evictions (agents removed from pool when full)
    - Total requests

    **Performance Insights:**
    - High hit rate (>70%) = Good performance
    - Low hit rate (<50%) = Consider increasing pool size
    - Many evictions = Pool too small for workload

    **Example Response:**
    ```json
    {
        "pool_size": 45,
        "cache_hits": 327,
        "cache_misses": 89,
        "evictions": 12,
        "total_requests": 416,
        "hit_rate": 78.61,
        "created_at": "2025-11-04T10:00:00Z",
        "last_access": "2025-11-04T15:30:00Z"
    }
    ```

    **Returns:**
    - AgentPoolStats dictionary
    """
    try:
        agent_pool = await get_agent_pool()
        stats = await agent_pool.get_stats()

        return stats.to_dict()

    except Exception as e:
        logger.error(f"Error fetching agent pool stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch agent pool stats: {str(e)}"
        )


@router.get(
    "/info",
    response_model=Dict[str, Any],
    summary="Get detailed agent pool information"
)
async def get_agent_pool_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed agent pool information.

    Returns comprehensive information including:
    - Pool configuration (max size, settings)
    - Statistics (hits, misses, evictions)
    - List of all cached agents with details

    **Use Cases:**
    - Debugging performance issues
    - Understanding which agents are cached
    - Monitoring pool health
    - Capacity planning

    **Example Response:**
    ```json
    {
        "config": {
            "max_pool_size": 100,
            "enable_stats": true
        },
        "stats": {
            "pool_size": 45,
            "cache_hits": 327,
            "cache_misses": 89,
            "hit_rate": 78.61,
            ...
        },
        "agents": [
            {
                "squad_id": "123e4567-e89b-12d3-a456-426614174000",
                "role": "project_manager",
                "position": 1
            },
            {
                "squad_id": "123e4567-e89b-12d3-a456-426614174000",
                "role": "backend_developer",
                "position": 2
            },
            ...
        ]
    }
    ```

    **Returns:**
    - Detailed pool information dictionary
    """
    try:
        agent_pool = await get_agent_pool()
        info = await agent_pool.get_pool_info()

        return info

    except Exception as e:
        logger.error(f"Error fetching agent pool info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch agent pool info: {str(e)}"
        )


@router.post(
    "/clear",
    response_model=Dict[str, Any],
    summary="Clear agent pool cache"
)
async def clear_agent_pool(
    current_user: User = Depends(get_current_user)
):
    """
    Clear all agents from pool cache.

    **WARNING:** This will remove all cached agents, forcing recreation
    on next use. This may temporarily impact performance as agents need
    to be recreated.

    **Use Cases:**
    - After squad configuration changes
    - Manual cache invalidation
    - Debugging issues
    - Memory cleanup

    **Performance Impact:**
    - Next requests will have cache misses
    - Temporary 60% slower response time until pool rebuilds
    - Pool will automatically rebuild during normal usage

    **Example Response:**
    ```json
    {
        "status": "cleared",
        "agents_removed": 45,
        "message": "Agent pool cleared successfully"
    }
    ```

    **Returns:**
    - Status and count of agents removed
    """
    try:
        agent_pool = await get_agent_pool()
        count = await agent_pool.clear_pool()

        logger.info(f"Agent pool cleared by user {current_user.id}: {count} agents removed")

        return {
            "status": "cleared",
            "agents_removed": count,
            "message": "Agent pool cleared successfully"
        }

    except Exception as e:
        logger.error(f"Error clearing agent pool: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear agent pool: {str(e)}"
        )


@router.delete(
    "/agents/{squad_id}/{role}",
    response_model=Dict[str, Any],
    summary="Remove specific agent from pool"
)
async def remove_agent_from_pool(
    squad_id: str,
    role: str,
    current_user: User = Depends(get_current_user)
):
    """
    Remove a specific agent from pool cache.

    Use this when:
    - Squad member configuration changed
    - Agent needs to be recreated with new settings
    - Debugging specific agent issues

    **Parameters:**
    - **squad_id**: Squad UUID
    - **role**: Agent role (project_manager, backend_developer, etc.)

    **Example Response:**
    ```json
    {
        "status": "removed",
        "squad_id": "123e4567-e89b-12d3-a456-426614174000",
        "role": "backend_developer",
        "message": "Agent removed from pool"
    }
    ```

    **Returns:**
    - Status and details of removed agent
    """
    try:
        from uuid import UUID

        # Convert squad_id to UUID
        try:
            squad_uuid = UUID(squad_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid squad_id: {squad_id}"
            )

        # Remove agent from pool
        agent_pool = await get_agent_pool()
        removed = await agent_pool.remove_agent(squad_uuid, role)

        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found in pool: squad={squad_id}, role={role}"
            )

        logger.info(
            f"Agent removed from pool by user {current_user.id}: "
            f"squad={squad_id}, role={role}"
        )

        return {
            "status": "removed",
            "squad_id": squad_id,
            "role": role,
            "message": "Agent removed from pool"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing agent from pool: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove agent from pool: {str(e)}"
        )
