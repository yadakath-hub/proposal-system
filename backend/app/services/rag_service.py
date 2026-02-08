"""
RAG service — chunk documents, build vector index, semantic search.
"""

import uuid

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentEmbedding
from app.services import embedding_service


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_document(
    content: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    if not content:
        return []

    # Split by paragraphs first, then merge into chunks
    paragraphs = [p.strip() for p in content.split("\n") if p.strip()]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)
        if current_len + para_len > chunk_size and current:
            chunks.append("\n".join(current))
            # Keep overlap: take last few paragraphs
            overlap_text = "\n".join(current)
            if len(overlap_text) > overlap:
                # Start next chunk with tail of current
                tail = overlap_text[-overlap:]
                current = [tail]
                current_len = len(tail)
            else:
                current = []
                current_len = 0
        current.append(para)
        current_len += para_len

    if current:
        chunks.append("\n".join(current))

    return chunks


# ---------------------------------------------------------------------------
# Index
# ---------------------------------------------------------------------------

async def index_document(
    document_id: uuid.UUID,
    content: str,
    source_type: str,
    db: AsyncSession,
    chunk_size: int = 500,
    overlap: int = 50,
) -> int:
    # Remove old embeddings for this document
    await db.execute(
        delete(DocumentEmbedding).where(
            DocumentEmbedding.source_id == document_id,
            DocumentEmbedding.source_type == source_type,
        )
    )
    await db.flush()

    chunks = chunk_document(content, chunk_size, overlap)
    if not chunks:
        return 0

    # Generate embeddings
    embeddings = await embedding_service.embed_chunks(chunks)

    # Insert into document_embeddings
    for i, (chunk_text, emb_vector) in enumerate(zip(chunks, embeddings)):
        entry = DocumentEmbedding(
            source_type=source_type,
            source_id=document_id,
            chunk_index=i,
            chunk_text=chunk_text,
            embedding=emb_vector,
            metadata_={"token_count": len(chunk_text)},
        )
        db.add(entry)

    await db.commit()
    return len(chunks)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

async def search(
    query: str,
    project_id: uuid.UUID | None,
    db: AsyncSession,
    top_k: int = 5,
    source_types: list[str] | None = None,
) -> list[dict]:
    query_embedding = await embedding_service.embed_text(query)

    # Build SQL with pgvector cosine distance
    conditions = []
    params: dict = {"embedding": str(query_embedding), "top_k": top_k}

    if source_types:
        conditions.append("de.source_type = ANY(:source_types)")
        params["source_types"] = source_types

    if project_id:
        conditions.append("d.project_id = :project_id")
        params["project_id"] = str(project_id)

    where_clause = ""
    join_clause = ""
    if project_id:
        join_clause = "LEFT JOIN documents d ON d.id = de.source_id"
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    sql = text(f"""
        SELECT
            de.chunk_text,
            1 - (de.embedding <=> :embedding::vector) AS score,
            de.source_type,
            de.source_id,
            de.chunk_index,
            de.metadata
        FROM document_embeddings de
        {join_clause}
        {where_clause}
        ORDER BY de.embedding <=> :embedding::vector
        LIMIT :top_k
    """)

    result = await db.execute(sql, params)
    rows = result.all()

    return [
        {
            "chunk_text": row.chunk_text,
            "score": round(float(row.score), 4),
            "source_type": row.source_type,
            "source_id": row.source_id,
            "chunk_index": row.chunk_index,
            "metadata": row.metadata,
        }
        for row in rows
    ]


async def get_context(
    query: str,
    project_id: uuid.UUID,
    db: AsyncSession,
    top_k: int = 5,
) -> str:
    results = await search(query, project_id, db, top_k=top_k)
    if not results:
        return ""
    context_parts = []
    for i, r in enumerate(results, 1):
        context_parts.append(f"[{i}] (score={r['score']}) {r['chunk_text']}")
    return "\n\n".join(context_parts)
