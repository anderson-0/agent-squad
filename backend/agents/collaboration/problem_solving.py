"""
Problem Solving Pattern

Enables agents to collaboratively solve problems by:
1. Broadcasting questions to relevant team members
2. Collecting answers from multiple agents
3. Synthesizing the best solution
4. Sharing learnings with the team
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.communication.message_bus import MessageBus
from backend.agents.context.context_manager import ContextManager
from backend.services.agent_service import AgentService
from backend.services.task_execution_service import TaskExecutionService
from backend.schemas.agent_message import Question, Answer


class ProblemSolvingPattern:
    """
    Collaborative Problem Solving Pattern

    When an agent is stuck or needs input:
    1. Agent broadcasts question to relevant team members
    2. Team members respond with their perspectives
    3. Responses are collected and synthesized
    4. Best solution is chosen and shared
    """

    def __init__(
        self,
        message_bus: MessageBus,
        context_manager: ContextManager,
    ):
        """
        Initialize problem solving pattern

        Args:
            message_bus: Message bus for communication
            context_manager: Context manager for RAG
        """
        self.message_bus = message_bus
        self.context_manager = context_manager

    async def broadcast_question(
        self,
        db: AsyncSession,
        asker_id: UUID,
        task_execution_id: UUID,
        question: str,
        context: Dict[str, Any],
        relevant_roles: Optional[List[str]] = None,
        urgency: str = "normal",
    ) -> str:
        """
        Broadcast a question to relevant team members.

        Args:
            db: Database session
            asker_id: Agent asking the question
            task_execution_id: Task execution ID
            question: Question text
            context: Question context
            relevant_roles: Optional list of relevant roles (backend_developer, tech_lead, etc.)
            urgency: Question urgency (low, normal, high, critical)

        Returns:
            Question ID for tracking responses
        """
        # Get asker details
        asker = await AgentService.get_squad_member(db, asker_id)
        if not asker:
            raise ValueError(f"Agent {asker_id} not found")

        # Get task execution
        execution = await TaskExecutionService.get_task_execution(db, task_execution_id)
        if not execution:
            raise ValueError(f"Task execution {task_execution_id} not found")

        # Get all squad members
        squad_members = await AgentService.get_squad_members(
            db, execution.squad_id, active_only=True
        )

        # Filter by relevant roles if specified
        if relevant_roles:
            recipients = [m for m in squad_members if m.role in relevant_roles and m.id != asker_id]
        else:
            # Send to all except asker
            recipients = [m for m in squad_members if m.id != asker_id]

        # Format question with context
        formatted_question = f"""
**Question from {asker.role}**:
{question}

**Context**:
{context.get('issue_description', 'N/A')}

**What I've tried**:
{chr(10).join([f'- {attempt}' for attempt in context.get('attempted_solutions', [])])}

**Why I need help**:
{context.get('why_stuck', 'Need expertise or additional perspective')}

