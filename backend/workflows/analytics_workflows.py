import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import UUID

import inngest
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.inngest import inngest
from backend.core.database import get_async_session_context
from backend.models import Squad, Conversation, ConversationEvent, SquadMember
from backend.models.analytics import SquadMetrics

logger = logging.getLogger(__name__)

@inngest.create_function(
    fn_id="generate-hourly-analytics",
    trigger=inngest.TriggerCron(cron="0 * * * *"), # Run every hour
)
async def generate_hourly_analytics(ctx: inngest.Context, step: inngest.Step) -> Dict[str, Any]:
    """
    Generate hourly analytics for all squads.
    """
    logger.info("Starting hourly analytics generation")
    
    # Calculate time window (previous hour)
    now = datetime.utcnow()
    end_time = now.replace(minute=0, second=0, microsecond=0)
    start_time = end_time - timedelta(hours=1)
    
    logger.info(f"Processing window: {start_time} to {end_time}")
    
    async with get_async_session_context() as db:
        # Get all squads
        result = await db.execute(select(Squad.id))
        squad_ids = result.scalars().all()
        
        results = []
        for squad_id in squad_ids:
            # Process each squad in a separate step to avoid timeouts and allow retries
            # Note: In a real large-scale app, we might fan-out events here.
            # For now, we'll just process them sequentially or we can use step.run
            
            metrics = await step.run(
                f"process-squad-{squad_id}",
                lambda: process_squad_metrics(squad_id, start_time, end_time)
            )
            results.append(metrics)
            
    return {"processed_squads": len(results), "window": f"{start_time} - {end_time}"}

async def process_squad_metrics(squad_id: UUID, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """
    Calculate and save metrics for a single squad.
    """
    async with get_async_session_context() as db:
        # 1. Get conversations in this window
        stmt = select(Conversation).join(
            SquadMember, Conversation.asker_id == SquadMember.id
        ).where(
            and_(
                SquadMember.squad_id == squad_id,
                Conversation.created_at >= start_time,
                Conversation.created_at < end_time
            )
        )
        result = await db.execute(stmt)
        conversations = result.scalars().all()
        
        total_questions = len(conversations)
        if total_questions == 0:
            logger.info(f"No conversations for squad {squad_id} in window")
            return {"squad_id": str(squad_id), "status": "no_data"}
            
        # 2. Calculate Aggregates
        resolved = [c for c in conversations if c.current_state == 'answered']
        escalated = [c for c in conversations if c.escalation_level > 0]
        # Timeouts are events, but we can approximate by state or check events. 
        # For simplicity, let's assume we check events or just use 'cancelled'/'unresolvable' as proxies if needed.
        # Better: Query events table for timeouts in this window.
        
        # Query timeouts
        timeout_stmt = select(func.count(ConversationEvent.id)).join(
            Conversation, ConversationEvent.conversation_id == Conversation.id
        ).join(
            SquadMember, Conversation.asker_id == SquadMember.id
        ).where(
            and_(
                SquadMember.squad_id == squad_id,
                ConversationEvent.event_type == 'timeout',
                ConversationEvent.created_at >= start_time,
                ConversationEvent.created_at < end_time
            )
        )
        timeout_result = await db.execute(timeout_stmt)
        total_timeouts = timeout_result.scalar() or 0
        
        # Avg Resolution Time
        resolution_times = [
            (c.resolved_at - c.created_at).total_seconds() 
            for c in resolved 
            if c.resolved_at and c.created_at
        ]
        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
        
        # Avg Escalation Depth
        avg_escalation = sum(c.escalation_level for c in conversations) / total_questions
        
        # Questions by Type
        questions_by_type = {}
        for c in conversations:
            q_type = c.question_type or "unknown"
            questions_by_type[q_type] = questions_by_type.get(q_type, 0) + 1
            
        # Agent Performance (Asker perspective for now, or we can analyze responders)
        # Let's analyze Responders
        agent_perf = {}
        # We need to query who responded. 
        # The Conversation model has `current_responder_id`. 
        # For answered conversations, this is the solver.
        for c in resolved:
            responder_id = str(c.current_responder_id)
            if responder_id not in agent_perf:
                agent_perf[responder_id] = {"answered": 0, "total_time": 0}
            
            agent_perf[responder_id]["answered"] += 1
            if c.resolved_at and c.created_at:
                agent_perf[responder_id]["total_time"] += (c.resolved_at - c.created_at).total_seconds()
                
        # Normalize agent perf
        final_agent_perf = {}
        for aid, data in agent_perf.items():
            final_agent_perf[aid] = {
                "answered": data["answered"],
                "avg_time": data["total_time"] / data["answered"] if data["answered"] > 0 else 0
            }
            
        # 3. Save to DB
        metrics = SquadMetrics(
            squad_id=squad_id,
            start_time=start_time,
            end_time=end_time,
            period_type="hourly",
            total_questions=total_questions,
            total_resolved=len(resolved),
            total_escalated=len(escalated),
            total_timeouts=total_timeouts,
            avg_resolution_time_seconds=avg_resolution_time,
            avg_escalation_depth=avg_escalation,
            questions_by_type=questions_by_type,
            agent_performance=final_agent_perf
        )
        
        db.add(metrics)
        await db.commit()
        
        return {"squad_id": str(squad_id), "status": "saved", "questions": total_questions}
