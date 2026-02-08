"""
Document API endpoints — upload, list, download, process, RAG search.
"""

import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.document import (
    DocumentDetail,
    DocumentResponse,
    ProcessResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from app.services.auth_service import get_current_user
from app.services import document_service, rag_service

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    project_id: uuid.UUID = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await document_service.upload_document(
        file, project_id, current_user.id, db
    )


@router.get("/project/{project_id}", response_model=list[DocumentResponse])
async def list_documents(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await document_service.get_documents(project_id, db)


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await document_service.get_document(document_id, db)


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await document_service.delete_document(document_id, current_user.id, db)


@router.post("/{document_id}/process", response_model=ProcessResponse)
async def process_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await document_service.process_document(document_id, db)


@router.get("/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data, filename, file_type = await document_service.download_document(
        document_id, db
    )
    media_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    return Response(
        content=data,
        media_type=media_types.get(file_type, "application/octet-stream"),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    body: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    results = await rag_service.search(
        query=body.query,
        project_id=body.project_id,
        db=db,
        top_k=body.top_k,
        source_types=body.source_types,
    )
    return SearchResponse(
        query=body.query,
        results=[SearchResult(**r) for r in results],
        total=len(results),
    )
