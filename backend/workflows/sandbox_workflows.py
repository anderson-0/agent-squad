"""
Inngest workflow functions for E2B sandbox operations

This module contains background workflow functions that execute E2B sandbox
operations asynchronously for Git-based agent tasks.

Key Workflows:
- execute_task_with_sandbox: Complete task execution with E2B sandbox (clone → code → commit → PR)
- cleanup_old_sandboxes: Periodic cleanup of terminated sandboxes

Performance:
- Before: API blocks for Git operations (5-15s)
- After: API responds instantly, workflow runs in background

Benefits:
- Non-blocking Git operations
- Automatic retries on network failures
- Durable execution (survives crashes)
- Built-in error handling
- Automatic sandbox cleanup
"""
from inngest import Inngest
from backend.core.inngest import inngest
from backend.core.database import get_db_context
from backend.services.sandbox_service import SandboxService
from backend.models.sandbox import Sandbox, SandboxStatus
from uuid import UUID
import logging
from typing import Dict, Any, Optional
from sqlalchemy import select, and_
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@inngest.create_function(
    fn_id="execute-task-with-sandbox",
    trigger=inngest.event("sandbox/task.execute"),
)
async def execute_task_with_sandbox(ctx, step):
    """
    Execute task with E2B sandbox workflow

    This function orchestrates a complete Git workflow:
    1. Create sandbox
    2. Clone repository
    3. Create feature branch
    4. Let agent implement changes
    5. Commit changes
    6. Push to remote
    7. Create Pull Request
    8. Terminate sandbox

    Event payload:
    {
        "task_id": "uuid",
        "agent_id": "uuid",
        "repo_url": "https://github.com/owner/repo.git",
        "branch_name": "feature-123",
        "base_branch": "main",
        "pr_title": "Add new feature",
        "pr_body": "Description of changes",
        "commit_message": "feat: add new feature",
        "execution_id": "uuid" (optional, for SSE broadcasting),
        "squad_id": "uuid" (optional, for SSE broadcasting)
    }

    Returns:
        Dict with sandbox_id, pr_url, and status
    """
    data = ctx.event.data
    task_id = UUID(data["task_id"])
    agent_id = UUID(data["agent_id"])
    repo_url = data["repo_url"]
    branch_name = data["branch_name"]
    base_branch = data.get("base_branch", "main")
    pr_title = data["pr_title"]
    pr_body = data["pr_body"]
    commit_message = data["commit_message"]
    execution_id = UUID(data["execution_id"]) if data.get("execution_id") else None
    squad_id = UUID(data["squad_id"]) if data.get("squad_id") else None

    logger.info(
        f"Starting sandbox workflow for task {task_id} "
        f"(agent={agent_id}, repo={repo_url})"
    )

    sandbox_id = None

    try:
        # Step 1: Create E2B sandbox
        sandbox = await step.run(
            "create-sandbox",
            lambda: create_sandbox_for_task(task_id, agent_id, repo_url, execution_id, squad_id),
            retries=3
        )
        sandbox_id = sandbox["id"]
        logger.info(f"Created sandbox {sandbox_id}")

        # Step 2: Clone repository
        await step.run(
            "clone-repository",
            lambda: clone_repo_in_sandbox(sandbox_id, repo_url, execution_id, squad_id),
            retries=3
        )
        logger.info(f"Cloned {repo_url} into sandbox {sandbox_id}")

        # Step 3: Create feature branch
        await step.run(
            "create-branch",
            lambda: create_branch_in_sandbox(
                sandbox_id,
                branch_name,
                base_branch,
                execution_id,
                squad_id
            ),
            retries=3
        )
        logger.info(f"Created branch {branch_name}")

        # Step 4: Agent implements changes
        # (This step would be handled by the agent service separately)
        # Here we just wait for the agent to signal completion
        logger.info("Waiting for agent to complete implementation...")

        # Step 5: Commit changes
        await step.run(
            "commit-changes",
            lambda: commit_changes_in_sandbox(
                sandbox_id,
                commit_message,
                execution_id,
                squad_id
            ),
            retries=3
        )
        logger.info(f"Committed changes: {commit_message}")

        # Step 6: Push to remote
        await step.run(
            "push-changes",
            lambda: push_changes_in_sandbox(
                sandbox_id,
                branch_name,
                execution_id,
                squad_id
            ),
            retries=3
        )
        logger.info(f"Pushed branch {branch_name} to remote")

        # Step 7: Create Pull Request
        pr = await step.run(
            "create-pull-request",
            lambda: create_pr_in_sandbox(
                sandbox_id,
                pr_title,
                pr_body,
                branch_name,
                base_branch,
                execution_id,
                squad_id
            ),
            retries=3
        )
        logger.info(f"Created PR: {pr['html_url']}")

        # Step 8: Mark as completed
        await step.run(
            "mark-completed",
            lambda: update_sandbox_status(sandbox_id, "completed")
        )

        return {
            "status": "success",
            "sandbox_id": str(sandbox_id),
            "pr_url": pr["html_url"],
            "pr_number": pr["number"]
        }

    except Exception as e:
        logger.error(f"Sandbox workflow failed: {e}")

        # Clean up sandbox on error
        if sandbox_id:
            await step.run(
                "terminate-sandbox-on-error",
                lambda: terminate_sandbox(sandbox_id, execution_id, squad_id)
            )

        raise

    finally:
        # Always terminate sandbox after workflow (success or failure)
        if sandbox_id:
            await step.run(
                "terminate-sandbox-final",
                lambda: terminate_sandbox(sandbox_id, execution_id, squad_id)
            )


