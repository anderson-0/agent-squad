"""
Branching API Endpoints (Stream E)

Endpoints for workflow branching:
- Create branch from discovery
- Get branches for execution
- Merge/abandon/complete branches
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user import User
from backend.models.branching import WorkflowBranch
from backend.models.project import TaskExecution
from backend.agents.branching.branching_engine import BranchingEngine, get_branching_engine
from backend.agents.discovery.discovery_engine import Discovery, get_discovery_engine
from backend.models.workflow import WorkflowPhase
from backend.schemas.branching import (
    CreateBranchRequest,
    BranchResponse,
    MergeBranchRequest,
    BranchTasksResponse,
)
from backend.core.logging import logger


router = APIRouter(prefix="/branching", tags=["branching"])


@router.post(
    "/workflows/{execution_id}/branches",
    status_code=status.HTTP_201_CREATED,
    response_model=BranchResponse,
    summary="Create workflow branch",
    description="Create a new workflow branch from a discovery"
)
async def create_branch(
    execution_id: UUID = Path(..., description="Task execution ID"),
    request: CreateBranchRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BranchResponse:
    """
    Create a workflow branch from a discovery.
    
    This enables discovery-driven branching where agents create
    parallel investigation/optimization tracks.
    """
    try:
        # Validate execution
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found"
            )
        
        # Get discovery (simplified - in real implementation, discoveries would be stored)
        # For now, we'll create a mock discovery from the request
        # TODO: Store discoveries in database and retrieve by ID
        discovery = Discovery(
            type="optimization",  # Default
            description="Branch created from discovery",
            value_score=0.7,
            suggested_phase=WorkflowPhase.INVESTIGATION,
            confidence=0.8,
            context={"discovery_id": str(request.discovery_id)},
        )
        
        # Create branch
        branching_engine = get_branching_engine()
        branch = await branching_engine.create_branch_from_discovery(
            db=db,
            execution_id=execution_id,
            discovery=discovery,
            branch_name=request.branch_name,
            initial_task_title=request.initial_task_title,
            initial_task_description=request.initial_task_description,
            agent_id=request.agent_id,
        )
        
        return BranchResponse(
            id=branch.id,
            parent_execution_id=branch.parent_execution_id,
            branch_name=branch.branch_name,
            branch_phase=branch.branch_phase,
            discovery_origin_type=branch.discovery_origin_type,
            discovery_description=branch.discovery_description,
            status=branch.status,
            created_at=branch.created_at.isoformat(),
            updated_at=branch.updated_at.isoformat(),
            metadata=branch.branch_metadata,
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating branch: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create branch: {str(e)}"
        )


@router.get(
    "/workflows/{execution_id}/branches",
    response_model=List[BranchResponse],
    summary="Get workflow branches",
    description="Get all branches for a workflow execution"
)
async def get_branches(
    execution_id: UUID = Path(..., description="Task execution ID"),
    status: str = Query(None, description="Filter by status (active, merged, abandoned, completed)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[BranchResponse]:
    """Get all branches for a workflow execution"""
    try:
        branching_engine = get_branching_engine()
        branches = await branching_engine.get_branches_for_execution(
            db=db,
            execution_id=execution_id,
            status=status,
        )
        
        return [
            BranchResponse(
                id=branch.id,
                parent_execution_id=branch.parent_execution_id,
                branch_name=branch.branch_name,
                branch_phase=branch.branch_phase,
                discovery_origin_type=branch.discovery_origin_type,
                discovery_description=branch.discovery_description,
                status=branch.status,
                created_at=branch.created_at,
                updated_at=branch.updated_at,
                metadata=branch.branch_metadata,
            )
            for branch in branches
        ]
        
    except Exception as e:
        logger.error(f"Error getting branches: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get branches: {str(e)}"
        )


@router.post(
    "/branches/{branch_id}/merge",
    response_model=BranchResponse,
    summary="Merge branch",
    description="Merge a branch back into parent workflow"
)
async def merge_branch(
    branch_id: UUID = Path(..., description="Branch ID"),
    request: MergeBranchRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BranchResponse:
    """Merge a branch back into parent workflow"""
    try:
        branching_engine = get_branching_engine()
        branch = await branching_engine.merge_branch(
            db=db,
            branch_id=branch_id,
            merge_summary=request.merge_summary,
        )
        
        return BranchResponse(
            id=branch.id,
            parent_execution_id=branch.parent_execution_id,
            branch_name=branch.branch_name,
            branch_phase=branch.branch_phase,
            discovery_origin_type=branch.discovery_origin_type,
            discovery_description=branch.discovery_description,
            status=branch.status,
            created_at=branch.created_at,
            updated_at=branch.updated_at,
            metadata=branch.branch_metadata,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error merging branch: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to merge branch: {str(e)}"
        )


@router.get(
    "/branches/{branch_id}/tasks",
    response_model=BranchTasksResponse,
    summary="Get branch tasks",
    description="Get all tasks in a branch"
)
async def get_branch_tasks(
    branch_id: UUID = Path(..., description="Branch ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BranchTasksResponse:
    """Get all tasks in a branch"""
    try:
        branching_engine = get_branching_engine()
        
        # Get branch
        branch = await db.get(WorkflowBranch, branch_id)
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Branch {branch_id} not found"
            )
        
        # Get tasks
        tasks = await branching_engine.get_branch_tasks(db, branch_id)
        
        completed = sum(1 for t in tasks if t.status == "completed")
        
        return BranchTasksResponse(
            branch=BranchResponse(
                id=branch.id,
                parent_execution_id=branch.parent_execution_id,
                branch_name=branch.branch_name,
                branch_phase=branch.branch_phase,
                discovery_origin_type=branch.discovery_origin_type,
                discovery_description=branch.discovery_description,
                status=branch.status,
                created_at=branch.created_at,
                updated_at=branch.updated_at,
                metadata=branch.branch_metadata,
            ),
            tasks=[
                {
                    "id": str(t.id),
                    "title": t.title,
                    "description": t.description,
                    "phase": t.phase,
                    "status": t.status,
                }
                for t in tasks
            ],
            total_tasks=len(tasks),
            completed_tasks=completed,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting branch tasks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get branch tasks: {str(e)}"
        )


@router.post(
    "/branches/{branch_id}/abandon",
    response_model=BranchResponse,
    summary="Abandon branch",
    description="Mark a branch as abandoned"
)
async def abandon_branch(
    branch_id: UUID = Path(..., description="Branch ID"),
    reason: Optional[str] = Query(None, description="Reason for abandonment"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BranchResponse:
    """Abandon a branch"""
    try:
        branching_engine = get_branching_engine()
        branch = await branching_engine.abandon_branch(
            db=db,
            branch_id=branch_id,
            reason=reason,
        )
        
        return BranchResponse(
            id=branch.id,
            parent_execution_id=branch.parent_execution_id,
            branch_name=branch.branch_name,
            branch_phase=branch.branch_phase,
            discovery_origin_type=branch.discovery_origin_type,
            discovery_description=branch.discovery_description,
            status=branch.status,
            created_at=branch.created_at,
            updated_at=branch.updated_at,
            metadata=branch.branch_metadata,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error abandoning branch: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to abandon branch: {str(e)}"
        )

