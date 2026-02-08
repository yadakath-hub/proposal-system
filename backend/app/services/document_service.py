"""
Document service — upload to MinIO, CRUD, trigger parsing & embedding.
"""

import io
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile, status
from minio import Minio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import Document
from app.schemas.document import DocumentDetail, DocumentResponse, ProcessResponse
from app.services import parser_service, rag_service


def _get_minio() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


async def _get_doc_or_404(doc_id: uuid.UUID, db: AsyncSession) -> Document:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "文件不存在")
    return doc


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

async def upload_document(
    file: UploadFile,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> DocumentResponse:
    if not file.filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "檔案名稱不可為空")

    file_type = parser_service.detect_file_type(file.filename)
    if file_type == "unknown":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "不支援的檔案格式")

    data = await file.read()
    file_size = len(data)

    if file_size > settings.max_upload_size_bytes:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"檔案大小超過 {settings.MAX_UPLOAD_SIZE_MB}MB 限制",
        )

    doc_id = uuid.uuid4()
    object_name = f"{project_id}/{doc_id}/{file.filename}"

    # Upload to MinIO
    client = _get_minio()
    client.put_object(
        bucket_name=settings.BUCKET_TENDER_DOCS,
        object_name=object_name,
        data=io.BytesIO(data),
        length=file_size,
        content_type=file.content_type or "application/octet-stream",
    )

    # Save DB record
    doc = Document(
        id=doc_id,
        project_id=project_id,
        filename=file.filename,
        original_filename=file.filename,
        file_type=file_type,
        file_size=file_size,
        file_path=object_name,
        uploaded_by=user_id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return DocumentResponse.model_validate(doc)


# ---------------------------------------------------------------------------
# List / Get / Delete
# ---------------------------------------------------------------------------

async def get_documents(
    project_id: uuid.UUID, db: AsyncSession
) -> list[DocumentResponse]:
    result = await db.execute(
        select(Document)
        .where(Document.project_id == project_id)
        .order_by(Document.created_at.desc())
    )
    return [DocumentResponse.model_validate(d) for d in result.scalars().all()]


async def get_document(
    doc_id: uuid.UUID, db: AsyncSession
) -> DocumentDetail:
    doc = await _get_doc_or_404(doc_id, db)
    return DocumentDetail.model_validate(doc)


async def delete_document(
    doc_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> None:
    doc = await _get_doc_or_404(doc_id, db)

    # Delete from MinIO
    try:
        client = _get_minio()
        client.remove_object(settings.BUCKET_TENDER_DOCS, doc.file_path)
    except Exception:
        pass  # file may already be gone

    await db.delete(doc)
    await db.commit()


# ---------------------------------------------------------------------------
# Download (returns file bytes + metadata)
# ---------------------------------------------------------------------------

async def download_document(
    doc_id: uuid.UUID, db: AsyncSession
) -> tuple[bytes, str, str]:
    doc = await _get_doc_or_404(doc_id, db)
    client = _get_minio()
    response = client.get_object(settings.BUCKET_TENDER_DOCS, doc.file_path)
    data = response.read()
    response.close()
    response.release_conn()
    return data, doc.original_filename, doc.file_type


# ---------------------------------------------------------------------------
# Process: parse + chunk + embed
# ---------------------------------------------------------------------------

async def process_document(
    doc_id: uuid.UUID, db: AsyncSession
) -> ProcessResponse:
    doc = await _get_doc_or_404(doc_id, db)

    # Download from MinIO
    client = _get_minio()
    response = client.get_object(settings.BUCKET_TENDER_DOCS, doc.file_path)
    data = response.read()
    response.close()
    response.release_conn()

    # Parse text
    content = parser_service.parse_file(data, doc.file_type)
    if not content.strip():
        return ProcessResponse(
            document_id=doc_id,
            status="empty",
            message="文件內容為空，無法解析",
        )

    doc.content_text = content
    doc.is_parsed = True
    doc.parsed_at = datetime.now(timezone.utc)

    # Chunk + embed
    try:
        chunk_count = await rag_service.index_document(
            document_id=doc_id,
            content=content,
            source_type="TenderDocument",
            db=db,
        )
        doc.chunk_count = chunk_count
    except Exception as e:
        # Parsing succeeded but embedding failed (e.g. no API key)
        doc.chunk_count = 0
        await db.commit()
        await db.refresh(doc)
        return ProcessResponse(
            document_id=doc_id,
            status="parsed",
            content_length=len(content),
            chunk_count=0,
            message=f"文件已解析但向量化失敗: {e}",
        )

    await db.commit()
    await db.refresh(doc)
    return ProcessResponse(
        document_id=doc_id,
        status="indexed",
        content_length=len(content),
        chunk_count=doc.chunk_count,
        message="文件已解析並建立向量索引",
    )
