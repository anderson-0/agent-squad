"""
Inngest workflow functions for HITL (Human-in-the-Loop) approval workflows

This module contains background workflow functions that handle approval
events and resume agent workflows after human approval.

Workflows:
- handle_approval_approved: Resume workflow after approval
- handle_approval_rejected: Handle rejection and notify squad
"""
from inngest import Inngest
from backend.core.inngest import inngest
from backend.core.database import get_db_context
from backend.models.approval_request import ApprovalRequest, ApprovalStatus
from backend.models.squad import Squad
from uuid import UUID
import logging
from typing import Dict, Any
from sqlalchemy import select

logger = logging.getLogger(__name__)


@inngest.create_function(
    fn_id="handle-approval-approved",
    trigger=inngest.event("hitl/approval.approved"),
)
async def handle_approval_approved(ctx, step):
    """
    Handle approved HITL requests.
    
    This function is triggered when a human approves a pending request.
    It processes the approval and can resume agent workflows, execute
    approved actions, or notify relevant systems.
    
    Event payload:
    {
        "approval_id": "uuid",
        "squad_id": "uuid",
        "agent_id": "uuid",
        "action_type": "deploy|delete_resource|etc",
        "payload": {...},
        "approved_at": "iso_timestamp"
    }
    
    Steps:
    1. Validate approval exists
    2. Execute approved action based on action_type
    3. Resume squad if paused
    4. Notify squad members
    """
    data = ctx.event.data
    approval_id = UUID(data["approval_id"])
    squad_id = UUID(data["squad_id"])
    action_type = data["action_type"]
    payload = data.get("payload", {})
    
    logger.info(
        f"Processing approved request: {approval_id} "
        f"(squad={squad_id}, action={action_type})"
    )
    
    # Step 1: Validate approval
    async with get_db_context() as db:
        result = await db.execute(
            select(ApprovalRequest).filter(ApprovalRequest.id == approval_id)
        )
        approval = result.scalar_one_or_none()
        
        if not approval:
            logger.error(f"Approval {approval_id} not found")
            return {"status": "error", "message": "Approval not found"}
        
        if approval.status != ApprovalStatus.APPROVED:
            logger.warning(f"Approval {approval_id} status is {approval.status}, expected APPROVED")
            return {"status": "skipped", "message": "Approval not in approved state"}
    
    # Step 2: Execute approved action
    action_result = await step.run(
        "execute-approved-action",
        lambda: execute_approved_action(action_type, payload, squad_id),
        retries=2
    )
    
    # Step 3: Resume squad if paused
    await step.run(
        "resume-squad-if-paused",
        lambda: resume_squad_if_paused(squad_id)
    )
    
    logger.info(f"Approval {approval_id} processed successfully")
    
    return {
        "status": "completed",
        "approval_id": str(approval_id),
        "action_result": action_result
    }


@inngest.create_function(
    fn_id="handle-approval-rejected",
    trigger=inngest.event("hitl/approval.rejected"),
)
async def handle_approval_rejected(ctx, step):
    """
    Handle rejected HITL requests.
    
    This function is triggered when a human rejects a pending request.
    It processes the rejection, logs the decision, and can notify
    relevant systems or agents.
    
    Event payload:
    {
        "approval_id": "uuid",
        "squad_id": "uuid",
        "agent_id": "uuid",
        "action_type": "deploy|delete_resource|etc",
        "payload": {...},
        "rejected_at": "iso_timestamp"
    }
    
    Steps:
    1. Validate rejection exists
    2. Log rejection reason
    3. Notify squad about rejection
    4. Optional: Suggest alternative actions
    """
    data = ctx.event.data
    approval_id = UUID(data["approval_id"])
    squad_id = UUID(data["squad_id"])
    action_type = data["action_type"]
    
    logger.info(
        f"Processing rejected request: {approval_id} "
        f"(squad={squad_id}, action={action_type})"
    )
    
    # Step 1: Validate rejection
    async with get_db_context() as db:
        result = await db.execute(
            select(ApprovalRequest).filter(ApprovalRequest.id == approval_id)
        )
        approval = result.scalar_one_or_none()
        
        if not approval:
            logger.error(f"Approval {approval_id} not found")
            return {"status": "error", "message": "Approval not found"}
        
        if approval.status != ApprovalStatus.REJECTED:
            logger.warning(f"Approval {approval_id} status is {approval.status}, expected REJECTED")
            return {"status": "skipped", "message": "Approval not in rejected state"}
    
    # Step 2: Log rejection
    await step.run(
        "log-rejection",
        lambda: log_rejection(approval_id, squad_id, action_type)
    )
    
    # Step 3: Notify squad (optional - can be extended)
    # This could send a message to the squad's conversation or update task status
    
    logger.info(f"Rejection {approval_id} processed successfully")
    
    return {
        "status": "completed",
        "approval_id": str(approval_id),
        "action": "logged"
    }


