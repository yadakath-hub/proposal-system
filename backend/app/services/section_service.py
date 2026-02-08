"""
Section service — CRUD, tree query, locking, version management.
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.section import Section, SectionVersion
from app.models.user import User
from app.schemas.section import (
    ReorderRequest,
    SectionCreate,
    SectionLockResponse,
    SectionResponse,
    SectionTree,
    SectionUpdate,
    SectionVersionCreate,
    SectionVersionResponse,
    SetCurrentVersionRequest,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_section_or_404(
    section_id: uuid.UUID, db: AsyncSession
) -> Section:
    result = await db.execute(select(Section).where(Section.id == section_id))
    section = result.scalar_one_or_none()
    if section is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "章節不存在")
    return section


def _is_lock_active(section: Section) -> bool:
    if section.locked_by is None or section.lock_expires_at is None:
        return False
    return section.lock_expires_at > datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Section CRUD
# ---------------------------------------------------------------------------

async def create_section(
    data: SectionCreate, user: User, db: AsyncSession
) -> SectionResponse:
    section = Section(
        project_id=data.project_id,
        parent_id=data.parent_id,
        chapter_number=data.chapter_number,
        title=data.title,
        requirement_text=data.requirement_text,
        sort_order=data.sort_order,
        depth_level=data.depth_level,
        estimated_pages=data.estimated_pages,
        assigned_to=data.assigned_to,
        word_style_name=data.word_style_name,
        docx_template_tag=data.docx_template_tag,
    )
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return SectionResponse.model_validate(section)


async def get_section(
    section_id: uuid.UUID, db: AsyncSession
) -> SectionResponse:
    section = await _get_section_or_404(section_id, db)
    return SectionResponse.model_validate(section)


async def get_sections_tree(
    project_id: uuid.UUID, db: AsyncSession
) -> list[SectionTree]:
    result = await db.execute(
        select(Section)
        .where(Section.project_id == project_id)
        .order_by(Section.sort_order)
    )
    sections = result.scalars().all()

    # Build tree in Python
    nodes: dict[uuid.UUID, SectionTree] = {}
    for s in sections:
        nodes[s.id] = SectionTree.model_validate(s)

    roots: list[SectionTree] = []
    for s in sections:
        node = nodes[s.id]
        if s.parent_id and s.parent_id in nodes:
            nodes[s.parent_id].children.append(node)
        else:
            roots.append(node)
    return roots


async def update_section(
    section_id: uuid.UUID, data: SectionUpdate, user: User, db: AsyncSession
) -> SectionResponse:
    section = await _get_section_or_404(section_id, db)

    # If locked by someone else, reject
    if _is_lock_active(section) and section.locked_by != user.id:
        raise HTTPException(status.HTTP_423_LOCKED, "章節已被其他使用者鎖定")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(section, field, value)
    await db.commit()
    await db.refresh(section)
    return SectionResponse.model_validate(section)


async def delete_section(
    section_id: uuid.UUID, user: User, db: AsyncSession
) -> None:
    section = await _get_section_or_404(section_id, db)
    if _is_lock_active(section) and section.locked_by != user.id:
        raise HTTPException(status.HTTP_423_LOCKED, "章節已被其他使用者鎖定")
    await db.delete(section)
    await db.commit()


async def reorder_sections(
    data: ReorderRequest, db: AsyncSession
) -> list[SectionResponse]:
    results = []
    for item in data.items:
        section = await _get_section_or_404(item.id, db)
        section.sort_order = item.sort_order
        results.append(section)
    await db.commit()
    for s in results:
        await db.refresh(s)
    return [SectionResponse.model_validate(s) for s in results]


# ---------------------------------------------------------------------------
# Locking
# ---------------------------------------------------------------------------

async def acquire_lock(
    section_id: uuid.UUID, user: User, db: AsyncSession
) -> SectionLockResponse:
    section = await _get_section_or_404(section_id, db)

    if _is_lock_active(section) and section.locked_by != user.id:
        raise HTTPException(status.HTTP_423_LOCKED, "章節已被其他使用者鎖定")

    now = datetime.now(timezone.utc)
    section.locked_by = user.id
    section.locked_at = now
    section.lock_expires_at = now + timedelta(
        minutes=settings.SECTION_LOCK_TIMEOUT_MINUTES
    )
    await db.commit()
    await db.refresh(section)
    return SectionLockResponse(
        section_id=section.id,
        locked_by=section.locked_by,
        locked_at=section.locked_at,
        lock_expires_at=section.lock_expires_at,
        locked=True,
    )


async def release_lock(
    section_id: uuid.UUID, user: User, db: AsyncSession
) -> SectionLockResponse:
    section = await _get_section_or_404(section_id, db)

    if _is_lock_active(section) and section.locked_by != user.id:
        if user.role != "Admin":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "只有鎖定者或管理員可以解鎖")

    section.locked_by = None
    section.locked_at = None
    section.lock_expires_at = None
    await db.commit()
    await db.refresh(section)
    return SectionLockResponse(
        section_id=section.id,
        locked_by=None,
        locked_at=None,
        lock_expires_at=None,
        locked=False,
    )


# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------

async def create_version(
    section_id: uuid.UUID,
    data: SectionVersionCreate,
    user: User,
    db: AsyncSession,
) -> SectionVersionResponse:
    section = await _get_section_or_404(section_id, db)

    # Get next version number
    result = await db.execute(
        select(func.coalesce(func.max(SectionVersion.version_number), 0) + 1)
        .where(SectionVersion.section_id == section_id)
    )
    next_num = result.scalar_one()

    version = SectionVersion(
        section_id=section_id,
        version_number=next_num,
        content=data.content,
        content_html=data.content_html,
        source_type=data.source_type,
        created_by=user.id,
        persona_id=data.persona_id,
        prompt_used=data.prompt_used,
        generation_params=data.generation_params or {},
        is_final=data.is_final,
    )
    db.add(version)

    # Auto-set as current version
    section.current_version_id = version.id
    await db.commit()
    await db.refresh(version)
    return SectionVersionResponse.model_validate(version)


async def get_versions(
    section_id: uuid.UUID, db: AsyncSession
) -> list[SectionVersionResponse]:
    await _get_section_or_404(section_id, db)
    result = await db.execute(
        select(SectionVersion)
        .where(SectionVersion.section_id == section_id)
        .order_by(SectionVersion.version_number.desc())
    )
    return [SectionVersionResponse.model_validate(v) for v in result.scalars().all()]


async def set_current_version(
    section_id: uuid.UUID,
    data: SetCurrentVersionRequest,
    db: AsyncSession,
) -> SectionResponse:
    section = await _get_section_or_404(section_id, db)

    # Verify version exists and belongs to section
    result = await db.execute(
        select(SectionVersion).where(
            SectionVersion.id == data.version_id,
            SectionVersion.section_id == section_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "版本不存在")

    section.current_version_id = data.version_id
    await db.commit()
    await db.refresh(section)
    return SectionResponse.model_validate(section)
