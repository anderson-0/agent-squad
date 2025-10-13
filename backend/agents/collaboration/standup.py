"""
Standup Pattern

Implements async daily standup for agent squads:
1. PM requests updates from all team members
2. Agents provide updates (yesterday, today, blockers)
3. PM analyzes updates and identifies issues
4. PM broadcasts insights and action items
5. Store insights for team visibility
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.communication.message_bus import MessageBus
from backend.services.agent_service import AgentService
from backend.services.task_execution_service import TaskExecutionService


class StandupPattern:
    """
    Async Standup Collaboration Pattern

    Daily standup workflow:
    1. PM requests updates from all active squad members
    2. Each agent responds with: what they did, what they're doing, blockers
    3. PM collects and analyzes all updates
    4. PM identifies blockers, risks, and coordination needs
    5. PM broadcasts key insights to the team
    """

    def __init__(self, message_bus: MessageBus):
        """
        Initialize standup pattern

        Args:
            message_bus: Message bus for communication
        """
        self.message_bus = message_bus

    async def request_updates(
        self,
        db: AsyncSession,
        pm_id: UUID,
        squad_id: UUID,
        task_execution_id: Optional[UUID] = None,
    ) -> str:
        """
        PM requests standup updates from all team members.

        Args:
            db: Database session
            pm_id: Project Manager agent ID
            squad_id: Squad ID
            task_execution_id: Optional task execution ID

        Returns:
            Standup session ID
        """
        # Get PM details
        pm = await AgentService.get_squad_member(db, pm_id)
        if not pm:
            raise ValueError(f"PM {pm_id} not found")

        # Get all active squad members (except PM)
        members = await AgentService.get_squad_members(db, squad_id, active_only=True)
        team_members = [m for m in members if m.id != pm_id]

        # Create standup session ID
        standup_id = f"standup_{squad_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Request format
        update_request = """
**Daily Standup Update Request**

Please provide your standup update:

**1. Yesterday / Since Last Update**:
   - What did you accomplish?
   - Any deliverables completed?

**2. Today / Next Steps**:
   - What are you working on now?
   - What's your focus for today?

**3. Blockers / Help Needed**:
   - Any blockers preventing progress?
   - Do you need help from teammates?
   - Any risks or concerns?

**4. Progress Status** (0-100%):
   - Overall progress on your current tasks

