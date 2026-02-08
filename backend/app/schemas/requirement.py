"""
Pydantic schemas for tender requirement analysis and section linking.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class RequirementType(str, Enum):
    FUNCTIONAL = "functional"
    TECHNICAL = "technical"
    SECURITY = "security"
    MANAGEMENT = "management"
    QUALIFICATION = "qualification"
    DELIVERABLE = "deliverable"
    TIMELINE = "timeline"
    OTHER = "other"


class ExtractedRequirement(BaseModel):
    """A single requirement extracted from a tender document."""
    id: str | None = None
    content: str
    requirement_type: RequirementType = RequirementType.OTHER
    source_text: str = ""
    source_page: int | None = None
    priority: str = "medium"
    suggested_section: str | None = None
    keywords: list[str] = []


class RequirementAnalysisRequest(BaseModel):
    project_id: uuid.UUID
    document_id: uuid.UUID
    auto_link: bool = True


class RequirementAnalysisResponse(BaseModel):
    success: bool
    project_id: uuid.UUID
    document_id: uuid.UUID | None = None
    total_requirements: int = 0
    requirements: list[ExtractedRequirement] = []
    summary: str | None = None
    key_points: list[str] = []
    message: str | None = None


class LinkRequirementRequest(BaseModel):
    section_id: uuid.UUID
    requirement_ids: list[uuid.UUID]


class RequirementSearchRequest(BaseModel):
    project_id: uuid.UUID
    query: str
    top_k: int = 5