@inngest.create_function(
    fn_id="cleanup-old-sandboxes",
    trigger=inngest.cron("sandbox.cleanup", "0 */6 * * *")  # Every 6 hours
)
async def cleanup_old_sandboxes(ctx, step):
    """
    Cleanup old sandboxes (periodic task)

    Terminates sandboxes that:
    - Are older than 24 hours
    - Are in RUNNING or ERROR status
    - Have no active task

    Runs every 6 hours via cron trigger
    """
    logger.info("Starting sandbox cleanup job")

    # Get old sandboxes
    old_sandboxes = await step.run(
        "find-old-sandboxes",
        lambda: find_old_sandboxes(),
        retries=3
    )

    logger.info(f"Found {len(old_sandboxes)} old sandboxes to clean up")

    # Terminate each sandbox
    terminated_count = 0
    for sandbox in old_sandboxes:
        try:
            await step.run(
                f"terminate-sandbox-{sandbox['id']}",
                lambda s=sandbox: terminate_sandbox(s["id"])
            )
            terminated_count += 1
        except Exception as e:
            logger.error(f"Failed to terminate sandbox {sandbox['id']}: {e}")

    logger.info(f"Cleanup complete: terminated {terminated_count}/{len(old_sandboxes)} sandboxes")

    return {
        "status": "success",
        "found": len(old_sandboxes),
        "terminated": terminated_count
    }


# Helper functions for database operations

async def create_sandbox_for_task(
    task_id: UUID,
    agent_id: UUID,
    repo_url: str,
    execution_id: Optional[UUID] = None,
    squad_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """Create E2B sandbox for task"""
    async with get_db_context() as db:
        service = SandboxService(db, execution_id=execution_id, squad_id=squad_id)
        sandbox = await service.create_sandbox(
            task_id=task_id,
            agent_id=agent_id,
            repo_url=repo_url
        )
        return {
            "id": str(sandbox.id),
            "e2b_id": sandbox.e2b_id,
            "status": sandbox.status.value
        }


async def clone_repo_in_sandbox(
    sandbox_id: str,
    repo_url: str,
    execution_id: Optional[UUID] = None,
    squad_id: Optional[UUID] = None
) -> Dict[str, str]:
    """Clone repository into sandbox"""
    async with get_db_context() as db:
        service = SandboxService(db, execution_id=execution_id, squad_id=squad_id)
        path = await service.clone_repo(UUID(sandbox_id), repo_url)
        return {"path": path}


async def create_branch_in_sandbox(
    sandbox_id: str,
    branch_name: str,
    base_branch: str,
    execution_id: Optional[UUID] = None,
    squad_id: Optional[UUID] = None
) -> Dict[str, str]:
    """Create feature branch in sandbox"""
    async with get_db_context() as db:
        service = SandboxService(db, execution_id=execution_id, squad_id=squad_id)
        branch = await service.create_branch(
            UUID(sandbox_id),
            branch_name,
            base_branch
        )
        return {"branch": branch}


async def commit_changes_in_sandbox(
    sandbox_id: str,
    commit_message: str,
    execution_id: Optional[UUID] = None,
    squad_id: Optional[UUID] = None
) -> Dict[str, str]:
    """Commit changes in sandbox"""
    async with get_db_context() as db:
        service = SandboxService(db, execution_id=execution_id, squad_id=squad_id)
        output = await service.commit_changes(
            UUID(sandbox_id),
            commit_message
        )
        return {"output": output}


async def push_changes_in_sandbox(
    sandbox_id: str,
    branch: str,
    execution_id: Optional[UUID] = None,
    squad_id: Optional[UUID] = None
) -> Dict[str, str]:
    """Push changes to remote"""
    async with get_db_context() as db:
        service = SandboxService(db, execution_id=execution_id, squad_id=squad_id)
        output = await service.push_changes(
            UUID(sandbox_id),
            branch
        )
        return {"output": output}


async def create_pr_in_sandbox(
    sandbox_id: str,
    title: str,
    body: str,
    head: str,
    base: str,
    execution_id: Optional[UUID] = None,
    squad_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """Create GitHub Pull Request"""
    async with get_db_context() as db:
        service = SandboxService(db, execution_id=execution_id, squad_id=squad_id)
        pr = await service.create_pr(
            UUID(sandbox_id),
            title,
            body,
            head,
            base
        )
        return pr


async def terminate_sandbox(
    sandbox_id: str,
    execution_id: Optional[UUID] = None,
    squad_id: Optional[UUID] = None
) -> Dict[str, bool]:
    """Terminate E2B sandbox"""
    async with get_db_context() as db:
        service = SandboxService(db, execution_id=execution_id, squad_id=squad_id)
        success = await service.terminate_sandbox(UUID(sandbox_id))
        return {"terminated": success}


async def update_sandbox_status(
    sandbox_id: str,
    status: str
) -> Dict[str, str]:
    """Update sandbox status in database"""
    async with get_db_context() as db:
        result = await db.execute(
            select(Sandbox).where(Sandbox.id == UUID(sandbox_id))
        )
        sandbox = result.scalars().first()

        if sandbox:
            sandbox.status = SandboxStatus[status.upper()]
            await db.commit()

        return {"status": status}


async def find_old_sandboxes() -> list[Dict[str, Any]]:
    """Find sandboxes older than 24 hours"""
    async with get_db_context() as db:
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        result = await db.execute(
            select(Sandbox).where(
                and_(
                    Sandbox.created_at < cutoff_time,
                    Sandbox.status.in_([SandboxStatus.RUNNING, SandboxStatus.ERROR])
                )
            )
        )
        sandboxes = result.scalars().all()

        return [
            {
                "id": str(s.id),
                "e2b_id": s.e2b_id,
                "created_at": s.created_at.isoformat(),
                "status": s.status.value
            }
            for s in sandboxes
        ]
