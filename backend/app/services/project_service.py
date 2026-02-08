"""
Project service — CRUD, member management, budget check.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.project import (
    BudgetResponse,
    ProjectCreate,
    ProjectMemberCreate,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_editor(user: User) -> None:
    if user.role not in ("Admin", "Editor"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "需要 Editor 以上權限")


async def _get_project_or_404(
    project_id: uuid.UUID, db: AsyncSession
) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "專案不存在")
    return project


async def _require_project_role(
    project_id: uuid.UUID,
    user: User,
    allowed_roles: list[str],
    db: AsyncSession,
) -> None:
    """Check the user has one of *allowed_roles* on the project."""
    if user.role == "Admin":
        return
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None or member.project_role not in allowed_roles:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "權限不足")


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------

async def create_project(
    data: ProjectCreate, user: User, db: AsyncSession
) -> ProjectResponse:
    _require_editor(user)
    project = Project(
        name=data.name,
        description=data.description,
        tender_number=data.tender_number,
        deadline=data.deadline,
        max_token_budget=data.max_token_budget,
        created_by=user.id,
    )
    db.add(project)
    await db.flush()

    # creator becomes Owner
    db.add(ProjectMember(
        project_id=project.id, user_id=user.id, project_role="Owner",
    ))
    await db.commit()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)


async def get_project(
    project_id: uuid.UUID, db: AsyncSession
) -> ProjectResponse:
    project = await _get_project_or_404(project_id, db)
    return ProjectResponse.model_validate(project)


async def get_projects(
    user: User, db: AsyncSession
) -> list[ProjectResponse]:
    if user.role == "Admin":
        result = await db.execute(
            select(Project).order_by(Project.created_at.desc())
        )
    else:
        result = await db.execute(
            select(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(ProjectMember.user_id == user.id)
            .order_by(Project.created_at.desc())
        )
    return [ProjectResponse.model_validate(p) for p in result.scalars().all()]


async def update_project(
    project_id: uuid.UUID, data: ProjectUpdate, user: User, db: AsyncSession
) -> ProjectResponse:
    await _require_project_role(project_id, user, ["Owner", "Manager"], db)
    project = await _get_project_or_404(project_id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)


async def delete_project(
    project_id: uuid.UUID, user: User, db: AsyncSession
) -> None:
    await _require_project_role(project_id, user, ["Owner"], db)
    project = await _get_project_or_404(project_id, db)
    await db.delete(project)
    await db.commit()


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------

async def add_member(
    project_id: uuid.UUID,
    data: ProjectMemberCreate,
    user: User,
    db: AsyncSession,
) -> ProjectMemberResponse:
    await _require_project_role(project_id, user, ["Owner", "Manager"], db)
    await _get_project_or_404(project_id, db)

    # check target user exists
    target = await db.execute(select(User).where(User.id == data.user_id))
    target_user = target.scalar_one_or_none()
    if target_user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "使用者不存在")

    # check not already a member
    existing = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == data.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "使用者已是專案成員")

    member = ProjectMember(
        project_id=project_id,
        user_id=data.user_id,
        project_role=data.project_role,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return ProjectMemberResponse(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        project_role=member.project_role,
        joined_at=member.joined_at,
        email=target_user.email,
        full_name=target_user.full_name,
    )


async def remove_member(
    project_id: uuid.UUID,
    target_user_id: uuid.UUID,
    user: User,
    db: AsyncSession,
) -> None:
    await _require_project_role(project_id, user, ["Owner", "Manager"], db)
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == target_user_id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "成員不存在")
    if member.project_role == "Owner":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "無法移除專案擁有者")
    await db.delete(member)
    await db.commit()


async def get_members(
    project_id: uuid.UUID, db: AsyncSession
) -> list[ProjectMemberResponse]:
    await _get_project_or_404(project_id, db)
    result = await db.execute(
        select(ProjectMember, User)
        .join(User, User.id == ProjectMember.user_id)
        .where(ProjectMember.project_id == project_id)
    )
    rows = result.all()
    return [
        ProjectMemberResponse(
            id=m.id,
            project_id=m.project_id,
            user_id=m.user_id,
            project_role=m.project_role,
            joined_at=m.joined_at,
            email=u.email,
            full_name=u.full_name,
        )
        for m, u in rows
    ]


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------

async def get_budget(
    project_id: uuid.UUID, db: AsyncSession
) -> BudgetResponse:
    project = await _get_project_or_404(project_id, db)
    remaining = project.max_token_budget - project.used_tokens
    usage_pct = (
        round(float(project.used_tokens) / project.max_token_budget * 100, 2)
        if project.max_token_budget > 0
        else 0.0
    )
    return BudgetResponse(
        max_token_budget=project.max_token_budget,
        used_tokens=project.used_tokens,
        remaining=remaining,
        usage_percent=usage_pct,
        alert_threshold=float(project.budget_alert_threshold),
    )
