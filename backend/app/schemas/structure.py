"""
Pydantic schemas for AI-powered section structure parsing and import.
"""

from __future__ import annotations

import uuid
from enum import Enum

from pydantic import BaseModel


class ParseSourceType(str, Enum):
    IMAGE = "image"
    PDF = "pdf"
    TEXT = "text"


class ParsedSection(BaseModel):
    """A single section extracted by AI parsing."""
    chapter_number: str  # e.g. "1", "1.1", "2.3.1"
    title: str
    depth_level: int  # 0 = top level, 1 = sub-section, etc.
    parent_number: str | None = None
    description: str | None = None


class StructureParseRequest(BaseModel):
    """JSON-based parse request (for base64 images or text)."""
    project_id: uuid.UUID
    source_type: ParseSourceType
    content: str | None = None  # base64 image or text content


class StructureParseResponse(BaseModel):
    success: bool
    sections: list[ParsedSection] = []
    raw_text: str | None = None
    confidence: float = 0.0
    message: str | None = None


class StructureImportRequest(BaseModel):
    project_id: uuid.UUID
    sections: list[ParsedSection]
    clear_existing: bool = False


class StructureImportResponse(BaseModel):
    success: bool
    imported_count: int = 0
    section_ids: list[uuid.UUID] = []
    message: str | None = None
