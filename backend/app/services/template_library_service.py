"""
Section template CRUD, search, and apply service.
"""

import math
import uuid
import logging
from datetime import datetime, timezone

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.section import Section, SectionVersion
from app.models.section_template import (
    SectionTemplate,
    TemplateUsageLog,
    TemplateVersion,
)
from app.schemas.section_template import SectionTemplateCreate, SectionTemplateUpdate

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Pure-Python cosine similarity (no numpy needed)."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


async def _generate_embedding(text: str) -> list[float] | None:
    """Generate an embedding vector, returning None on failure."""
    try:
        from app.services.embedding_service import embed_text
        return await embed_text(text)
    except Exception as e:
        logger.warning(f"Failed to generate embedding: {e}")
        return None


# ---------------------------------------------------------------------------
# Create / Update / Delete
# ---------------------------------------------------------------------------

async def create_template(
    db: AsyncSession,
    data: SectionTemplateCreate,
    user_id: uuid.UUID,
) -> SectionTemplate:
    word_count = len(data.content)
    embedding = await _generate_embedding(
        f"{data.name} {data.description or ''} {data.content[:1000]}"
    )

    template = SectionTemplate(
        name=data.name,
        category=data.category.value,
        description=data.description,
        content=data.content,
        tags=data.tags,
        word_count=word_count,
        embedding=embedding,
        is_active=data.is_active,
        created_by=user_id,
    )
    db.add(template)
    await db.flush()

    db.add(TemplateVersion(
        template_id=template.id,
        version=1,
        content=data.content,
        change_note="初始版本",
        created_by=user_id,
    ))

    await db.commit()
    await db.refresh(template)
    return template


async def update_template(
    db: AsyncSession,
    template_id: uuid.UUID,
    data: SectionTemplateUpdate,
    user_id: uuid.UUID,
    change_note: str | None = None,
) -> SectionTemplate:
    result = await db.execute(
        select(SectionTemplate).where(SectionTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise ValueError("範本不存在")

    content_changed = data.content is not None and data.content != template.content

    for key, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            if key == "category":
                value = value.value if hasattr(value, "value") else value
            setattr(template, key, value)

    if content_changed:
        template.word_count = len(data.content)
        template.version += 1
        template.embedding = await _generate_embedding(
            f"{template.name} {template.description or ''} {data.content[:1000]}"
        )
        db.add(TemplateVersion(
            template_id=template.id,
            version=template.version,
            content=data.content,
            change_note=change_note or "內容更新",
            created_by=user_id,
        ))

    template.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(template)
    return template


async def delete_template(
    db: AsyncSession, template_id: uuid.UUID
) -> None:
    result = await db.execute(
        select(SectionTemplate).where(SectionTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if template:
        template.is_active = False
        await db.commit()


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

async def get_template(
    db: AsyncSession, template_id: uuid.UUID
) -> SectionTemplate | None:
    result = await db.execute(
        select(SectionTemplate).where(SectionTemplate.id == template_id)
    )
    return result.scalar_one_or_none()


async def get_template_versions(
    db: AsyncSession, template_id: uuid.UUID
) -> list[TemplateVersion]:
    result = await db.execute(
        select(TemplateVersion)
        .where(TemplateVersion.template_id == template_id)
        .order_by(TemplateVersion.version.desc())
    )
    return list(result.scalars().all())


async def get_templates(
    db: AsyncSession,
    category: str | None = None,
    search: str | None = None,
    active_only: bool = True,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[SectionTemplate], int]:
    query = select(SectionTemplate)
    count_query = select(func.count(SectionTemplate.id))

    conditions = []
    if active_only:
        conditions.append(SectionTemplate.is_active == True)  # noqa: E712
    if category:
        conditions.append(SectionTemplate.category == category)
    if search:
        term = f"%{search}%"
        conditions.append(or_(
            SectionTemplate.name.ilike(term),
            SectionTemplate.description.ilike(term),
            SectionTemplate.content.ilike(term),
        ))

    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))

    query = (
        query.order_by(
            SectionTemplate.usage_count.desc(),
            SectionTemplate.updated_at.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(query)
    templates = list(result.scalars().all())
    total = (await db.execute(count_query)).scalar()

    return templates, total


async def get_category_stats(db: AsyncSession) -> dict:
    result = await db.execute(
        select(
            SectionTemplate.category,
            func.count(SectionTemplate.id).label("count"),
            func.sum(SectionTemplate.usage_count).label("total_usage"),
        )
        .where(SectionTemplate.is_active == True)  # noqa: E712
        .group_by(SectionTemplate.category)
    )
    stats = {}
    for row in result.all():
        stats[row.category] = {
            "count": row.count,
            "total_usage": row.total_usage or 0,
        }
    return stats


# ---------------------------------------------------------------------------
# Semantic search
# ---------------------------------------------------------------------------

async def search_similar(
    db: AsyncSession,
    query_text: str,
    category: str | None = None,
    top_k: int = 5,
) -> list[tuple[SectionTemplate, float]]:
    query_embedding = await _generate_embedding(query_text)
    if not query_embedding:
        return []

    templates, _ = await get_templates(
        db, category=category, active_only=True, limit=100
    )

    scored: list[tuple[SectionTemplate, float]] = []
    for t in templates:
        if t.embedding:
            sim = _cosine_similarity(query_embedding, t.embedding)
            scored.append((t, sim))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


# ---------------------------------------------------------------------------
# Apply template to section
# ---------------------------------------------------------------------------

SECTION_TYPE_TO_CATEGORY: dict[str, str] = {
    "introduction": "introduction",
    "summary": "introduction",
    "technical": "technical",
    "solution": "solution",
    "management": "management",
    "compliance": "compliance",
    "security": "security",
    "pricing": "pricing",
    "other": "other",
}


async def apply_template(
    db: AsyncSession,
    template_id: uuid.UUID,
    section_id: uuid.UUID,
    user_id: uuid.UUID,
    mode: str = "replace",
) -> str:
    """Apply template content to a section by creating a new SectionVersion."""
    template = await get_template(db, template_id)
    if not template:
        raise ValueError("範本不存在")

    section_result = await db.execute(
        select(Section).where(Section.id == section_id)
    )
    section = section_result.scalar_one_or_none()
    if not section:
        raise ValueError("章節不存在")

    # Determine new content
    if mode == "append" and section.current_version_id:
        ver_result = await db.execute(
            select(SectionVersion).where(
                SectionVersion.id == section.current_version_id
            )
        )
        current_ver = ver_result.scalar_one_or_none()
        existing = current_ver.content if current_ver else ""
        new_content = existing + "\n\n" + template.content
    else:
        new_content = template.content

    # Create new version
    next_num_result = await db.execute(
        select(func.coalesce(func.max(SectionVersion.version_number), 0) + 1)
        .where(SectionVersion.section_id == section_id)
    )
    next_num = next_num_result.scalar_one()

    version = SectionVersion(
        section_id=section_id,
        version_number=next_num,
        content=new_content,
        source_type="Human",
        created_by=user_id,
    )
    db.add(version)
    await db.flush()

    section.current_version_id = version.id

    # Update template stats
    template.usage_count += 1
    template.last_used_at = datetime.now(timezone.utc)

    # Log usage
    db.add(TemplateUsageLog(
        template_id=template_id,
        section_id=section_id,
        project_id=section.project_id,
        user_id=user_id,
        apply_mode=mode,
    ))

    await db.commit()
    return new_content
