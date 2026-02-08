"""
API endpoints for AI-powered section structure parsing and import.
"""

import base64
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.schemas.structure import (
    ParseSourceType,
    StructureParseRequest,
    StructureParseResponse,
    StructureImportRequest,
    StructureImportResponse,
)
from app.services import structure_parser_service, structure_import_service

router = APIRouter()


@router.post("/parse", response_model=StructureParseResponse)
async def parse_structure(
    project_id: uuid.UUID = Form(...),
    source_type: ParseSourceType = Form(...),
    file: Optional[UploadFile] = File(None),
    text_content: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
):
    """
    Parse section structure from an uploaded image, PDF, or pasted text.
    """
    try:
        sections = []
        raw_text = ""
        confidence = 0.0

        if source_type == ParseSourceType.IMAGE:
            if not file:
                raise HTTPException(status_code=400, detail="請上傳圖片檔案")
            content = await file.read()
            image_b64 = base64.b64encode(content).decode("utf-8")
            sections, raw_text, confidence = (
                await structure_parser_service.parse_from_image(image_b64)
            )

        elif source_type == ParseSourceType.PDF:
            if not file:
                raise HTTPException(status_code=400, detail="請上傳 PDF 檔案")
            content = await file.read()
            sections, raw_text, confidence = (
                await structure_parser_service.parse_from_pdf(content)
            )

        elif source_type == ParseSourceType.TEXT:
            if not text_content:
                raise HTTPException(status_code=400, detail="請提供文字內容")
            sections, raw_text, confidence = (
                await structure_parser_service.parse_from_text(text_content)
            )

        return StructureParseResponse(
            success=True,
            sections=sections,
            raw_text=raw_text,
            confidence=confidence,
        )

    except HTTPException:
        raise
    except Exception as e:
        return StructureParseResponse(success=False, sections=[], message=str(e))


@router.post("/parse-base64", response_model=StructureParseResponse)
async def parse_structure_base64(
    request: StructureParseRequest,
    current_user: User = Depends(get_current_user),
):
    """Parse section structure from base64 image or pasted text."""
    try:
        if request.source_type == ParseSourceType.IMAGE:
            if not request.content:
                raise HTTPException(status_code=400, detail="請提供圖片 Base64 內容")
            sections, raw_text, confidence = (
                await structure_parser_service.parse_from_image(request.content)
            )

        elif request.source_type == ParseSourceType.TEXT:
            if not request.content:
                raise HTTPException(status_code=400, detail="請提供文字內容")
            sections, raw_text, confidence = (
                await structure_parser_service.parse_from_text(request.content)
            )
        else:
            raise HTTPException(status_code=400, detail="此端點不支援 PDF，請使用 /parse")

        return StructureParseResponse(
            success=True,
            sections=sections,
            raw_text=raw_text,
            confidence=confidence,
        )

    except HTTPException:
        raise
    except Exception as e:
        return StructureParseResponse(success=False, sections=[], message=str(e))


@router.post("/import", response_model=StructureImportResponse)
async def import_structure(
    request: StructureImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Batch-import parsed sections into a project."""
    return await structure_import_service.import_sections(
        db=db,
        project_id=request.project_id,
        sections=request.sections,
        user=current_user,
        clear_existing=request.clear_existing,
    )


@router.get("/templates")
async def get_structure_templates(
    current_user: User = Depends(get_current_user),
):
    """Return predefined proposal structure templates."""
    return [
        {
            "id": "standard",
            "name": "標準建議書架構",
            "sections": [
                {"chapter_number": "1", "title": "專案說明", "depth_level": 0},
                {"chapter_number": "1.1", "title": "專案背景", "depth_level": 1},
                {"chapter_number": "1.2", "title": "專案目標", "depth_level": 1},
                {"chapter_number": "2", "title": "技術規劃", "depth_level": 0},
                {"chapter_number": "2.1", "title": "系統架構", "depth_level": 1},
                {"chapter_number": "2.2", "title": "技術規格", "depth_level": 1},
                {"chapter_number": "3", "title": "專案管理", "depth_level": 0},
                {"chapter_number": "3.1", "title": "時程規劃", "depth_level": 1},
                {"chapter_number": "3.2", "title": "人力配置", "depth_level": 1},
                {"chapter_number": "4", "title": "資安規劃", "depth_level": 0},
                {"chapter_number": "5", "title": "報價說明", "depth_level": 0},
            ],
        },
        {
            "id": "simple",
            "name": "簡易建議書架構",
            "sections": [
                {"chapter_number": "1", "title": "公司簡介", "depth_level": 0},
                {"chapter_number": "2", "title": "服務內容", "depth_level": 0},
                {"chapter_number": "3", "title": "執行方式", "depth_level": 0},
                {"chapter_number": "4", "title": "報價", "depth_level": 0},
            ],
        },
        {
            "id": "government",
            "name": "政府標案完整架構",
            "sections": [
                {"chapter_number": "1", "title": "廠商基本資料", "depth_level": 0},
                {"chapter_number": "1.1", "title": "公司簡介與實績", "depth_level": 1},
                {"chapter_number": "1.2", "title": "組織架構", "depth_level": 1},
                {"chapter_number": "2", "title": "需求分析與理解", "depth_level": 0},
                {"chapter_number": "2.1", "title": "需求理解", "depth_level": 1},
                {"chapter_number": "2.2", "title": "現況分析", "depth_level": 1},
                {"chapter_number": "3", "title": "技術建議方案", "depth_level": 0},
                {"chapter_number": "3.1", "title": "系統架構規劃", "depth_level": 1},
                {"chapter_number": "3.2", "title": "功能規格", "depth_level": 1},
                {"chapter_number": "3.3", "title": "整合與介接", "depth_level": 1},
                {"chapter_number": "4", "title": "專案管理計畫", "depth_level": 0},
                {"chapter_number": "4.1", "title": "專案組織與人力", "depth_level": 1},
                {"chapter_number": "4.2", "title": "時程規劃", "depth_level": 1},
                {"chapter_number": "4.3", "title": "品質管理", "depth_level": 1},
                {"chapter_number": "4.4", "title": "風險管理", "depth_level": 1},
                {"chapter_number": "5", "title": "資訊安全計畫", "depth_level": 0},
                {"chapter_number": "5.1", "title": "資安管理制度", "depth_level": 1},
                {"chapter_number": "5.2", "title": "個資保護", "depth_level": 1},
                {"chapter_number": "6", "title": "教育訓練與維運", "depth_level": 0},
                {"chapter_number": "7", "title": "報價與付款", "depth_level": 0},
            ],
        },
    ]
