"""
Context Manager

The Context Manager builds rich context for agents by aggregating information
from multiple sources: RAG (code, tickets, docs), memory, conversation history,
and squad metadata.

This allows agents to make informed decisions with relevant background knowledge.
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from backend.agents.context.rag_service import RAGService
from backend.agents.context.memory_store import MemoryStore
from backend.agents.communication.history_manager import HistoryManager
from backend.core.database import AsyncSessionLocal
from backend.models.squad import Squad
# Agent model doesn't exist - using SquadMember instead
from sqlalchemy import select


class ContextManager:
    """
    Context Manager - Aggregates context from multiple sources

    Responsibilities:
    - Build context for agent prompts
    - Retrieve relevant code from RAG
    - Retrieve related tickets and solutions
    - Get recent conversation history
    - Access short-term memory
    - Provide squad metadata

    Context Sources:
    1. RAG (Pinecone): Code, tickets, docs, conversations, decisions
    2. Memory (Redis): Short-term working memory
    3. History (PostgreSQL): Conversation history
    4. Database: Squad and agent metadata
    """

    def __init__(
        self,
        rag_service: RAGService,
        memory_store: MemoryStore,
        history_manager: HistoryManager,
    ):
        """
        Initialize Context Manager

        Args:
            rag_service: RAG service for vector search
            memory_store: Redis memory store
            history_manager: Conversation history manager
        """
        self.rag = rag_service
        self.memory = memory_store
        self.history = history_manager

    async def build_context(
        self,
        agent_id: UUID,
        squad_id: UUID,
        query: str,
        task_execution_id: Optional[UUID] = None,
        include_code: bool = True,
        include_tickets: bool = True,
        include_docs: bool = True,
        include_conversations: bool = False,
        include_decisions: bool = True,
        conversation_history_limit: int = 20,
        max_results_per_source: int = 5,
    ) -> Dict[str, Any]:
        """
        Build comprehensive context for an agent.

        Args:
            agent_id: Agent UUID
            squad_id: Squad UUID
            query: Query string for RAG retrieval
            task_execution_id: Optional task execution ID
            include_code: Include code from repositories
            include_tickets: Include past tickets and solutions
            include_docs: Include documentation
            include_conversations: Include past agent conversations
            include_decisions: Include architecture decisions
            conversation_history_limit: Max conversation messages
            max_results_per_source: Max RAG results per namespace

        Returns:
            Dictionary with comprehensive context
        """
        context = {
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "squad_id": str(squad_id),
            "agent_id": str(agent_id),
        }

        # 1. Get squad metadata
        context["squad"] = await self._get_squad_metadata(squad_id)

        # 2. Get agent metadata
        context["agent"] = await self._get_agent_metadata(agent_id)

        # 3. RAG retrieval from various namespaces
        rag_results = {}

        if include_code:
            rag_results["code"] = await self.rag.query(
                squad_id=squad_id,
                namespace="code",
                query=query,
                top_k=max_results_per_source,
            )

        if include_tickets:
            rag_results["tickets"] = await self.rag.query(
                squad_id=squad_id,
                namespace="tickets",
                query=query,
                top_k=max_results_per_source,
            )

        if include_docs:
            rag_results["docs"] = await self.rag.query(
                squad_id=squad_id,
                namespace="docs",
                query=query,
                top_k=max_results_per_source,
            )

        if include_conversations:
            rag_results["conversations"] = await self.rag.query(
                squad_id=squad_id,
                namespace="conversations",
                query=query,
                top_k=max_results_per_source,
            )

        if include_decisions:
            rag_results["decisions"] = await self.rag.query(
                squad_id=squad_id,
                namespace="decisions",
                query=query,
                top_k=max_results_per_source,
            )

        context["rag"] = rag_results

        # 4. Get short-term memory
        context["memory"] = await self.memory.get_context(
            agent_id=agent_id,
            task_execution_id=task_execution_id,
        )

        # 5. Get conversation history (if task execution exists)
        if task_execution_id:
            history = await self.history.get_conversation_history(
                task_execution_id=task_execution_id,
                limit=conversation_history_limit,
            )
            context["conversation_history"] = [
                {
                    "timestamp": msg.created_at.isoformat(),
                    "sender_id": str(msg.sender_id),
                    "recipient_id": str(msg.recipient_id) if msg.recipient_id else None,
                    "message_type": msg.message_type,
                    "content": msg.content,
                }
                for msg in history
            ]
        else:
            context["conversation_history"] = []

        return context

    async def build_context_for_ticket_review(
        self,
        agent_id: UUID,
        squad_id: UUID,
        ticket: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build specialized context for ticket review (PM + Tech Lead).

        Args:
            agent_id: Agent UUID
            squad_id: Squad UUID
            ticket: Ticket data

        Returns:
            Context for ticket review
        """
        # Extract key terms from ticket for better RAG retrieval
        query = f"{ticket.get('title', '')} {ticket.get('description', '')}"[:500]

        context = await self.build_context(
            agent_id=agent_id,
            squad_id=squad_id,
            query=query,
            include_code=True,
            include_tickets=True,  # Past similar tickets
            include_docs=True,     # Architecture docs
            include_conversations=False,
            include_decisions=True,  # Past ADRs
            max_results_per_source=3,
        )

        # Add ticket details
        context["ticket"] = ticket

        return context

    async def build_context_for_implementation(
        self,
        agent_id: UUID,
        squad_id: UUID,
        task: Dict[str, Any],
        task_execution_id: UUID,
    ) -> Dict[str, Any]:
        """
        Build specialized context for implementation (Backend/Frontend Dev).

        Args:
            agent_id: Agent UUID
            squad_id: Squad UUID
            task: Task assignment details
            task_execution_id: Task execution UUID

        Returns:
            Context for implementation
        """
        query = f"{task.get('description', '')} {' '.join(task.get('acceptance_criteria', []))}"[:500]

        context = await self.build_context(
            agent_id=agent_id,
            squad_id=squad_id,
            query=query,
            task_execution_id=task_execution_id,
            include_code=True,        # Existing codebase
            include_tickets=True,     # Similar past tasks
            include_docs=True,        # Architecture docs
            include_conversations=True,  # Recent team discussions
            include_decisions=True,   # ADRs
            conversation_history_limit=30,
            max_results_per_source=5,
        )

        # Add task details
        context["task"] = task

        return context

    async def build_context_for_code_review(
        self,
        agent_id: UUID,
        squad_id: UUID,
        pr_description: str,
        code_diff: str,
        acceptance_criteria: List[str],
    ) -> Dict[str, Any]:
        """
        Build specialized context for code review (Tech Lead).

        Args:
            agent_id: Agent UUID (Tech Lead)
            squad_id: Squad UUID
            pr_description: Pull request description
            code_diff: Git diff of changes
            acceptance_criteria: Original acceptance criteria

        Returns:
            Context for code review
        """
        query = f"{pr_description} {' '.join(acceptance_criteria)}"[:500]

        context = await self.build_context(
            agent_id=agent_id,
            squad_id=squad_id,
            query=query,
            include_code=True,       # Existing patterns
            include_tickets=False,
            include_docs=True,       # Style guides, best practices
            include_conversations=False,
            include_decisions=True,  # ADRs to verify compliance
            max_results_per_source=3,
        )

        # Add PR details
        context["pr_description"] = pr_description
        context["code_diff"] = code_diff[:5000]  # Limit diff size
        context["acceptance_criteria"] = acceptance_criteria

        return context

    async def store_context_in_memory(
        self,
        agent_id: UUID,
        task_execution_id: Optional[UUID],
        key: str,
        value: Any,
        ttl_seconds: int = 3600,
    ) -> None:
        """
        Store information in short-term memory.

        Args:
            agent_id: Agent UUID
            task_execution_id: Optional task execution UUID
            key: Memory key
            value: Value to store
            ttl_seconds: Time to live in seconds (default 1 hour)
        """
        await self.memory.store(
            agent_id=agent_id,
            task_execution_id=task_execution_id,
            key=key,
            value=value,
            ttl_seconds=ttl_seconds,
        )

    async def update_rag_with_conversation(
        self,
        squad_id: UUID,
        task_execution_id: UUID,
        conversation_summary: str,
    ) -> None:
        """
        Store conversation summary in RAG for future reference.

        Args:
            squad_id: Squad UUID
            task_execution_id: Task execution UUID
            conversation_summary: Summary of conversation
        """
        await self.rag.upsert(
            squad_id=squad_id,
            namespace="conversations",
            documents=[{
                "id": f"conversation_{task_execution_id}",
                "text": conversation_summary,
                "metadata": {
                    "task_execution_id": str(task_execution_id),
                    "created_at": datetime.utcnow().isoformat(),
                },
            }],
        )

    async def update_rag_with_decision(
        self,
        squad_id: UUID,
        decision_id: str,
        decision_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Store architecture decision in RAG.

        Args:
            squad_id: Squad UUID
            decision_id: Decision identifier
            decision_text: ADR or decision text
            metadata: Optional metadata
        """
        await self.rag.upsert(
            squad_id=squad_id,
            namespace="decisions",
            documents=[{
                "id": decision_id,
                "text": decision_text,
                "metadata": metadata or {},
            }],
        )

    # Helper methods

    async def _get_squad_metadata(self, squad_id: UUID) -> Dict[str, Any]:
        """Get squad metadata from database"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Squad).where(Squad.id == squad_id)
            )
            squad = result.scalar_one_or_none()

            if not squad:
                return {}

            return {
                "id": str(squad.id),
                "name": squad.name,
                "description": squad.description,
                "project_id": str(squad.project_id),
                "created_at": squad.created_at.isoformat(),
            }

    async def _get_agent_metadata(self, agent_id: UUID) -> Dict[str, Any]:
        """Get agent metadata from database"""
        from backend.models.squad import SquadMember
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SquadMember).where(SquadMember.id == agent_id)
            )
            agent = result.scalar_one_or_none()

            if not agent:
                return {}

            return {
                "id": str(agent.id),
                "name": agent.name,
                "role": agent.role,
                "specialization": agent.specialization,
                "llm_provider": agent.llm_provider,
                "llm_model": agent.llm_model,
            }
