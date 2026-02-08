"""
Batch import parsed section structures into a project.
"""

import uuid
import logging

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.section import Section
from app.models.user import User
from app.schemas.structure import ParsedSection, StructureImportResponse

logger = logging.getLogger(__name__)


async def import_sections(
    db: AsyncSession,
    project_id: uuid.UUID,
    sections: list[ParsedSection],
    user: User,
    clear_existing: bool = False,
) -> StructureImportResponse:
    """Import a list of parsed sections into a project."""
    try:
        # Optionally clear existing sections
        if clear_existing:
            await db.execute(
                delete(Section).where(Section.project_id == project_id)
            )
            max_sort = -1
        else:
            # Get current max sort_order
            result = await db.execute(
                select(func.coalesce(func.max(Section.sort_order), -1))
                .where(Section.project_id == project_id)
            )
            max_sort = result.scalar_one()

        # Track chapter_number → section id for parent resolution
        number_to_id: dict[str, uuid.UUID] = {}
        imported_ids: list[uuid.UUID] = []

        for idx, parsed in enumerate(sections):
            # Resolve parent_id from chapter_number hierarchy
            parent_id = None
            if parsed.parent_number and parsed.parent_number in number_to_id:
                parent_id = number_to_id[parsed.parent_number]

            section = Section(
                project_id=project_id,
                parent_id=parent_id,
                chapter_number=parsed.chapter_number,
                title=parsed.title,
                requirement_text=parsed.description or "",
                sort_order=max_sort + idx + 1,
                depth_level=parsed.depth_level,
                estimated_pages=1,
            )
            db.add(section)
            # Flush to get the generated id
            await db.flush()

            number_to_id[parsed.chapter_number] = section.id
            imported_ids.append(section.id)

        await db.commit()

        return StructureImportResponse(
            success=True,
            imported_count=len(imported_ids),
            section_ids=imported_ids,
            message=f"成功匯入 {len(imported_ids)} 個章節",
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"Import error: {e}")
        return StructureImportResponse(
            success=False,
            imported_count=0,
            section_ids=[],
            message=str(e),
        )
