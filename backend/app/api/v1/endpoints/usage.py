"""
Usage statistics API endpoints.
"""

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.usage_log import UsageLog
from app.models.user import User
from app.schemas.usage import (
    DailyUsage,
    ModelUsage,
    ProjectUsageResponse,
    UsageLogResponse,
    UsageStats,
)
from app.services.auth_service import get_current_user
from app.services import cost_service

router = APIRouter()


@router.get("/stats", response_model=UsageStats)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base = select(UsageLog)
    if current_user.role != "Admin":
        base = base.where(UsageLog.user_id == current_user.id)

    # Totals
    totals = await db.execute(
        select(
            func.count(UsageLog.id),
            func.coalesce(func.sum(UsageLog.input_tokens), 0),
            func.coalesce(func.sum(UsageLog.output_tokens), 0),
            func.coalesce(func.sum(UsageLog.cost_usd), Decimal(0)),
        ).where(
            *([UsageLog.user_id == current_user.id] if current_user.role != "Admin" else [])
        )
    )
    row = totals.one()
    total_requests, total_input, total_output, total_cost = row

    # By model
    model_q = (
        select(
            UsageLog.model_used,
            func.count(UsageLog.id).label("cnt"),
            func.coalesce(func.sum(UsageLog.input_tokens + UsageLog.output_tokens), 0).label("tokens"),
            func.coalesce(func.sum(UsageLog.cost_usd), Decimal(0)).label("cost"),
        )
        .group_by(UsageLog.model_used)
    )
    if current_user.role != "Admin":
        model_q = model_q.where(UsageLog.user_id == current_user.id)
    model_rows = (await db.execute(model_q)).all()

    return UsageStats(
        total_requests=total_requests,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        total_tokens=total_input + total_output,
        total_cost_usd=float(total_cost),
        by_model=[
            ModelUsage(model=r.model_used, request_count=r.cnt, total_tokens=r.tokens, total_cost=float(r.cost))
            for r in model_rows
        ],
    )


@router.get("/project/{project_id}", response_model=ProjectUsageResponse)
async def get_project_usage(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    usage = await cost_service.get_project_usage(project_id, db)
    budget = await cost_service.check_budget_alert(project_id, db)

    # Recent logs
    result = await db.execute(
        select(UsageLog)
        .where(UsageLog.project_id == project_id)
        .order_by(UsageLog.created_at.desc())
        .limit(50)
    )
    logs = [UsageLogResponse.model_validate(l) for l in result.scalars().all()]

    return ProjectUsageResponse(
        project_id=project_id,
        max_token_budget=budget.get("budget", 0),
        used_tokens=budget.get("used", 0),
        remaining_tokens=budget.get("remaining", 0),
        usage_percent=budget.get("usage_percent", 0),
        total_cost_usd=usage["total_cost_usd"],
        logs=logs,
    )


@router.get("/me", response_model=UsageStats)
async def get_my_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    totals = await db.execute(
        select(
            func.count(UsageLog.id),
            func.coalesce(func.sum(UsageLog.input_tokens), 0),
            func.coalesce(func.sum(UsageLog.output_tokens), 0),
            func.coalesce(func.sum(UsageLog.cost_usd), Decimal(0)),
        ).where(UsageLog.user_id == current_user.id)
    )
    row = totals.one()
    total_requests, total_input, total_output, total_cost = row

    return UsageStats(
        total_requests=total_requests,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        total_tokens=total_input + total_output,
        total_cost_usd=float(total_cost),
    )


@router.get("/daily", response_model=list[DailyUsage])
async def get_daily_usage(
    project_id: uuid.UUID | None = Query(None),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = None if current_user.role == "Admin" else current_user.id
    rows = await cost_service.get_daily_usage(db, project_id=project_id, user_id=user_id, days=days)
    return [DailyUsage(**r) for r in rows]
