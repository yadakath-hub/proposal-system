"""
Export service — assemble sections into DOCX/PDF, upload to MinIO.
"""

import io
import time
import uuid

from fastapi import HTTPException, status
from minio import Minio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.export_template import ExportHistory, Template
from app.models.project import Project
from app.models.section import Section, SectionVersion
from app.schemas.export import (
    ExportHistoryResponse,
    ExportRequest,
    ExportResponse,
)
from app.services.docx_builder import DocxBuilder
from app.services import pdf_converter


def _get_minio() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


# ---------------------------------------------------------------------------
# Export project
# ---------------------------------------------------------------------------

async def export_project(
    request: ExportRequest,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> ExportResponse:
    start = time.monotonic()

    # Get project
    result = await db.execute(select(Project).where(Project.id == request.project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "專案不存在")

    # Get sections
    q = (
        select(Section)
        .where(Section.project_id == request.project_id)
        .order_by(Section.sort_order)
    )
    if request.section_ids:
        q = q.where(Section.id.in_(request.section_ids))
    result = await db.execute(q)
    sections = result.scalars().all()

    if not sections:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "沒有可匯出的章節")

    # Load template style_config if specified
    style_config = None
    if request.template_id:
        tmpl_result = await db.execute(
            select(Template).where(Template.id == request.template_id)
        )
        tmpl = tmpl_result.scalar_one_or_none()
        if tmpl and tmpl.style_config:
            style_config = tmpl.style_config

    # Build DOCX
    builder = DocxBuilder(style_config=style_config)

    # Cover page
    if request.include_cover:
        builder.add_cover_page(
            project_name=project.name,
            company_name=request.company_name,
            tender_number=project.tender_number or "",
        )

    # TOC
    if request.include_toc:
        builder.add_table_of_contents()

    # Header / Footer
    builder.set_header(project.name)
    builder.set_footer(include_page_number=True)

    # Sections
    for section in sections:
        content = ""
        # Try to get current version content
        if section.current_version_id:
            ver_result = await db.execute(
                select(SectionVersion).where(
                    SectionVersion.id == section.current_version_id
                )
            )
            version = ver_result.scalar_one_or_none()
            if version:
                content = version.content or ""

        level = section.depth_level + 1  # depth_level 0 → heading 1
        builder.add_section(
            title=f"{section.chapter_number} {section.title}",
            content=content,
            level=level,
        )

    docx_bytes = builder.save_to_bytes()

    # Convert to PDF if requested
    final_bytes = docx_bytes
    file_format = "docx"
    page_count = builder.get_page_count()

    if request.format == "pdf":
        pdf_bytes = await pdf_converter.docx_to_pdf(docx_bytes)
        if pdf_bytes:
            if request.watermark:
                pdf_bytes = pdf_converter.add_watermark(pdf_bytes, request.watermark)
            final_bytes = pdf_bytes
            file_format = "pdf"
            page_count = pdf_converter.get_pdf_page_count(pdf_bytes)
        else:
            # LibreOffice not available, fall back to DOCX
            file_format = "docx"

    # Upload to MinIO
    ext = file_format
    file_name = f"{project.name}_建議書.{ext}"
    object_name = f"exports/{request.project_id}/{uuid.uuid4()}/{file_name}"

    client = _get_minio()
    client.put_object(
        bucket_name=settings.BUCKET_EXPORTS,
        object_name=object_name,
        data=io.BytesIO(final_bytes),
        length=len(final_bytes),
        content_type="application/pdf" if ext == "pdf" else (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
    )

    elapsed_ms = int((time.monotonic() - start) * 1000)

    # Save export history
    history = ExportHistory(
        project_id=request.project_id,
        file_path=object_name,
        file_name=file_name,
        file_format=file_format,
        file_size=len(final_bytes),
        page_count=page_count,
        section_count=len(sections),
        template_id=request.template_id,
        include_toc=request.include_toc,
        include_cover=request.include_cover,
        status="completed",
        export_time_ms=elapsed_ms,
        created_by=user_id,
    )
    db.add(history)
    await db.commit()
    await db.refresh(history)

    return ExportResponse(
        id=history.id,
        success=True,
        file_name=file_name,
        file_format=file_format,
        file_size=len(final_bytes),
        page_count=page_count,
        section_count=len(sections),
        export_time_ms=elapsed_ms,
        status="completed",
    )


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

async def download_export(
    export_id: uuid.UUID, db: AsyncSession
) -> tuple[bytes, str, str]:
    result = await db.execute(
        select(ExportHistory).where(ExportHistory.id == export_id)
    )
    history = result.scalar_one_or_none()
    if history is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "匯出記錄不存在")

    client = _get_minio()
    response = client.get_object(settings.BUCKET_EXPORTS, history.file_path)
    data = response.read()
    response.close()
    response.release_conn()
    return data, history.file_name, history.file_format


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

async def get_export_history(
    project_id: uuid.UUID, db: AsyncSession
) -> list[ExportHistoryResponse]:
    result = await db.execute(
        select(ExportHistory)
        .where(ExportHistory.project_id == project_id)
        .order_by(ExportHistory.created_at.desc())
    )
    return [ExportHistoryResponse.model_validate(h) for h in result.scalars().all()]


async def delete_export(
    export_id: uuid.UUID, db: AsyncSession
) -> None:
    result = await db.execute(
        select(ExportHistory).where(ExportHistory.id == export_id)
    )
    history = result.scalar_one_or_none()
    if history is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "匯出記錄不存在")

    # Remove from MinIO
    try:
        client = _get_minio()
        client.remove_object(settings.BUCKET_EXPORTS, history.file_path)
    except Exception:
        pass

    await db.delete(history)
    await db.commit()


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

async def get_export_status(
    export_id: uuid.UUID, db: AsyncSession
) -> ExportHistoryResponse:
    result = await db.execute(
        select(ExportHistory).where(ExportHistory.id == export_id)
    )
    history = result.scalar_one_or_none()
    if history is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "匯出記錄不存在")
    return ExportHistoryResponse.model_validate(history)


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

async def get_templates(db: AsyncSession) -> list:
    result = await db.execute(
        select(Template)
        .where(Template.is_active == True)
        .order_by(Template.is_system.desc(), Template.name)
    )
    return result.scalars().all()


async def get_template(template_id: uuid.UUID, db: AsyncSession) -> Template:
    result = await db.execute(select(Template).where(Template.id == template_id))
    tmpl = result.scalar_one_or_none()
    if tmpl is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "範本不存在")
    return tmpl


async def create_template(
    name: str,
    template_type: str,
    file_path: str,
    user_id: uuid.UUID,
    db: AsyncSession,
    description: str | None = None,
    style_config: dict | None = None,
) -> Template:
    tmpl = Template(
        name=name,
        description=description,
        template_type=template_type,
        file_path=file_path,
        style_config=style_config or {},
        created_by=user_id,
    )
    db.add(tmpl)
    await db.commit()
    await db.refresh(tmpl)
    return tmpl


async def update_template(
    template_id: uuid.UUID,
    data: dict,
    db: AsyncSession,
) -> Template:
    tmpl = await get_template(template_id, db)
    for field, value in data.items():
        if value is not None:
            setattr(tmpl, field, value)
    await db.commit()
    await db.refresh(tmpl)
    return tmpl


async def delete_template(
    template_id: uuid.UUID, db: AsyncSession
) -> None:
    tmpl = await get_template(template_id, db)
    if tmpl.is_system:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "系統範本無法刪除")
    await db.delete(tmpl)
    await db.commit()