Please be specific and concise.
        """

        # Send to all team members
        for member in team_members:
            await self.message_bus.send_message(
                sender_id=pm_id,
                recipient_id=member.id,
                content=update_request,
                message_type="status_request",
                metadata={
                    "standup_id": standup_id,
                    "requested_at": datetime.utcnow().isoformat(),
                },
                task_execution_id=task_execution_id,
            )

        # Log the request
        if task_execution_id:
            await TaskExecutionService.add_log(
                db=db,
                execution_id=task_execution_id,
                level="info",
                message=f"PM requested standup updates from {len(team_members)} team members",
                metadata={
                    "standup_id": standup_id,
                    "team_size": len(team_members),
                },
            )

        return standup_id

    async def collect_updates(
        self,
        db: AsyncSession,
        task_execution_id: UUID,
        standup_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Collect standup updates from team members.

        Args:
            db: Database session
            task_execution_id: Task execution ID
            standup_id: Standup session ID

        Returns:
            List of updates from team members
        """
        # Get all messages for this execution
        messages = await TaskExecutionService.get_execution_messages(
            db, task_execution_id
        )

        # Filter status updates for this standup
        updates = []
        for msg in messages:
            if msg.message_type == "status_update":
                metadata = msg.message_metadata or {}
                if metadata.get("standup_id") == standup_id:
                    # Get agent details
                    agent = await AgentService.get_squad_member(db, msg.sender_id)

                    updates.append({
                        "agent_id": str(msg.sender_id),
                        "agent_role": agent.role if agent else "unknown",
                        "update": msg.content,
                        "timestamp": msg.created_at.isoformat(),
                        "metadata": metadata,
                    })

        return updates

    async def analyze_updates(
        self,
        db: AsyncSession,
        pm_id: UUID,
        updates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        PM analyzes standup updates to identify patterns and issues.

        Args:
            db: Database session
            pm_id: PM agent ID
            updates: List of updates from team

        Returns:
            Analysis with insights and action items
        """
        # Get PM agent
        pm_agent = await AgentService.get_or_create_agent(db, pm_id)

        # Format updates for analysis
        updates_text = "\n\n---\n\n".join([
            f"**{u['agent_role']}** (at {u['timestamp']}):\n{u['update']}"
            for u in updates
        ])

        # Create analysis prompt
        analysis_prompt = f"""
Daily Standup Summary - {len(updates)} team members reporting:

{updates_text}

Please analyze and provide:

**1. Overall Team Progress**:
   - What's the overall velocity?
   - Are we on track?
   - Any patterns or trends?

**2. Blockers Identified**:
   - List all blockers mentioned
   - Severity (critical, high, medium, low)
   - Suggested solutions or who can help

**3. Team Members Needing Help**:
   - Who is stuck or struggling?
   - What kind of help do they need?
   - Who could provide that help?

**4. Tasks at Risk**:
   - Any tasks likely to miss deadlines?
   - Why are they at risk?
   - Mitigation strategies?

**5. Positive Highlights**:
   - What's going well?
   - Who made significant progress?
   - Any wins to celebrate?

**6. Action Items for PM**:
   - What do I need to do today?
   - Who do I need to follow up with?
   - Any escalations needed?

**7. Key Message for Team**:
   - What should I communicate to the team?
   - Any coordination needed?

Be specific and actionable. Focus on what matters most.
        """

        # Get analysis from PM's LLM
        response = await pm_agent.process_message(
            analysis_prompt,
            context={
                "updates": updates,
                "action": "standup_analysis"
            }
        )

        return {
            "update_count": len(updates),
            "analysis": response.content,
            "blockers": self._extract_blockers(response.content),
            "at_risk_members": self._extract_at_risk(response.content),
            "action_items": self._extract_action_items(response.content),
            "team_message": self._extract_team_message(response.content),
        }

    async def broadcast_insights(
        self,
        db: AsyncSession,
        pm_id: UUID,
        squad_id: UUID,
        task_execution_id: Optional[UUID],
        analysis: Dict[str, Any],
        standup_id: str,
    ) -> None:
        """
        PM broadcasts key insights and action items to the team.

        Args:
            db: Database session
            pm_id: PM agent ID
            squad_id: Squad ID
            task_execution_id: Optional task execution ID
            analysis: Standup analysis
            standup_id: Standup session ID
        """
        # Get all squad members
        members = await AgentService.get_squad_members(db, squad_id, active_only=True)
        team_members = [m for m in members if m.id != pm_id]

        # Format insights message
        insights_message = f"""
**Daily Standup Summary**

**Team Status**: {analysis['update_count']} members reporting

{analysis.get('team_message', '')}

**Blockers Identified** ({len(analysis.get('blockers', []))}):
{chr(10).join([f'- {b}' for b in analysis.get('blockers', [])[:5]])}

**Action Items**:
{chr(10).join([f'- {a}' for a in analysis.get('action_items', [])[:5]])}

**At Risk**:
{chr(10).join([f'- {r}' for r in analysis.get('at_risk_members', [])[:3]])}

Let's stay coordinated and help each other! 🚀
        """

        # Broadcast to all team members
        for member in team_members:
            await self.message_bus.send_message(
                sender_id=pm_id,
                recipient_id=member.id,
                content=insights_message,
                message_type="standup",
                metadata={
                    "standup_id": standup_id,
                    "insights": True,
                },
                task_execution_id=task_execution_id,
            )

        # Log broadcast
        if task_execution_id:
            await TaskExecutionService.add_log(
                db=db,
                execution_id=task_execution_id,
                level="info",
                message=f"PM broadcast standup insights to {len(team_members)} team members",
                metadata={
                    "standup_id": standup_id,
                    "blocker_count": len(analysis.get('blockers', [])),
                    "action_item_count": len(analysis.get('action_items', [])),
                },
            )

    async def conduct_standup(
        self,
        db: AsyncSession,
        pm_id: UUID,
        squad_id: UUID,
        task_execution_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Complete standup flow: request → collect → analyze → broadcast.

        This is the main entry point for conducting async standup.

        Args:
            db: Database session
            pm_id: PM agent ID
            squad_id: Squad ID
            task_execution_id: Optional task execution ID

        Returns:
            Complete standup results with analysis and insights
        """
        # Step 1: Request updates
        standup_id = await self.request_updates(
            db=db,
            pm_id=pm_id,
            squad_id=squad_id,
            task_execution_id=task_execution_id,
        )

        # Step 2: Collect updates (in production, wait for responses)
        # For Phase 3, we'll need to wait or make this async
        if task_execution_id:
            updates = await self.collect_updates(
                db=db,
                task_execution_id=task_execution_id,
                standup_id=standup_id,
            )
        else:
            updates = []

        # If no updates yet, return early status
        if not updates:
            return {
                "standup_id": standup_id,
                "status": "waiting_for_updates",
                "message": "Standup requests sent, waiting for team responses",
            }

        # Step 3: Analyze updates
        analysis = await self.analyze_updates(
            db=db,
            pm_id=pm_id,
            updates=updates,
        )

        # Step 4: Broadcast insights
        await self.broadcast_insights(
            db=db,
            pm_id=pm_id,
            squad_id=squad_id,
            task_execution_id=task_execution_id,
            analysis=analysis,
            standup_id=standup_id,
        )

        return {
            "standup_id": standup_id,
            "status": "completed",
            "update_count": len(updates),
            "analysis": analysis,
        }

    # Helper methods

    def _extract_blockers(self, content: str) -> List[str]:
        """Extract blockers from analysis"""
        lines = content.split('\n')
        in_section = False
        blockers = []

        for line in lines:
            if 'blockers identified' in line.lower():
                in_section = True
                continue
            if in_section and line.strip().startswith('-'):
                blocker_text = line.strip()[1:].strip()
                if blocker_text and len(blocker_text) < 200:
                    blockers.append(blocker_text)
            elif in_section and line.strip() and line.strip().startswith('**'):
                break

        return blockers[:10]

    def _extract_at_risk(self, content: str) -> List[str]:
        """Extract at-risk members or tasks"""
        lines = content.split('\n')
        in_section = False
        at_risk = []

        for line in lines:
            if 'at risk' in line.lower() or 'needing help' in line.lower():
                in_section = True
                continue
            if in_section and line.strip().startswith('-'):
                risk_text = line.strip()[1:].strip()
                if risk_text and len(risk_text) < 200:
                    at_risk.append(risk_text)
            elif in_section and line.strip() and line.strip().startswith('**'):
                break

        return at_risk[:5]

    def _extract_action_items(self, content: str) -> List[str]:
        """Extract action items"""
        lines = content.split('\n')
        in_section = False
        action_items = []

        for line in lines:
            if 'action items' in line.lower():
                in_section = True
                continue
            if in_section and line.strip().startswith('-'):
                action_text = line.strip()[1:].strip()
                if action_text and len(action_text) < 200:
                    action_items.append(action_text)
            elif in_section and line.strip() and line.strip().startswith('**'):
                break

        return action_items[:10]

    def _extract_team_message(self, content: str) -> str:
        """Extract key message for team"""
        lines = content.split('\n')
        in_section = False
        message_lines = []

        for line in lines:
            if 'key message' in line.lower() or 'team message' in line.lower():
                in_section = True
                continue
            if in_section:
                if line.strip() and not line.strip().startswith('**'):
                    message_lines.append(line.strip())
                elif line.strip().startswith('**'):
                    break

        return ' '.join(message_lines[:3]) if message_lines else "Team is making progress!"
