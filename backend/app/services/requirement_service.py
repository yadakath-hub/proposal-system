"""
Requirement CRUD and section-linking service.
"""

import uuid
import logging

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.requirement import ProjectRequirement, SectionRequirementLink
from app.models.section import Section
from app.models.user import User
from app.schemas.requirement import ExtractedRequirement
from app.services import document_service, parser_service
from app.services import requirement_analyzer_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Analyze + save
# ---------------------------------------------------------------------------

async def analyze_and_save(
    db: AsyncSession,
    project_id: uuid.UUID,
    document_id: uuid.UUID,
    user: User,
    auto_link: bool = True,
) -> dict:
    """Download document, run AI analysis, persist requirements."""

    # 1. Get document record
    doc = await db.execute(select(Document).where(Document.id == document_id))
    doc = doc.scalar_one_or_none()
    if doc is None:
        raise ValueError("文件不存在")

    # 2. Get parsed text (prefer cached; otherwise download + parse)
    if doc.content_text and doc.is_parsed:
        text = doc.content_text
    else:
        data, _, file_type = await document_service.download_document(
            document_id, db
        )
        text = parser_service.parse_file(data, file_type)

    if not text or len(text.strip()) < 50:
        raise ValueError("文件內容太少，無法分析需求")

    # 3. Gather existing sections for auto-link
    existing_sections: list[dict] = []
    if auto_link:
        result = await db.execute(
            select(Section)
            .where(Section.project_id == project_id)
            .order_by(Section.sort_order)
        )
        existing_sections = [
            {
                "id": s.id,
                "chapter_number": s.chapter_number,
                "title": s.title,
            }
            for s in result.scalars().all()
        ]

    # 4. AI analysis
    requirements, summary, key_points = (
        await requirement_analyzer_service.analyze_document(text, existing_sections)
    )

    # 5. Persist requirements
    saved: list[ProjectRequirement] = []
    for req in requirements:
        db_req = ProjectRequirement(
            project_id=project_id,
            document_id=document_id,
            requirement_key=req.id or f"REQ-{len(saved)+1:03d}",
            content=req.content,
            requirement_type=req.requirement_type.value,
            source_text=req.source_text,
            source_page=req.source_page,
            priority=req.priority,
            keywords=req.keywords,
        )
        db.add(db_req)
        await db.flush()

        # 6. Auto-link to section
        if auto_link and req.suggested_section:
            section_id = _find_section_id(req.suggested_section, existing_sections)
            if section_id:
                db.add(
                    SectionRequirementLink(
                        section_id=section_id,
                        requirement_id=db_req.id,
                        relevance_score=80,
                        created_by=user.id,
                    )
                )

        saved.append(db_req)

    await db.commit()

    return {
        "success": True,
        "total_requirements": len(saved),
        "requirements": requirements,
        "summary": summary,
        "key_points": key_points,
    }


def _find_section_id(
    suggested: str, sections: list[dict]
) -> uuid.UUID | None:
    """Resolve a suggestion string to a section UUID."""
    for s in sections:
        if s["chapter_number"] == suggested:
            return s["id"]
    # Fuzzy: title contains suggestion
    for s in sections:
        if suggested.lower() in s["title"].lower():
            return s["id"]
    return None


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

async def get_project_requirements(
    db: AsyncSession, project_id: uuid.UUID
) -> list[ProjectRequirement]:
    result = await db.execute(
        select(ProjectRequirement)
        .where(ProjectRequirement.project_id == project_id)
        .order_by(ProjectRequirement.requirement_key)
    )
    return list(result.scalars().all())


async def get_section_requirements(
    db: AsyncSession, section_id: uuid.UUID
) -> list[dict]:
    """Return linked requirements for a section (with join)."""
    result = await db.execute(
        select(SectionRequirementLink, ProjectRequirement)
        .join(
            ProjectRequirement,
            SectionRequirementLink.requirement_id == ProjectRequirement.id,
        )
        .where(SectionRequirementLink.section_id == section_id)
        .order_by(SectionRequirementLink.relevance_score.desc())
    )
    rows = result.all()

    return [
        {
            "link_id": str(link.id),
            "requirement_id": str(req.id),
            "requirement_key": req.requirement_key,
            "content": req.content,
            "requirement_type": req.requirement_type,
            "source_text": req.source_text,
            "priority": req.priority,
            "relevance_score": link.relevance_score,
            "is_addressed": link.is_addressed,
        }
        for link, req in rows
    ]


# ---------------------------------------------------------------------------
# Link / unlink
# ---------------------------------------------------------------------------

async def link_requirement_to_section(
    db: AsyncSession,
    section_id: uuid.UUID,
    requirement_id: uuid.UUID,
    user_id: uuid.UUID,
    relevance_score: int = 100,
) -> None:
    existing = await db.execute(
        select(SectionRequirementLink).where(
            SectionRequirementLink.section_id == section_id,
            SectionRequirementLink.requirement_id == requirement_id,
        )
    )
    if existing.scalar_one_or_none():
        return  # already linked

    db.add(
        SectionRequirementLink(
            section_id=section_id,
            requirement_id=requirement_id,
            relevance_score=relevance_score,
            created_by=user_id,
        )
    )
    await db.commit()


async def unlink_requirement(db: AsyncSession, link_id: uuid.UUID) -> None:
    await db.execute(
        delete(SectionRequirementLink).where(SectionRequirementLink.id == link_id)
    )
    await db.commit()


async def mark_addressed(
    db: AsyncSession, link_id: uuid.UUID, is_addressed: bool
) -> None:
    result = await db.execute(
        select(SectionRequirementLink).where(SectionRequirementLink.id == link_id)
    )
    link = result.scalar_one_or_none()
    if link:
        link.is_addressed = is_addressed
        await db.commit()
