"""
Sandbox API Router
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID

from backend.core.database import get_db
from backend.services.sandbox_service import SandboxService
from backend.models.sandbox import SandboxStatus

router = APIRouter()

class SandboxCreate(BaseModel):
    agent_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    repo_url: Optional[str] = None

class SandboxResponse(BaseModel):
    id: UUID
    e2b_id: str
    status: str
    repo_url: Optional[str]
    agent_id: Optional[UUID]
    task_id: Optional[UUID]

    class Config:
        from_attributes = True

class GitCommitRequest(BaseModel):
    message: str
    repo_path: Optional[str] = None

class GitPushRequest(BaseModel):
    branch: str
    repo_path: Optional[str] = None

class PRRequest(BaseModel):
    title: str
    body: str
    head: str
    base: str = "main"
    repo_owner_name: Optional[str] = None

@router.post("/", response_model=SandboxResponse)
async def create_sandbox(
    request: SandboxCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new sandbox."""
    service = SandboxService(db)
    try:
        sandbox = await service.create_sandbox(
            agent_id=request.agent_id,
            task_id=request.task_id,
            repo_url=request.repo_url
        )
        return sandbox
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{sandbox_id}", response_model=SandboxResponse)
async def get_sandbox(
    sandbox_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get sandbox details."""
    service = SandboxService(db)
    sandbox = await service.get_sandbox(sandbox_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return sandbox

@router.delete("/{sandbox_id}")
async def terminate_sandbox(
    sandbox_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Terminate a sandbox."""
    service = SandboxService(db)
    success = await service.terminate_sandbox(sandbox_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return {"status": "terminated"}

@router.post("/{sandbox_id}/git/clone")
async def clone_repo(
    sandbox_id: UUID,
    repo_url: str,
    db: AsyncSession = Depends(get_db)
):
    """Clone a repository into the sandbox."""
    service = SandboxService(db)
    try:
        path = await service.clone_repo(sandbox_id, repo_url)
        return {"path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{sandbox_id}/git/commit")
async def commit_changes(
    sandbox_id: UUID,
    request: GitCommitRequest,
    db: AsyncSession = Depends(get_db)
):
    """Commit changes in the sandbox."""
    service = SandboxService(db)
    try:
        output = await service.commit_changes(
            sandbox_id, 
            request.message, 
            request.repo_path
        )
        return {"output": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{sandbox_id}/git/push")
async def push_changes(
    sandbox_id: UUID,
    request: GitPushRequest,
    db: AsyncSession = Depends(get_db)
):
    """Push changes to remote."""
    service = SandboxService(db)
    try:
        output = await service.push_changes(
            sandbox_id, 
            request.branch, 
            request.repo_path
        )
        return {"output": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{sandbox_id}/git/pr")
async def create_pr(
    sandbox_id: UUID,
    request: PRRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a Pull Request."""
    service = SandboxService(db)
    try:
        pr = await service.create_pr(
            sandbox_id,
            request.title,
            request.body,
            request.head,
            request.base,
            request.repo_owner_name
        )
        return pr
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Inngest Workflow Integration

class SandboxWorkflowRequest(BaseModel):
    task_id: UUID
    agent_id: UUID
    repo_url: str
    branch_name: str
    base_branch: str = "main"
    pr_title: str
    pr_body: str
    commit_message: str

@router.post("/workflows/execute")
async def execute_sandbox_workflow(
    request: SandboxWorkflowRequest
):
    """
    Execute complete sandbox workflow in background using Inngest.

    This endpoint triggers an Inngest workflow that:
    1. Creates E2B sandbox
    2. Clones repository
    3. Creates feature branch
    4. Commits changes (after agent completes work)
    5. Pushes to remote
    6. Creates Pull Request
    7. Terminates sandbox

    Returns immediately with workflow ID while execution happens in background.
    """
    try:
        from backend.core.inngest import inngest

        # Trigger Inngest workflow
        event_id = await inngest.send(
            event={
                "name": "sandbox/task.execute",
                "data": {
                    "task_id": str(request.task_id),
                    "agent_id": str(request.agent_id),
                    "repo_url": request.repo_url,
                    "branch_name": request.branch_name,
                    "base_branch": request.base_branch,
                    "pr_title": request.pr_title,
                    "pr_body": request.pr_body,
                    "commit_message": request.commit_message
                }
            }
        )

        return {
            "status": "workflow_started",
            "event_id": event_id,
            "message": "Sandbox workflow executing in background"
        }
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Inngest not available - install with: pip install inngest"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
