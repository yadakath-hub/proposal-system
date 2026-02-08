"""
ORM models for project requirements and section-requirement links.
"""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.sql import func

from app.db.session import Base


class ProjectRequirement(Base):
    __tablename__ = "project_requirements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )

    requirement_key = Column(String(50), nullable=False)  # REQ-001
    content = Column(Text, nullable=False)
    requirement_type = Column(String(50), default="other")
    source_text = Column(Text, nullable=True)
    source_page = Column(Integer, nullable=True)
    priority = Column(String(20), default="medium")
    keywords = Column(JSON, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


class SectionRequirementLink(Base):
    __tablename__ = "section_requirement_links"
    __table_args__ = (
        UniqueConstraint("section_id", "requirement_id", name="uq_section_requirement"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(
        UUID(as_uuid=True), ForeignKey("sections.id", ondelete="CASCADE"), nullable=False
    )
    requirement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("project_requirements.id", ondelete="CASCADE"),
        nullable=False,
    )

    relevance_score = Column(Integer, default=0)
    is_addressed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
