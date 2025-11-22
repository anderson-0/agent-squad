from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from backend.core.database import get_db
from backend.core.auth import get_current_user
from backend.models.user import User
from backend.models.analytics import SquadMetrics
from backend.services.squad_service import SquadService

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get(
    "/squad/{squad_id}",
    summary="Get squad analytics",
    description="Get aggregated metrics for a squad"
)
async def get_squad_analytics(
    squad_id: UUID,
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get aggregated analytics for a squad.
    """
    # Verify squad ownership
    await SquadService.verify_squad_ownership(db, squad_id, current_user.id)
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get metrics
    stmt = select(SquadMetrics).where(
        and_(
            SquadMetrics.squad_id == squad_id,
            SquadMetrics.start_time >= start_date
        )
    ).order_by(SquadMetrics.start_time.asc())
    
    result = await db.execute(stmt)
    metrics = result.scalars().all()
    
    # Aggregate for summary
    total_questions = sum(m.total_questions for m in metrics)
    total_resolved = sum(m.total_resolved for m in metrics)
    total_escalated = sum(m.total_escalated for m in metrics)
    total_timeouts = sum(m.total_timeouts for m in metrics)
    
    # Weighted averages
    if total_resolved > 0:
        avg_time = sum(m.avg_resolution_time_seconds * m.total_resolved for m in metrics) / total_resolved
    else:
        avg_time = 0
        
    # Time series data for charts
    time_series = [
        {
            "timestamp": m.start_time.isoformat(),
            "questions": m.total_questions,
            "resolved": m.total_resolved,
            "escalated": m.total_escalated,
            "avg_time": m.avg_resolution_time_seconds
        }
        for m in metrics
    ]
    
    # Aggregate question types
    question_types = {}
    for m in metrics:
        for q_type, count in m.questions_by_type.items():
            question_types[q_type] = question_types.get(q_type, 0) + count
            
    return {
        "summary": {
            "total_questions": total_questions,
            "total_resolved": total_resolved,
            "total_escalated": total_escalated,
            "total_timeouts": total_timeouts,
            "avg_resolution_time_seconds": avg_time,
            "resolution_rate": (total_resolved / total_questions * 100) if total_questions > 0 else 0,
            "escalation_rate": (total_escalated / total_questions * 100) if total_questions > 0 else 0
        },
        "time_series": time_series,
        "question_types": question_types
    }
