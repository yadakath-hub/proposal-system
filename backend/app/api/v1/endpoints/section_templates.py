"""
API endpoints for section template library management and AI recommendations.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.schemas.section_template import (
    SectionTemplateCreate,
    SectionTemplateUpdate,
    TemplateCategoryEnum,
    TemplateApplyRequest,
    TemplateRecommendRequest,
)
from app.services import template_library_service
from app.services import template_recommender_service

router = APIRouter()


@router.post("")
async def create_template(
    data: SectionTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new section template."""
    template = await template_library_service.create_template(
        db, data, current_user.id
    )
    return _template_to_dict(template)


@router.get("")
async def list_templates(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    active_only: bool = Query(True),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List templates with optional filters."""
    templates, total = await template_library_service.get_templates(
        db,
        category=category,
        search=search,
        active_only=active_only,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [_template_summary(t) for t in templates],
        "total": total,
    }


@router.get("/categories")
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get category list with counts."""
    stats = await template_library_service.get_category_stats(db)

    LABELS = {
        TemplateCategoryEnum.INTRODUCTION: "公司簡介/專案說明",
        TemplateCategoryEnum.TECHNICAL: "技術規劃",
        TemplateCategoryEnum.SOLUTION: "解決方案",
        TemplateCategoryEnum.MANAGEMENT: "專案管理",
        TemplateCategoryEnum.SECURITY: "資安規劃",
        TemplateCategoryEnum.COMPLIANCE: "法規合規",
        TemplateCategoryEnum.QUALIFICATION: "廠商資格",
        TemplateCategoryEnum.EXPERIENCE: "專案實績",
        TemplateCategoryEnum.TEAM: "團隊組織",
        TemplateCategoryEnum.TIMELINE: "時程規劃",
        TemplateCategoryEnum.PRICING: "報價說明",
        TemplateCategoryEnum.MAINTENANCE: "維護服務",
        TemplateCategoryEnum.TRAINING: "教育訓練",
        TemplateCategoryEnum.OTHER: "其他",
    }

    categories = [
        {
            "value": cat.value,
            "label": label,
            **stats.get(cat.value, {"count": 0, "total_usage": 0}),
        }
        for cat, label in LABELS.items()
    ]
    return {"categories": categories}


@router.get("/{template_id}")
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single template with versions."""
    template = await template_library_service.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="範本不存在")

    versions = await template_library_service.get_template_versions(
        db, template_id
    )

    result = _template_to_dict(template)
    result["versions"] = [
        {
            "version": v.version,
            "change_note": v.change_note,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]
    return result


@router.put("/{template_id}")
async def update_template(
    template_id: uuid.UUID,
    data: SectionTemplateUpdate,
    change_note: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a template."""
    try:
        template = await template_library_service.update_template(
            db, template_id, data, current_user.id, change_note
        )
        return {
            "success": True,
            "template_id": str(template.id),
            "version": template.version,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{template_id}")
async def delete_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a template."""
    await template_library_service.delete_template(db, template_id)
    return {"success": True}


@router.get("/{template_id}/versions")
async def get_template_versions(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get version history for a template."""
    versions = await template_library_service.get_template_versions(
        db, template_id
    )
    return {
        "template_id": str(template_id),
        "versions": [
            {
                "id": str(v.id),
                "version": v.version,
                "content": v.content,
                "change_note": v.change_note,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in versions
        ],
    }


@router.post("/recommend")
async def recommend_templates(
    request: TemplateRecommendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI-powered template recommendation."""
    result = await template_recommender_service.recommend_templates(
        db=db,
        section_id=request.section_id,
        section_title=request.section_title,
        section_type=request.section_type,
        requirement_content=request.requirement_content,
        project_context=request.project_context,
        top_k=request.top_k,
    )
    return result


@router.post("/apply")
async def apply_template(
    request: TemplateApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Apply a template to a section."""
    try:
        new_content = await template_library_service.apply_template(
            db=db,
            template_id=request.template_id,
            section_id=request.section_id,
            user_id=current_user.id,
            mode=request.mode,
        )
        return {"success": True, "content": new_content}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _template_to_dict(t) -> dict:
    return {
        "id": str(t.id),
        "name": t.name,
        "category": t.category,
        "description": t.description,
        "content": t.content,
        "word_count": t.word_count,
        "version": t.version,
        "usage_count": t.usage_count,
        "tags": t.tags or [],
        "is_active": t.is_active,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _template_summary(t) -> dict:
    return {
        "id": str(t.id),
        "name": t.name,
        "category": t.category,
        "description": t.description,
        "word_count": t.word_count,
        "version": t.version,
        "usage_count": t.usage_count,
        "tags": t.tags or [],
        "is_active": t.is_active,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }
