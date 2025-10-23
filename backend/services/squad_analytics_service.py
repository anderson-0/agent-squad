"""
Squad Analytics Service

Provides analytics and statistics for squad members:
- Token consumption tracking
- Message statistics
- Communication patterns
- Conversation filtering
"""
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from backend.models import SquadMember, AgentMessage, SquadMemberStats, Squad
from backend.core.logging import logger


class SquadAnalyticsService:
    """
    Service for tracking and retrieving squad member analytics.

    Provides methods to:
    - Track token usage per member
    - Track message counts
    - Get communication matrix (who talks to whom)
    - Filter conversations between specific members
    """

    @staticmethod
    async def get_or_create_stats(
        db: AsyncSession,
        squad_member_id: UUID
    ) -> SquadMemberStats:
        """
        Get or create stats record for a squad member.

        Args:
            db: Database session
            squad_member_id: Squad member ID

        Returns:
            SquadMemberStats instance
        """
        # Try to get existing stats
        stmt = select(SquadMemberStats).where(
            SquadMemberStats.squad_member_id == squad_member_id
        )
        result = await db.execute(stmt)
        stats = result.scalar_one_or_none()

        if stats:
            return stats

        # Create new stats record
        stats = SquadMemberStats(
            squad_member_id=squad_member_id,
            total_input_tokens=0,
            total_output_tokens=0,
            total_tokens=0,
            total_messages_sent=0,
            total_messages_received=0
        )
        db.add(stats)
        await db.commit()
        await db.refresh(stats)

        logger.info(f"Created stats record for squad member {squad_member_id}")
        return stats

    @staticmethod
    async def update_token_usage(
        db: AsyncSession,
        squad_member_id: UUID,
        input_tokens: int,
        output_tokens: int
    ) -> SquadMemberStats:
        """
        Update token usage for a squad member.

        Call this after each LLM call to track token consumption.

        Args:
            db: Database session
            squad_member_id: Squad member ID
            input_tokens: Input tokens consumed
            output_tokens: Output tokens consumed

        Returns:
            Updated SquadMemberStats
        """
        stats = await SquadAnalyticsService.get_or_create_stats(db, squad_member_id)

        # Update token counts
        stats.total_input_tokens += input_tokens
        stats.total_output_tokens += output_tokens
        stats.total_tokens += (input_tokens + output_tokens)
        stats.last_llm_call_at = datetime.utcnow()
        stats.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(stats)

        logger.debug(
            f"Updated tokens for {squad_member_id}: "
            f"+{input_tokens} input, +{output_tokens} output "
            f"(total: {stats.total_tokens})"
        )

        return stats

    @staticmethod
    async def update_message_sent(
        db: AsyncSession,
        squad_member_id: UUID
    ) -> SquadMemberStats:
        """
        Increment message sent count for a squad member.

        Call this when a squad member sends a message.

        Args:
            db: Database session
            squad_member_id: Squad member ID

        Returns:
            Updated SquadMemberStats
        """
        stats = await SquadAnalyticsService.get_or_create_stats(db, squad_member_id)

        stats.total_messages_sent += 1
        stats.last_message_sent_at = datetime.utcnow()
        stats.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(stats)

        return stats

    @staticmethod
    async def update_message_received(
        db: AsyncSession,
        squad_member_id: UUID
    ) -> SquadMemberStats:
        """
        Increment message received count for a squad member.

        Call this when a squad member receives a message.

        Args:
            db: Database session
            squad_member_id: Squad member ID

        Returns:
            Updated SquadMemberStats
        """
        stats = await SquadAnalyticsService.get_or_create_stats(db, squad_member_id)

        stats.total_messages_received += 1
        stats.last_message_received_at = datetime.utcnow()
        stats.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(stats)

        return stats

    @staticmethod
    async def get_member_stats(
        db: AsyncSession,
        squad_member_id: UUID
    ) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a squad member.

        Args:
            db: Database session
            squad_member_id: Squad member ID

        Returns:
            Dictionary with member statistics
        """
        # Get member info
        stmt = select(SquadMember).where(SquadMember.id == squad_member_id)
        result = await db.execute(stmt)
        member = result.scalar_one_or_none()

        if not member:
            raise ValueError(f"Squad member not found: {squad_member_id}")

        # Get stats
        stats = await SquadAnalyticsService.get_or_create_stats(db, squad_member_id)

        return {
            "squad_member_id": str(squad_member_id),
            "role": member.role,
            "specialization": member.specialization,
            "is_active": member.is_active,
            "token_usage": {
                "total_input_tokens": stats.total_input_tokens,
                "total_output_tokens": stats.total_output_tokens,
                "total_tokens": stats.total_tokens,
            },
            "message_counts": {
                "total_sent": stats.total_messages_sent,
                "total_received": stats.total_messages_received,
                "total": stats.total_messages_sent + stats.total_messages_received,
            },
            "last_activity": {
                "last_message_sent": stats.last_message_sent_at.isoformat() if stats.last_message_sent_at else None,
                "last_message_received": stats.last_message_received_at.isoformat() if stats.last_message_received_at else None,
                "last_llm_call": stats.last_llm_call_at.isoformat() if stats.last_llm_call_at else None,
            },
            "stats_updated_at": stats.updated_at.isoformat(),
        }

    @staticmethod
    async def get_squad_stats(
        db: AsyncSession,
        squad_id: UUID
    ) -> Dict[str, Any]:
        """
        Get aggregated statistics for entire squad.

        Args:
            db: Database session
            squad_id: Squad ID

        Returns:
            Dictionary with squad-level statistics
        """
        # Get squad with members
        stmt = select(Squad).where(Squad.id == squad_id).options(
            selectinload(Squad.members)
        )
        result = await db.execute(stmt)
        squad = result.scalar_one_or_none()

        if not squad:
            raise ValueError(f"Squad not found: {squad_id}")

        # Get stats for all members
        member_stats = []
        total_input_tokens = 0
        total_output_tokens = 0
        total_messages = 0

        for member in squad.members:
            if not member.is_active:
                continue

            stats = await SquadAnalyticsService.get_or_create_stats(db, member.id)
            total_input_tokens += stats.total_input_tokens
            total_output_tokens += stats.total_output_tokens
            total_messages += stats.total_messages_sent

            member_stats.append({
                "member_id": str(member.id),
                "role": member.role,
                "input_tokens": stats.total_input_tokens,
                "output_tokens": stats.total_output_tokens,
                "total_tokens": stats.total_tokens,
                "messages_sent": stats.total_messages_sent,
            })

        return {
            "squad_id": str(squad_id),
            "squad_name": squad.name,
            "total_members": len([m for m in squad.members if m.is_active]),
            "aggregate_stats": {
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_tokens": total_input_tokens + total_output_tokens,
                "total_messages": total_messages,
            },
            "members": member_stats,
        }

    @staticmethod
    async def get_communication_matrix(
        db: AsyncSession,
        squad_id: UUID,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get communication matrix showing who talks to whom in the squad.

        Args:
            db: Database session
            squad_id: Squad ID
            since: Optional datetime to filter messages after

        Returns:
            Dictionary with communication matrix and pairwise message counts
        """
        # Get squad members
        stmt = select(SquadMember).where(
            and_(
                SquadMember.squad_id == squad_id,
                SquadMember.is_active == True
            )
        )
        result = await db.execute(stmt)
        members = result.scalars().all()

        member_ids = [m.id for m in members]
        member_map = {m.id: {"role": m.role, "specialization": m.specialization} for m in members}

        # Build query for messages between squad members
        message_filter = and_(
            AgentMessage.sender_id.in_(member_ids),
            or_(
                AgentMessage.recipient_id.in_(member_ids),
                AgentMessage.recipient_id.is_(None)  # Broadcasts
            )
        )

        if since:
            message_filter = and_(message_filter, AgentMessage.created_at >= since)

        # Get pairwise message counts
        stmt = select(
            AgentMessage.sender_id,
            AgentMessage.recipient_id,
            func.count(AgentMessage.id).label("message_count")
        ).where(message_filter).group_by(
            AgentMessage.sender_id,
            AgentMessage.recipient_id
        )

        result = await db.execute(stmt)
        pairwise_counts = result.all()

        # Build matrix
        matrix = {}
        for sender_id, recipient_id, count in pairwise_counts:
            sender_key = str(sender_id)
            recipient_key = str(recipient_id) if recipient_id else "broadcast"

            if sender_key not in matrix:
                matrix[sender_key] = {}

            matrix[sender_key][recipient_key] = count

        # Build member list for reference
        member_list = [
            {
                "member_id": str(m.id),
                "role": m.role,
                "specialization": m.specialization,
            }
            for m in members
        ]

        return {
            "squad_id": str(squad_id),
            "members": member_list,
            "communication_matrix": matrix,
            "time_period": {
                "since": since.isoformat() if since else None,
                "until": datetime.utcnow().isoformat(),
            }
        }

    @staticmethod
    async def get_conversations_between_members(
        db: AsyncSession,
        member_a_id: UUID,
        member_b_id: UUID,
        limit: int = 100,
        offset: int = 0,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get all messages exchanged between two specific squad members.

        Args:
            db: Database session
            member_a_id: First member ID
            member_b_id: Second member ID
            limit: Maximum number of messages to return
            offset: Offset for pagination
            since: Optional start datetime
            until: Optional end datetime

        Returns:
            Dictionary with filtered messages
        """
        # Build filter for messages between the two members (bidirectional)
        message_filter = or_(
            and_(
                AgentMessage.sender_id == member_a_id,
                AgentMessage.recipient_id == member_b_id
            ),
            and_(
                AgentMessage.sender_id == member_b_id,
                AgentMessage.recipient_id == member_a_id
            )
        )

        if since:
            message_filter = and_(message_filter, AgentMessage.created_at >= since)
        if until:
            message_filter = and_(message_filter, AgentMessage.created_at <= until)

        # Get messages
        stmt = select(AgentMessage).where(message_filter).order_by(
            AgentMessage.created_at.asc()
        ).limit(limit).offset(offset)

        result = await db.execute(stmt)
        messages = result.scalars().all()

        # Get total count
        count_stmt = select(func.count(AgentMessage.id)).where(message_filter)
        count_result = await db.execute(count_stmt)
        total_count = count_result.scalar()

        # Format messages
        formatted_messages = [
            {
                "id": str(msg.id),
                "sender_id": str(msg.sender_id),
                "recipient_id": str(msg.recipient_id) if msg.recipient_id else None,
                "content": msg.content,
                "message_type": msg.message_type,
                "created_at": msg.created_at.isoformat(),
                "metadata": msg.message_metadata,
            }
            for msg in messages
        ]

        return {
            "member_a_id": str(member_a_id),
            "member_b_id": str(member_b_id),
            "total_messages": total_count,
            "returned_messages": len(formatted_messages),
            "limit": limit,
            "offset": offset,
            "messages": formatted_messages,
            "time_period": {
                "since": since.isoformat() if since else None,
                "until": until.isoformat() if until else None,
            }
        }
