"""
Cost calculation service — compute per-request cost, cache savings, budget checks.
"""

import uuid
from decimal import Decimal

from sqlalchemy import func, select, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_config import MODEL_CONFIG, estimate_cost as _estimate
from app.models.project import Project
from app.models.usage_log import UsageLog
from app.schemas.ai import CostEstimate


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int = 0,
) -> CostEstimate:
    raw = _estimate(model, input_tokens, output_tokens, cached_tokens)
    return CostEstimate(**raw)


def calculate_cache_savings(
    model: str,
    cached_tokens: int,
) -> float:
    pricing = MODEL_CONFIG.get(model)
    if pricing is None or cached_tokens <= 0:
        return 0.0
    full_cost = cached_tokens * pricing.input_per_million / 1_000_000
    cached_cost = cached_tokens * pricing.cached_per_million / 1_000_000
    return round(full_cost - cached_cost, 6)


async def get_project_usage(
    project_id: uuid.UUID, db: AsyncSession
) -> dict:
    result = await db.execute(
        select(
            func.count(UsageLog.id).label("total_requests"),
            func.coalesce(func.sum(UsageLog.input_tokens), 0).label("total_input"),
            func.coalesce(func.sum(UsageLog.output_tokens), 0).label("total_output"),
            func.coalesce(func.sum(UsageLog.cost_usd), Decimal(0)).label("total_cost"),
        ).where(UsageLog.project_id == project_id)
    )
    row = result.one()
    return {
        "total_requests": row.total_requests,
        "total_input_tokens": row.total_input,
        "total_output_tokens": row.total_output,
        "total_cost_usd": float(row.total_cost),
    }


async def check_budget_alert(
    project_id: uuid.UUID, db: AsyncSession
) -> dict:
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        return {"allowed": False, "error": "Project not found"}
    remaining = project.max_token_budget - project.used_tokens
    usage_pct = (
        round(float(project.used_tokens) / project.max_token_budget * 100, 2)
        if project.max_token_budget > 0 else 0.0
    )
    alert = usage_pct >= float(project.budget_alert_threshold) * 100
    return {
        "allowed": remaining > 0,
        "remaining": remaining,
        "used": project.used_tokens,
        "budget": project.max_token_budget,
        "usage_percent": usage_pct,
        "alert": alert,
    }


async def get_daily_usage(
    db: AsyncSession,
    project_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    days: int = 30,
) -> list[dict]:
    q = select(
        cast(UsageLog.created_at, Date).label("date"),
        func.count(UsageLog.id).label("request_count"),
        func.coalesce(func.sum(UsageLog.input_tokens + UsageLog.output_tokens), 0).label("total_tokens"),
        func.coalesce(func.sum(UsageLog.cost_usd), Decimal(0)).label("total_cost"),
    )
    if project_id:
        q = q.where(UsageLog.project_id == project_id)
    if user_id:
        q = q.where(UsageLog.user_id == user_id)
    q = q.group_by(cast(UsageLog.created_at, Date)).order_by(cast(UsageLog.created_at, Date).desc()).limit(days)

    result = await db.execute(q)
    return [
        {
            "date": str(row.date),
            "request_count": row.request_count,
            "total_tokens": row.total_tokens,
            "total_cost": float(row.total_cost),
        }
        for row in result.all()
    ]
