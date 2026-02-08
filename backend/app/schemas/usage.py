"""
Pydantic v2 schemas for usage statistics.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class UsageLogResponse(BaseModel):
    model_config = {"from_attributes": True, "protected_namespaces": ()}

    id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID | None = None
    section_id: uuid.UUID | None = None
    model_used: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    action_type: str
    created_at: datetime



class UsageStats(BaseModel):
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    cache_savings_usd: float = 0.0
    by_model: list[ModelUsage] = []
    by_level: list[LevelUsage] = []


class ModelUsage(BaseModel):
    model: str
    request_count: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0


class LevelUsage(BaseModel):
    level: str
    request_count: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0


class DailyUsage(BaseModel):
    date: str
    request_count: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0


class ProjectUsageResponse(BaseModel):
    project_id: uuid.UUID
    max_token_budget: int
    used_tokens: int
    remaining_tokens: int
    usage_percent: float
    total_cost_usd: float = 0.0
    logs: list[UsageLogResponse] = []


# Resolve forward references
UsageStats.model_rebuild()
