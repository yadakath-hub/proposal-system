"""
Pydantic schemas for section template library and AI recommendations.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class TemplateCategoryEnum(str, Enum):
    INTRODUCTION = "introduction"
    TECHNICAL = "technical"
    SOLUTION = "solution"
    MANAGEMENT = "management"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    QUALIFICATION = "qualification"
    EXPERIENCE = "experience"
    TEAM = "team"
    TIMELINE = "timeline"
    PRICING = "pricing"
    MAINTENANCE = "maintenance"
    TRAINING = "training"
    OTHER = "other"


class SectionTemplateCreate(BaseModel):
    name: str
    category: TemplateCategoryEnum
    description: str | None = None
    content: str
    tags: list[str] = []
    is_active: bool = True


class SectionTemplateUpdate(BaseModel):
    name: str | None = None
    category: TemplateCategoryEnum | None = None
    description: str | None = None
    content: str | None = None
    tags: list[str] | None = None
    is_active: bool | None = None


class TemplateRecommendRequest(BaseModel):
    section_id: uuid.UUID
    section_title: str
    section_type: str | None = None
    requirement_content: str | None = None
    project_context: str | None = None
    top_k: int = 3


class TemplateApplyRequest(BaseModel):
    template_id: uuid.UUID
    section_id: uuid.UUID
    mode: str = "replace"  # replace | append


class TemplateSearchRequest(BaseModel):
    query: str | None = None
    category: TemplateCategoryEnum | None = None
    tags: list[str] | None = None
    limit: int = 20
