from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from backend.core.database import get_db
from backend.models.squad import Squad
from backend.models.approval_request import ApprovalRequest, ApprovalStatus

router = APIRouter()

@router.post("/squads/{squad_id}/pause", status_code=status.HTTP_200_OK)
async def pause_squad(
    squad_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Pause a squad's execution.
    """
    result = await db.execute(select(Squad).filter(Squad.id == squad_id))
    squad = result.scalar_one_or_none()
    if not squad:
        raise HTTPException(status_code=404, detail="Squad not found")
    
    squad.is_paused = True
    await db.commit()
    return {"message": "Squad paused", "is_paused": True}

@router.post("/squads/{squad_id}/resume", status_code=status.HTTP_200_OK)
async def resume_squad(
    squad_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Resume a squad's execution.
    """
    result = await db.execute(select(Squad).filter(Squad.id == squad_id))
    squad = result.scalar_one_or_none()
    if not squad:
        raise HTTPException(status_code=404, detail="Squad not found")
    
    squad.is_paused = False
    await db.commit()
    return {"message": "Squad resumed", "is_paused": False}

@router.get("/squads/{squad_id}/approvals", response_model=List[dict])
async def get_pending_approvals(
    squad_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get pending approval requests for a squad.
    """
    result = await db.execute(
        select(ApprovalRequest).filter(
            ApprovalRequest.squad_id == squad_id,
            ApprovalRequest.status == ApprovalStatus.PENDING
        )
    )
    approvals = result.scalars().all()
    
    return [
        {
            "id": str(req.id),
            "squad_id": str(req.squad_id),
            "agent_id": str(req.agent_id),
            "action_type": req.action_type,
            "payload": req.payload,
            "status": req.status,
            "created_at": req.created_at
        }
        for req in approvals
    ]

@router.post("/approvals/{approval_id}/approve", status_code=status.HTTP_200_OK)
async def approve_request(
    approval_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Approve a pending request and trigger workflow continuation.
    """
    result = await db.execute(select(ApprovalRequest).filter(ApprovalRequest.id == approval_id))
    request = result.scalar_one_or_none()
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    if request.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Request is already {request.status}")
    
    request.status = ApprovalStatus.APPROVED
    await db.commit()
    
    # Trigger Inngest event to resume workflow with approval
    try:
        from backend.core.inngest import inngest
        await inngest.send(
            event={
                "name": "hitl/approval.approved",
                "data": {
                    "approval_id": str(request.id),
                    "squad_id": str(request.squad_id),
                    "agent_id": str(request.agent_id),
                    "action_type": request.action_type,
                    "payload": request.payload,
                    "approved_at": request.updated_at.isoformat() if request.updated_at else None
                }
            }
        )
    except ImportError:
        # Inngest not available, skip event trigger
        pass
    except Exception as e:
        # Log error but don't fail the approval
        import logging
        logging.getLogger(__name__).error(f"Failed to send Inngest event: {e}")
    
    return {"message": "Request approved", "status": "approved"}

@router.post("/approvals/{approval_id}/reject", status_code=status.HTTP_200_OK)
async def reject_request(
    approval_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Reject a pending request and notify the workflow.
    """
    result = await db.execute(select(ApprovalRequest).filter(ApprovalRequest.id == approval_id))
    request = result.scalar_one_or_none()
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    if request.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Request is already {request.status}")
    
    request.status = ApprovalStatus.REJECTED
    await db.commit()
    
    # Trigger Inngest event to notify rejection
    try:
        from backend.core.inngest import inngest
        await inngest.send(
            event={
                "name": "hitl/approval.rejected",
                "data": {
                    "approval_id": str(request.id),
                    "squad_id": str(request.squad_id),
                    "agent_id": str(request.agent_id),
                    "action_type": request.action_type,
                    "payload": request.payload,
                    "rejected_at": request.updated_at.isoformat() if request.updated_at else None
                }
            }
        )
    except ImportError:
        # Inngest not available, skip event trigger
        pass
    except Exception as e:
        # Log error but don't fail the rejection
        import logging
        logging.getLogger(__name__).error(f"Failed to send Inngest event: {e}")
    
    return {"message": "Request rejected", "status": "rejected"}


