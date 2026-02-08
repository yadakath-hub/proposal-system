"""
Pydantic v2 schemas for document upload, parsing, and RAG search.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    is_parsed: bool
    parsed_at: datetime | None = None
    chunk_count: int = 0
    uploaded_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetail(DocumentResponse):
    content_text: str | None = None
    file_path: str


class SearchRequest(BaseModel):
    query: str
    project_id: uuid.UUID
    top_k: int = 5
    source_types: list[str] | None = None


class SearchResult(BaseModel):
    chunk_text: str
    score: float
    source_type: str
    source_id: uuid.UUID
    chunk_index: int
    metadata: dict | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int


class ProcessResponse(BaseModel):
    document_id: uuid.UUID
    status: str
    content_length: int = 0
    chunk_count: int = 0
    message: str = ""