**Urgency**: {urgency}
        """

        # Create unique question ID
        question_id = f"question_{task_execution_id}_{asker_id}_{datetime.utcnow().timestamp()}"

        # Broadcast to recipients
        for recipient in recipients:
            await self.message_bus.send_message(
                sender_id=asker_id,
                recipient_id=recipient.id,
                content=formatted_question,
                message_type="question",
                metadata={
                    "question_id": question_id,
                    "urgency": urgency,
                    "context": context,
                },
                task_execution_id=task_execution_id,
            )

        # Log the broadcast
        await TaskExecutionService.add_log(
            db=db,
            execution_id=task_execution_id,
            level="info",
            message=f"{asker.role} broadcast question to {len(recipients)} team members",
            metadata={
                "question_id": question_id,
                "recipients": [str(r.id) for r in recipients],
                "urgency": urgency,
            },
        )

        return question_id

    async def collect_answers(
        self,
        db: AsyncSession,
        task_execution_id: UUID,
        question_id: str,
        timeout_seconds: int = 300,
    ) -> List[Dict[str, Any]]:
        """
        Collect answers to a question from team members.

        Args:
            db: Database session
            task_execution_id: Task execution ID
            question_id: Question ID to track
            timeout_seconds: Timeout for collecting answers (default 5 minutes)

        Returns:
            List of answers with agent details
        """
        # Get all messages for this execution
        messages = await TaskExecutionService.get_execution_messages(
            db, task_execution_id
        )

        # Filter answers to this specific question
        answers = []
        for msg in messages:
            if msg.message_type == "answer":
                metadata = msg.message_metadata or {}
                if metadata.get("question_id") == question_id:
                    # Get responder details
                    responder = await AgentService.get_squad_member(db, msg.sender_id)

                    answers.append({
                        "responder_id": str(msg.sender_id),
                        "responder_role": responder.role if responder else "unknown",
                        "answer": msg.content,
                        "timestamp": msg.created_at.isoformat(),
                        "metadata": metadata,
                    })

        return answers

    async def synthesize_solution(
        self,
        db: AsyncSession,
        asker_id: UUID,
        question: str,
        answers: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Synthesize the best solution from multiple answers.

        Uses the asker agent's LLM to analyze and synthesize responses.

        Args:
            db: Database session
            asker_id: Agent who asked the question
            question: Original question
            answers: List of answers from team
            context: Question context

        Returns:
            Synthesized solution
        """
        # Get asker agent
        agent = await AgentService.get_or_create_agent(db, asker_id)

        # Format answers for LLM
        answers_text = "\n\n".join([
            f"**Answer from {a['responder_role']}** (at {a['timestamp']}):\n{a['answer']}"
            for a in answers
        ])

        # Create synthesis prompt
        synthesis_prompt = f"""
You asked the team for help with this question:

{question}

**Context**:
{context.get('issue_description', 'N/A')}

**Team Responses** ({len(answers)} responses):

{answers_text}

Please synthesize the best solution:

1. **Summary of Suggestions**:
   - What are the main approaches suggested?
   - Are there common themes?

2. **Recommended Solution**:
   - Which approach is best for this situation?
   - Why is this the best choice?
   - How should you implement it?

3. **Next Steps**:
   - Concrete actions to take
   - Order of implementation

4. **Potential Risks**:
   - What could go wrong?
   - How to mitigate?

5. **Who to Thank**:
   - Which team members provided the most helpful insights?

Be specific and actionable. Choose the best path forward.
        """

        # Get synthesis from agent's LLM
        response = await agent.process_message(
            synthesis_prompt,
            context={
                "question": question,
                "answers": answers,
                "action": "solution_synthesis"
            }
        )

        return {
            "question": question,
            "answer_count": len(answers),
            "synthesized_solution": response.content,
            "recommended_approach": self._extract_recommendation(response.content),
            "next_steps": self._extract_next_steps(response.content),
            "contributors": [a['responder_role'] for a in answers],
        }

    async def share_learning(
        self,
        db: AsyncSession,
        task_execution_id: UUID,
        question: str,
        solution: Dict[str, Any],
        squad_id: UUID,
    ) -> None:
        """
        Share the learning with the team and store in RAG.

        Args:
            db: Database session
            task_execution_id: Task execution ID
            question: Original question
            solution: Synthesized solution
            squad_id: Squad ID
        """
        # Format learning
        learning_text = f"""
**Problem**: {question}

**Solution**: {solution.get('recommended_approach', 'See full synthesis')}

**Contributors**: {', '.join(solution.get('contributors', []))}

**Full Synthesis**:
{solution.get('synthesized_solution', '')}
        """

        # Store in RAG for future reference
        await self.context_manager.update_rag_with_conversation(
            squad_id=squad_id,
            task_execution_id=task_execution_id,
            conversation_summary=learning_text,
        )

        # Log the learning
        await TaskExecutionService.add_log(
            db=db,
            execution_id=task_execution_id,
            level="info",
            message=f"Problem solved collaboratively with {solution.get('answer_count', 0)} team responses",
            metadata={
                "question": question,
                "contributors": solution.get('contributors', []),
            },
        )

    async def solve_problem_collaboratively(
        self,
        db: AsyncSession,
        asker_id: UUID,
        task_execution_id: UUID,
        question: str,
        context: Dict[str, Any],
        relevant_roles: Optional[List[str]] = None,
        timeout_seconds: int = 300,
    ) -> Dict[str, Any]:
        """
        Complete problem-solving flow: ask → collect → synthesize → share.

        This is the main entry point for collaborative problem solving.

        Args:
            db: Database session
            asker_id: Agent asking for help
            task_execution_id: Task execution ID
            question: Question text
            context: Question context with issue_description, attempted_solutions, why_stuck
            relevant_roles: Optional list of relevant roles to ask
            timeout_seconds: Timeout for collecting answers

        Returns:
            Complete solution with synthesis and next steps
        """
        # Step 1: Broadcast question
        question_id = await self.broadcast_question(
            db=db,
            asker_id=asker_id,
            task_execution_id=task_execution_id,
            question=question,
            context=context,
            relevant_roles=relevant_roles,
            urgency=context.get("urgency", "normal"),
        )

        # Step 2: Wait for answers (in production, this would be event-driven)
        # For Phase 3, we simulate the wait
        await asyncio.sleep(1)  # Simulated wait for responses

        # Step 3: Collect answers
        answers = await self.collect_answers(
            db=db,
            task_execution_id=task_execution_id,
            question_id=question_id,
            timeout_seconds=timeout_seconds,
        )

        # If no answers, return guidance to escalate
        if not answers:
            return {
                "question": question,
                "answer_count": 0,
                "recommendation": "No responses received. Consider escalating to human or rephrasing question.",
                "next_steps": ["Escalate to human", "Try different approach"],
            }

        # Step 4: Synthesize solution
        solution = await self.synthesize_solution(
            db=db,
            asker_id=asker_id,
            question=question,
            answers=answers,
            context=context,
        )

        # Step 5: Share learning
        execution = await TaskExecutionService.get_task_execution(db, task_execution_id)
        if execution:
            await self.share_learning(
                db=db,
                task_execution_id=task_execution_id,
                question=question,
                solution=solution,
                squad_id=execution.squad_id,
            )

        return solution

    # Helper methods

    def _extract_recommendation(self, content: str) -> str:
        """Extract recommended approach from synthesis"""
        lines = content.split('\n')
        in_section = False
        recommendation_lines = []

        for line in lines:
            if 'recommended' in line.lower() and ':' in line:
                in_section = True
                continue
            if in_section:
                if line.strip() and not line.strip().startswith('#'):
                    recommendation_lines.append(line.strip())
                    if len(recommendation_lines) >= 3:
                        break

        return ' '.join(recommendation_lines) if recommendation_lines else "See full synthesis"

    def _extract_next_steps(self, content: str) -> List[str]:
        """Extract next steps from synthesis"""
        lines = content.split('\n')
        in_section = False
        steps = []

        for line in lines:
            if 'next steps' in line.lower() and ':' in line:
                in_section = True
                continue
            if in_section and line.strip().startswith('-'):
                steps.append(line.strip()[1:].strip())
            elif in_section and line.strip() and not line.strip().startswith('-'):
                if line.strip().startswith('#'):
                    break

        return steps[:5]  # Max 5 steps
