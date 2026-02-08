"""
Export API endpoints — generate DOCX/PDF, manage templates.
"""

import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.export import (
    ExportHistoryResponse,
    ExportRequest,
    ExportResponse,
    TemplateCreate,
    TemplateResponse,
    TemplateUpdate,
)
from app.services.auth_service import get_current_user
from app.services import export_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Export operations
# ---------------------------------------------------------------------------

@router.post("/", response_model=ExportResponse, status_code=201)
async def create_export(
    body: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await export_service.export_project(body, current_user.id, db)


@router.get("/{export_id}/status", response_model=ExportHistoryResponse)
async def get_export_status(
    export_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await export_service.get_export_status(export_id, db)


@router.get("/{export_id}/download")
async def download_export(
    export_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data, filename, fmt = await export_service.download_export(export_id, db)
    media_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    return Response(
        content=data,
        media_type=media_types.get(fmt, "application/octet-stream"),
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"
        },
    )


@router.get("/project/{project_id}", response_model=list[ExportHistoryResponse])
async def get_export_history(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await export_service.get_export_history(project_id, db)


@router.delete("/{export_id}", status_code=204)
async def delete_export(
    export_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await export_service.delete_export(export_id, db)


# ---------------------------------------------------------------------------
# Template management
# ---------------------------------------------------------------------------

@router.get("/templates/", response_model=list[TemplateResponse])
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    templates = await export_service.get_templates(db)
    return [TemplateResponse.model_validate(t) for t in templates]


@router.post("/templates/", response_model=TemplateResponse, status_code=201)
async def create_template(
    body: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tmpl = await export_service.create_template(
        name=body.name,
        template_type=body.template_type,
        file_path="",  # no file upload in this endpoint
        user_id=current_user.id,
        db=db,
        description=body.description,
        style_config=body.style_config,
    )
    return TemplateResponse.model_validate(tmpl)


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tmpl = await export_service.get_template(template_id, db)
    return TemplateResponse.model_validate(tmpl)


@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    body: TemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tmpl = await export_service.update_template(
        template_id, body.model_dump(exclude_unset=True), db
    )
    return TemplateResponse.model_validate(tmpl)


@router.delete("/templates/{template_id}", status_code=204)
async def delete_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await export_service.delete_template(template_id, db)
