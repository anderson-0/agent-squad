"""
Inngest workflow functions for agent execution

This module contains background workflow functions that execute multi-agent
collaborations asynchronously. Users get instant API responses while workflows
run in the background.

Key Workflows:
- execute_agent_workflow: Multi-agent collaboration (PM → Backend → QA)
- execute_single_agent: Single agent execution
- execute_agent_with_tools: Agent with MCP tool execution

Performance:
- Before: API blocks for 5-30s (waiting for LLM)
- After: API responds in < 100ms (workflow queued)

Benefits:
- Instant user experience
- Automatic retries on failure
- Durable execution (survives crashes)
- Independent worker scaling
- Built-in monitoring
"""
from inngest import Inngest
from backend.core.inngest import inngest
from backend.core.database import get_db_context
from backend.models.project import TaskExecution
from backend.models.squad import SquadMember
from uuid import UUID
import logging
from typing import Dict, Any
from sqlalchemy import select

logger = logging.getLogger(__name__)


@inngest.create_function(
    fn_id="execute-agent-workflow",
    trigger=inngest.event("agent/workflow.execute"),
)
async def execute_agent_workflow(ctx, step):
    """
    Execute multi-agent workflow in background

    This function orchestrates a full PM → Backend Dev → QA workflow
    asynchronously, allowing the API to return instantly while the
    workflow executes in the background.

    Event payload:
    {
        "task_execution_id": "uuid",
        "squad_id": "uuid",
        "user_id": "uuid",
        "organization_id": "uuid",
        "message": "User request"
    }

    Steps:
    1. Update status to "running"
    2. Get squad agents (PM, Backend Dev, QA)
    3. Execute PM agent (planning)
    4. Execute Backend Dev agent (implementation)
    5. Execute QA agent (testing)
    6. Update status to "completed"

    Returns:
        Dict with execution status and results
    """
    data = ctx.event.data
    task_execution_id = UUID(data["task_execution_id"])
    squad_id = UUID(data["squad_id"])
    user_id = UUID(data["user_id"])
    organization_id = UUID(data.get("organization_id")) if data.get("organization_id") else None
    message = data["message"]

    logger.info(
        f"Starting workflow execution: {task_execution_id} "
        f"(squad={squad_id}, user={user_id})"
    )

    # Step 1: Update status to "running"
    await step.run(
        "update-status-running",
        lambda: update_execution_status(task_execution_id, "running")
    )

    # Step 2: Get squad members
    squad_members = await step.run(
        "get-squad-members",
        lambda: get_squad_members(squad_id),
        retries=3  # Retry database failures
    )

    if not squad_members:
        logger.error(f"No squad members found for squad {squad_id}")
        await step.run(
            "update-status-failed",
            lambda: update_execution_status(
                task_execution_id,
                "failed",
                {"error": "No squad members found"}
            )
        )
        return {"status": "failed", "error": "No squad members found"}

    # Step 3: Execute PM agent (planning phase)
    logger.info(f"Executing PM agent for execution {task_execution_id}")
    pm_response = await step.run(
        "execute-pm-agent",
        lambda: execute_agent(
            squad_member=squad_members.get("project_manager"),
            message=message,
            task_execution_id=task_execution_id,
            user_id=user_id,
            organization_id=organization_id,
            role="project_manager"
        ),
        retries=2  # Retry LLM failures
    )

    if not pm_response or pm_response.get("error"):
        logger.error(f"PM agent failed: {pm_response}")
        await step.run(
            "update-status-failed",
            lambda: update_execution_status(
                task_execution_id,
                "failed",
                {"error": "PM agent failed", "details": pm_response}
            )
        )
        return {"status": "failed", "pm_error": pm_response}

    # Step 4: Execute Backend Dev agent (implementation phase)
    logger.info(f"Executing Backend Dev agent for execution {task_execution_id}")
    backend_message = f"PM Task: {pm_response.get('content', message)}"

    backend_response = await step.run(
        "execute-backend-agent",
        lambda: execute_agent(
            squad_member=squad_members.get("backend_developer"),
            message=backend_message,
            task_execution_id=task_execution_id,
            user_id=user_id,
            organization_id=organization_id,
            role="backend_developer",
            context={"pm_response": pm_response}
        ),
        retries=2
    )

    if not backend_response or backend_response.get("error"):
        logger.error(f"Backend agent failed: {backend_response}")
        await step.run(
            "update-status-failed",
            lambda: update_execution_status(
                task_execution_id,
                "failed",
                {"error": "Backend agent failed", "details": backend_response}
            )
        )
        return {"status": "failed", "backend_error": backend_response}

    # Step 5: Execute QA agent (testing phase)
    logger.info(f"Executing QA agent for execution {task_execution_id}")
    qa_message = f"Review implementation: {backend_response.get('content', 'Review the code')}"

    qa_response = await step.run(
        "execute-qa-agent",
        lambda: execute_agent(
            squad_member=squad_members.get("tester"),
            message=qa_message,
            task_execution_id=task_execution_id,
            user_id=user_id,
            organization_id=organization_id,
            role="tester",
            context={
                "pm_response": pm_response,
                "backend_response": backend_response
            }
        ),
        retries=2
    )

    if not qa_response or qa_response.get("error"):
        logger.error(f"QA agent failed: {qa_response}")
        await step.run(
            "update-status-failed",
            lambda: update_execution_status(
                task_execution_id,
                "failed",
                {"error": "QA agent failed", "details": qa_response}
            )
        )
        return {"status": "failed", "qa_error": qa_response}

    # Step 6: Update status to "completed" with final results
    final_result = {
        "pm": pm_response,
        "backend_developer": backend_response,
        "qa_tester": qa_response,
        "status": "completed"
    }

    await step.run(
        "update-status-completed",
        lambda: update_execution_status(task_execution_id, "completed", final_result)
    )

    logger.info(f"Workflow completed successfully: {task_execution_id}")

    return {
        "status": "completed",
        "execution_id": str(task_execution_id),
        "result": final_result
    }


