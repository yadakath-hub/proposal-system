"""
Pydantic v2 schemas for sections, section versions, and locking.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Section
# ---------------------------------------------------------------------------

class SectionCreate(BaseModel):
    project_id: uuid.UUID
    parent_id: uuid.UUID | None = None
    chapter_number: str
    title: str
    requirement_text: str | None = None
    sort_order: int = 0
    depth_level: int = 0
    estimated_pages: int | None = 1
    assigned_to: uuid.UUID | None = None
    word_style_name: str | None = None
    docx_template_tag: str | None = None


class SectionUpdate(BaseModel):
    title: str | None = None
    chapter_number: str | None = None
    requirement_text: str | None = None
    sort_order: int | None = None
    depth_level: int | None = None
    estimated_pages: int | None = None
    assigned_to: uuid.UUID | None = None
    status: str | None = None
    word_style_name: str | None = None
    docx_template_tag: str | None = None


class SectionResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    parent_id: uuid.UUID | None = None
    chapter_number: str
    title: str
    requirement_text: str | None = None
    sort_order: int
    depth_level: int
    estimated_pages: int | None = None
    assigned_to: uuid.UUID | None = None
    status: str
    word_style_name: str | None = None
    docx_template_tag: str | None = None
    current_version_id: uuid.UUID | None = None
    locked_by: uuid.UUID | None = None
    locked_at: datetime | None = None
    lock_expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SectionTree(SectionResponse):
    children: list[SectionTree] = []


class ReorderItem(BaseModel):
    id: uuid.UUID
    sort_order: int


class ReorderRequest(BaseModel):
    items: list[ReorderItem]


# ---------------------------------------------------------------------------
# Section Version
# ---------------------------------------------------------------------------

class SectionVersionCreate(BaseModel):
    content: str
    content_html: str | None = None
    source_type: str = "Human"
    persona_id: uuid.UUID | None = None
    prompt_used: str | None = None
    generation_params: dict | None = None
    is_final: bool = False


class SectionVersionResponse(BaseModel):
    id: uuid.UUID
    section_id: uuid.UUID
    version_number: int
    content: str
    content_html: str | None = None
    source_type: str
    created_by: uuid.UUID
    persona_id: uuid.UUID | None = None
    prompt_used: str | None = None
    is_final: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Lock
# ---------------------------------------------------------------------------

class SectionLockResponse(BaseModel):
    section_id: uuid.UUID
    locked_by: uuid.UUID | None = None
    locked_at: datetime | None = None
    lock_expires_at: datetime | None = None
    locked: bool


class SetCurrentVersionRequest(BaseModel):
    version_id: uuid.UUID
