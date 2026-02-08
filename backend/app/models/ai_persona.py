"""
SQLAlchemy model for ai_personas table.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AiPersona(Base):
    __tablename__ = "ai_personas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    preferred_model: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="gpt-4o"
    )
    parameters: Mapped[dict | None] = mapped_column(JSONB, server_default="{}")
    default_max_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="4096"
    )
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
