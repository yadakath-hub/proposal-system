"""
Pydantic v2 schemas for document export and templates.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

class ExportRequest(BaseModel):
    project_id: uuid.UUID
    section_ids: list[uuid.UUID] | None = None
    format: str = "docx"  # docx or pdf
    template_id: uuid.UUID | None = None
    include_toc: bool = True
    include_cover: bool = True
    company_name: str = ""
    watermark: str | None = None


class ExportResponse(BaseModel):
    id: uuid.UUID
    success: bool
    file_name: str
    file_format: str
    file_size: int = 0
    page_count: int = 0
    section_count: int = 0
    export_time_ms: int = 0
    status: str = "completed"
    download_url: str = ""


class ExportHistoryResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    file_name: str
    file_format: str
    file_size: int
    page_count: int
    section_count: int
    status: str
    export_time_ms: int
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ExportProgress(BaseModel):
    export_id: uuid.UUID
    status: str
    current_section: int = 0
    total_sections: int = 0
    percentage: float = 0.0


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------

class TemplateCreate(BaseModel):
    name: str
    description: str | None = None
    template_type: str = "FullDoc"
    style_config: dict | None = None


class TemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    style_config: dict | None = None
    is_active: bool | None = None


class TemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    template_type: str
    file_path: str
    style_config: dict | None = None
    is_active: bool
    is_system: bool
    created_by: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
