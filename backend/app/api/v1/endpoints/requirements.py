"""
API endpoints for tender requirement analysis and section linking.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.schemas.requirement import (
    RequirementAnalysisRequest,
    RequirementAnalysisResponse,
    LinkRequirementRequest,
    RequirementSearchRequest,
)
from app.services import requirement_service

router = APIRouter()


@router.post("/analyze", response_model=RequirementAnalysisResponse)
async def analyze_requirements(
    request: RequirementAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze a tender document and extract requirements."""
    try:
        result = await requirement_service.analyze_and_save(
            db=db,
            project_id=request.project_id,
            document_id=request.document_id,
            user=current_user,
            auto_link=request.auto_link,
        )

        return RequirementAnalysisResponse(
            success=result["success"],
            project_id=request.project_id,
            document_id=request.document_id,
            total_requirements=result["total_requirements"],
            requirements=result["requirements"],
            summary=result["summary"],
            key_points=result["key_points"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_id}")
async def get_project_requirements(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all requirements for a project."""
    requirements = await requirement_service.get_project_requirements(db, project_id)
    return {
        "project_id": str(project_id),
        "total": len(requirements),
        "requirements": [
            {
                "id": str(r.id),
                "requirement_key": r.requirement_key,
                "content": r.content,
                "requirement_type": r.requirement_type,
                "source_text": r.source_text,
                "priority": r.priority,
                "keywords": r.keywords or [],
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in requirements
        ],
    }


@router.get("/section/{section_id}")
async def get_section_requirements(
    section_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get requirements linked to a section."""
    requirements = await requirement_service.get_section_requirements(db, section_id)
    return {
        "section_id": str(section_id),
        "total": len(requirements),
        "requirements": requirements,
    }


@router.post("/link")
async def link_requirements(
    request: LinkRequirementRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Link requirements to a section."""
    for req_id in request.requirement_ids:
        await requirement_service.link_requirement_to_section(
            db=db,
            section_id=request.section_id,
            requirement_id=req_id,
            user_id=current_user.id,
        )
    return {
        "success": True,
        "message": f"已關聯 {len(request.requirement_ids)} 個需求",
    }


@router.delete("/link/{link_id}")
async def unlink_requirement(
    link_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a section-requirement link."""
    await requirement_service.unlink_requirement(db, link_id)
    return {"success": True}


@router.patch("/link/{link_id}/addressed")
async def mark_requirement_addressed(
    link_id: uuid.UUID,
    is_addressed: bool,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle the 'addressed' flag on a link."""
    await requirement_service.mark_addressed(db, link_id, is_addressed)
    return {"success": True}


@router.post("/search")
async def search_requirements(
    request: RequirementSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Simple keyword search across project requirements."""
    all_reqs = await requirement_service.get_project_requirements(
        db, request.project_id
    )
    query_lower = request.query.lower()

    scored = []
    for r in all_reqs:
        score = 0
        text = f"{r.content} {r.source_text or ''} {' '.join(r.keywords or [])}"
        for word in query_lower.split():
            if word in text.lower():
                score += 1
        if score > 0:
            scored.append((score, r))

    scored.sort(key=lambda x: x[0], reverse=True)

    return {
        "results": [
            {
                "id": str(r.id),
                "requirement_key": r.requirement_key,
                "content": r.content,
                "requirement_type": r.requirement_type,
                "source_text": r.source_text,
                "priority": r.priority,
            }
            for _, r in scored[: request.top_k]
        ]
    }
