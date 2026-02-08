"""
Section API endpoints — CRUD, tree, locking, versions.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
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
from app.services.auth_service import get_current_user
from app.services import section_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Section CRUD
# ---------------------------------------------------------------------------

@router.post("/", response_model=SectionResponse, status_code=201)
async def create_section(
    body: SectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await section_service.create_section(body, current_user, db)


@router.get("/tree/{project_id}", response_model=list[SectionTree])
async def get_sections_tree(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await section_service.get_sections_tree(project_id, db)


@router.get("/{section_id}", response_model=SectionResponse)
async def get_section(
    section_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await section_service.get_section(section_id, db)


@router.put("/{section_id}", response_model=SectionResponse)
async def update_section(
    section_id: uuid.UUID,
    body: SectionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await section_service.update_section(section_id, body, current_user, db)


@router.delete("/{section_id}", status_code=204)
async def delete_section(
    section_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await section_service.delete_section(section_id, current_user, db)


@router.put("/reorder", response_model=list[SectionResponse])
async def reorder_sections(
    body: ReorderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await section_service.reorder_sections(body, db)


# ---------------------------------------------------------------------------
# Locking
# ---------------------------------------------------------------------------

@router.post("/{section_id}/lock", response_model=SectionLockResponse)
async def acquire_lock(
    section_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await section_service.acquire_lock(section_id, current_user, db)


@router.delete("/{section_id}/lock", response_model=SectionLockResponse)
async def release_lock(
    section_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await section_service.release_lock(section_id, current_user, db)


# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------

@router.post("/{section_id}/versions", response_model=SectionVersionResponse, status_code=201)
async def create_version(
    section_id: uuid.UUID,
    body: SectionVersionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await section_service.create_version(section_id, body, current_user, db)


@router.get("/{section_id}/versions", response_model=list[SectionVersionResponse])
async def get_versions(
    section_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await section_service.get_versions(section_id, db)


@router.put("/{section_id}/current-version", response_model=SectionResponse)
async def set_current_version(
    section_id: uuid.UUID,
    body: SetCurrentVersionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await section_service.set_current_version(section_id, body, db)
