"""
SQLAlchemy models for templates (export templates) and export_history.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Integer, BigInteger, String, Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Template(Base):
    """Maps to existing 'templates' table created in init_db.sql."""
    __tablename__ = "templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_type: Mapped[str] = mapped_column(
        Enum(
            "CoverPage", "TOC", "Chapter", "Appendix", "FullDoc", "Header", "Footer",
            name="template_type",
            create_type=False,
        ),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    preview_image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tag_schema: Mapped[list | None] = mapped_column(JSONB, server_default="[]")
    style_config: Mapped[dict | None] = mapped_column(JSONB, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ExportHistory(Base):
    __tablename__ = "export_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False, server_default="")
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_format: Mapped[str] = mapped_column(String(10), nullable=False, server_default="docx")
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    section_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("templates.id", ondelete="SET NULL"), nullable=True
    )
    include_toc: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    include_cover: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    export_time_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
