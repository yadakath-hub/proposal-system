"""
Embedding service — generate vector embeddings via OpenAI or Gemini.
Uses OpenAI text-embedding-3-small (1536 dim) to match DB column vector(1536).
"""

import asyncio
from typing import Sequence

import openai

from app.core.config import settings


_client: openai.AsyncOpenAI | None = None


def _get_client() -> openai.AsyncOpenAI:
    global _client
    if _client is None:
        _client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def embed_text(text: str, model: str | None = None) -> list[float]:
    model = model or settings.OPENAI_EMBEDDING_MODEL
    client = _get_client()
    response = await client.embeddings.create(
        input=text,
        model=model,
    )
    return response.data[0].embedding


async def embed_chunks(texts: list[str], model: str | None = None) -> list[list[float]]:
    model = model or settings.OPENAI_EMBEDDING_MODEL
    client = _get_client()

    # OpenAI supports batch embedding (up to ~8k inputs)
    BATCH_SIZE = 100
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        response = await client.embeddings.create(
            input=batch,
            model=model,
        )
        # Sort by index to preserve order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        all_embeddings.extend(emb.embedding for emb in sorted_data)

    return all_embeddings
