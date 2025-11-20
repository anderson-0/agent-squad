"""
Template API Endpoints

Endpoints for browsing and applying squad templates
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.services.template_service import TemplateService
from backend.schemas.template import (
    TemplateListResponse,
    TemplateDetailResponse,
    ApplyTemplateRequest,
    ApplyTemplateResponse,
    CreateTemplateRequest,
    UpdateTemplateRequest
)

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/", response_model=List[TemplateListResponse])
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category (development, support, sales, etc.)"),
    featured_only: bool = Query(False, description="Show only featured templates"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all available squad templates

    Returns templates ordered by popularity (usage count).
    Can be filtered by category or limited to featured templates only.

    **Example categories:**
    - development
    - support
    - sales
    - devops
    - content
    """
    templates = await TemplateService.list_templates(
        db=db,
        category=category,
        featured_only=featured_only
    )

    return [
        TemplateListResponse(
            id=t.id,
            name=t.name,
            slug=t.slug,
            description=t.description,
            category=t.category,
            is_featured=t.is_featured,
            usage_count=t.usage_count,
            avg_rating=t.avg_rating
        )
        for t in templates
    ]


@router.get("/{template_id}", response_model=TemplateDetailResponse)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a template

    Returns complete template definition including:
    - Agent definitions
    - Routing rules
    - Example conversations
    - Success metrics
    - Use cases and tags
    """
    template = await TemplateService.get_template(db, template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return TemplateDetailResponse(
        id=template.id,
        name=template.name,
        slug=template.slug,
        description=template.description,
        category=template.category,
        is_featured=template.is_featured,
        template_definition=template.template_definition,
        usage_count=template.usage_count,
        avg_rating=template.avg_rating,
        created_at=template.created_at,
        updated_at=template.updated_at
    )


@router.get("/by-slug/{slug}", response_model=TemplateDetailResponse)
async def get_template_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get template by slug

    Alternative to getting by UUID. Slugs are human-readable
    identifiers like 'software-dev-squad' or 'customer-support-squad'.
    """
    template = await TemplateService.get_template_by_slug(db, slug)

    if not template:
        raise HTTPException(status_code=404, detail=f"Template with slug '{slug}' not found")

    return TemplateDetailResponse(
        id=template.id,
        name=template.name,
        slug=template.slug,
        description=template.description,
        category=template.category,
        is_featured=template.is_featured,
        template_definition=template.template_definition,
        usage_count=template.usage_count,
        avg_rating=template.avg_rating,
        created_at=template.created_at,
        updated_at=template.updated_at
    )


@router.post("/{template_id}/apply", response_model=ApplyTemplateResponse)
async def apply_template(
    template_id: UUID,
    request: ApplyTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Apply a template to a squad

    Creates all agents and routing rules defined in the template.
    System prompts are automatically loaded from the roles/ directory.

    **What this does:**
    1. Creates all agents from template
    2. Sets up routing rules with escalation hierarchy
    3. Assigns appropriate LLM models to each agent
    4. Increments template usage count

    **Customization:**
    You can optionally override agents or routing rules by providing
    a customization object.

    **Example:**
    ```json
    {
      "squad_id": "...",
      "user_id": "...",
      "customization": {
        "agents": [
          {
            "role": "backend_developer",
            "llm_model": "gpt-4-turbo"  // Override default
          }
        ]
      }
    }
    ```
    """
    try:
        result = await TemplateService.apply_template(
            db=db,
            template_id=template_id,
            squad_id=request.squad_id,
            user_id=request.user_id,
            customization=request.customization
        )

        return ApplyTemplateResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply template: {str(e)}")


@router.post("/", response_model=TemplateDetailResponse, status_code=201)
async def create_template(
    request: CreateTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new squad template

    **Note:** This is an admin-level operation. In production,
    this endpoint should be protected with appropriate authentication
    and authorization.

    Templates should include:
    - Agent definitions with roles and LLM assignments
    - Routing rules for escalation
    - Example conversations (optional but recommended)
    - Success metrics (optional)
    """
    try:
        template = await TemplateService.create_template(
            db=db,
            name=request.name,
            slug=request.slug,
            description=request.description,
            category=request.category,
            template_definition=request.template_definition.dict(),
            is_featured=request.is_featured
        )

        return TemplateDetailResponse(
            id=template.id,
            name=template.name,
            slug=template.slug,
            description=template.description,
            category=template.category,
            is_featured=template.is_featured,
            template_definition=template.template_definition,
            usage_count=template.usage_count,
            avg_rating=template.avg_rating,
            created_at=template.created_at,
            updated_at=template.updated_at
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")


@router.patch("/{template_id}", response_model=TemplateDetailResponse)
async def update_template(
    template_id: UUID,
    request: UpdateTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a template

    **Note:** This is an admin-level operation.

    Only provided fields will be updated. Omitted fields remain unchanged.
    """
    updates = request.dict(exclude_unset=True)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    template = await TemplateService.update_template(db, template_id, updates)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return TemplateDetailResponse(
        id=template.id,
        name=template.name,
        slug=template.slug,
        description=template.description,
        category=template.category,
        is_featured=template.is_featured,
        template_definition=template.template_definition,
        usage_count=template.usage_count,
        avg_rating=template.avg_rating,
        created_at=template.created_at,
        updated_at=template.updated_at
    )


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a template (soft delete)

    **Note:** This is an admin-level operation.

    Templates are not actually deleted from the database,
    but marked as inactive (is_active = False).
    """
    deleted = await TemplateService.delete_template(db, template_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found")

    return None