# Helper functions

async def execute_approved_action(
    action_type: str,
    payload: Dict[str, Any],
    squad_id: UUID
) -> Dict[str, Any]:
    """
    Execute the approved action based on action_type.
    
    This is a placeholder that should be extended with actual
    action handlers for different action types.
    """
    logger.info(f"Executing approved action: {action_type} for squad {squad_id}")
    
    # Action handlers can be added here based on action_type
    # For example:
    # - "deploy": trigger deployment workflow
    # - "delete_resource": delete specified resource
    # - "merge_pr": merge pull request
    # - etc.
    
    action_handlers = {
        "deploy": handle_deploy_action,
        "delete_resource": handle_delete_resource_action,
        "merge_pr": handle_merge_pr_action,
        # Add more handlers as needed
    }
    
    handler = action_handlers.get(action_type)
    if handler:
        return await handler(payload, squad_id)
    else:
        logger.warning(f"No handler for action type: {action_type}")
        return {
            "status": "no_handler",
            "action_type": action_type,
            "message": f"Action type '{action_type}' has no registered handler"
        }


async def handle_deploy_action(payload: Dict[str, Any], squad_id: UUID) -> Dict[str, Any]:
    """Handle deployment approval."""
    service = payload.get("service")
    environment = payload.get("environment")
    
    logger.info(f"Deploying {service} to {environment} for squad {squad_id}")
    
    # TODO: Implement actual deployment logic
    # This could trigger a deployment pipeline, update deployment status, etc.
    
    return {
        "status": "success",
        "action": "deploy",
        "service": service,
        "environment": environment
    }


async def handle_delete_resource_action(payload: Dict[str, Any], squad_id: UUID) -> Dict[str, Any]:
    """Handle resource deletion approval."""
    resource = payload.get("resource")
    
    logger.info(f"Deleting resource {resource} for squad {squad_id}")
    
    # TODO: Implement actual resource deletion logic
    
    return {
        "status": "success",
        "action": "delete_resource",
        "resource": resource
    }


async def handle_merge_pr_action(payload: Dict[str, Any], squad_id: UUID) -> Dict[str, Any]:
    """Handle pull request merge approval."""
    pr_number = payload.get("pr_number")
    repo = payload.get("repo")
    
    logger.info(f"Merging PR #{pr_number} in {repo} for squad {squad_id}")
    
    # TODO: Implement actual PR merge logic using GitHub API
    
    return {
        "status": "success",
        "action": "merge_pr",
        "pr_number": pr_number,
        "repo": repo
    }


async def resume_squad_if_paused(squad_id: UUID) -> None:
    """Resume squad if it was paused waiting for approval."""
    async with get_db_context() as db:
        result = await db.execute(select(Squad).filter(Squad.id == squad_id))
        squad = result.scalar_one_or_none()
        
        if squad and squad.is_paused:
            logger.info(f"Resuming paused squad {squad_id}")
            squad.is_paused = False
            await db.commit()
        else:
            logger.info(f"Squad {squad_id} was not paused, no action needed")


async def log_rejection(approval_id: UUID, squad_id: UUID, action_type: str) -> None:
    """Log the rejection for audit purposes."""
    logger.info(
        f"REJECTION LOGGED: approval_id={approval_id}, "
        f"squad_id={squad_id}, action_type={action_type}"
    )
    
    # TODO: Store rejection in audit log table if needed
    # This could also trigger notifications to relevant stakeholders
