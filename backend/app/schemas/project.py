"""
Pydantic v2 schemas for projects and project members.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    tender_number: str | None = None
    deadline: date | None = None
    max_token_budget: int = 1_000_000


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    tender_number: str | None = None
    tender_pdf_path: str | None = None
    deadline: date | None = None
    status: str | None = None
    max_token_budget: int | None = None
    budget_alert_threshold: Decimal | None = None


class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    tender_number: str | None = None
    tender_pdf_path: str | None = None
    deadline: date | None = None
    status: str
    max_token_budget: int
    used_tokens: int
    budget_alert_threshold: Decimal
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectList(BaseModel):
    items: list[ProjectResponse]
    total: int


# ---------------------------------------------------------------------------
# Project Member
# ---------------------------------------------------------------------------

class ProjectMemberCreate(BaseModel):
    user_id: uuid.UUID
    project_role: str = "Reviewer"


class ProjectMemberResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    project_role: str
    joined_at: datetime
    # joined user info
    email: str | None = None
    full_name: str | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------

class BudgetResponse(BaseModel):
    max_token_budget: int
    used_tokens: int
    remaining: int
    usage_percent: float
    alert_threshold: float