@inngest.create_function(
    fn_id="execute-single-agent",
    trigger=inngest.event("agent/single.execute"),
)
async def execute_single_agent_workflow(ctx, step):
    """
    Execute single agent in background

    Simpler workflow for single agent execution (no multi-agent collaboration).
    Useful for individual agent tasks.

    Event payload:
    {
        "agent_id": "uuid",
        "message": "User request",
        "task_execution_id": "uuid" (optional),
        "user_id": "uuid"
    }
    """
    data = ctx.event.data
    agent_id = UUID(data["agent_id"])
    message = data["message"]
    task_execution_id = UUID(data.get("task_execution_id")) if data.get("task_execution_id") else None
    user_id = UUID(data["user_id"])

    logger.info(f"Starting single agent execution: {agent_id}")

    # Get squad member
    squad_member = await step.run(
        "get-squad-member",
        lambda: get_squad_member_by_id(agent_id),
        retries=3
    )

    if not squad_member:
        logger.error(f"Squad member not found: {agent_id}")
        return {"status": "failed", "error": "Squad member not found"}

    # Execute agent
    response = await step.run(
        "execute-agent",
        lambda: execute_agent(
            squad_member=squad_member,
            message=message,
            task_execution_id=task_execution_id,
            user_id=user_id,
            role=squad_member.role
        ),
        retries=2
    )

    logger.info(f"Single agent execution completed: {agent_id}")

    return {
        "status": "completed",
        "agent_id": str(agent_id),
        "response": response
    }


# Helper functions

async def update_execution_status(
    execution_id: UUID,
    status: str,
    result: Dict[str, Any] = None
):
    """
    Update task execution status in database

    Args:
        execution_id: Task execution ID
        status: New status (running, completed, failed)
        result: Execution result data (optional)
    """
    async with get_db_context() as db:
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            logger.error(f"Task execution not found: {execution_id}")
            return

        execution.status = status

        if result:
            # Merge with existing result
            if execution.result:
                execution.result.update(result)
            else:
                execution.result = result

        await db.commit()

        logger.info(f"Updated execution {execution_id}: status={status}")


async def get_squad_members(squad_id: UUID) -> Dict[str, SquadMember]:
    """
    Get all squad members for a squad

    Returns:
        Dict mapping role to SquadMember
        {
            "project_manager": SquadMember,
            "backend_developer": SquadMember,
            "tester": SquadMember
        }
    """
    async with get_db_context() as db:
        result = await db.execute(
            select(SquadMember).where(SquadMember.squad_id == squad_id)
        )
        members = result.scalars().all()

        # Map by role
        members_by_role = {member.role: member for member in members}

        logger.info(f"Found {len(members)} squad members for squad {squad_id}")

        return members_by_role


async def get_squad_member_by_id(member_id: UUID) -> SquadMember:
    """Get squad member by ID"""
    async with get_db_context() as db:
        member = await db.get(SquadMember, member_id)
        return member


async def execute_agent(
    squad_member: SquadMember,
    message: str,
    task_execution_id: UUID = None,
    user_id: UUID = None,
    organization_id: UUID = None,
    role: str = None,
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Execute a single agent with message

    Phase 2 Optimization: Uses agent pool to reuse instances (60% faster)

    Performance:
    - Cache hit: <0.05s (agent already in pool)
    - Cache miss: 0.126s (create new agent)
    - Expected hit rate: 70-90% in production

    Args:
        squad_member: SquadMember instance
        message: User message to process
        task_execution_id: Task execution ID (for tracking)
        user_id: User ID (for cost tracking)
        organization_id: Organization ID (for cost tracking)
        role: Agent role (for logging)
        context: Additional context dict

    Returns:
        Dict with agent response
    """
    if not squad_member:
        logger.error(f"Squad member is None for role {role}")
        return {"error": "Squad member not found"}

    try:
        # Import here to avoid circular imports
        from backend.services.agent_pool import get_agent_pool

        # Get agent from pool (Phase 2 optimization)
        # This reuses agents instead of creating new ones every time
        agent_pool = await get_agent_pool()
        agent = await agent_pool.get_or_create_agent(squad_member)

        # Process message
        async with get_db_context() as db:
            response = await agent.process_message(
                message=message,
                context=context or {},
                squad_id=squad_member.squad_id,
                user_id=user_id,
                organization_id=organization_id,
                task_execution_id=task_execution_id,
                track_cost=True,
                db=db
            )

            logger.info(
                f"Agent {role} processed message: "
                f"tokens={response.metadata.get('total_tokens', 0)}"
            )

            return response.model_dump()

    except Exception as e:
        logger.error(f"Error executing agent {role}: {e}", exc_info=True)
        return {"error": str(e)}
