"""
AI generation API endpoints.
"""

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.db.session import get_db
from app.models.user import User
from app.schemas.ai import (
    AuditRequest, AuditResponse,
    CostEstimate, EstimateCostRequest, EstimateCostResponse,
    GenerateRequest, GenerateResponse,
    ModelInfo, StrategyInfo,
)
from app.services.auth_service import get_current_user
from app.services import ai_service, cost_service, strategy_service
from app.services.llm_providers.base import ProviderError, RateLimitError

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
async def generate_content(
    body: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await ai_service.generate_content(body, current_user.id, db)
    except ProviderError as e:
        code = status.HTTP_429_TOO_MANY_REQUESTS if isinstance(e, RateLimitError) else status.HTTP_502_BAD_GATEWAY
        raise HTTPException(code, detail=str(e))


@router.post("/generate/stream")
async def generate_stream(
    body: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    async def event_generator():
        try:
            async for chunk in ai_service.generate_stream(body, current_user.id, db):
                yield {"event": "message", "data": json.dumps({"content": chunk})}
            yield {"event": "done", "data": json.dumps({"status": "complete"})}
        except ProviderError as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())


@router.post("/audit", response_model=AuditResponse)
async def audit_content(
    body: AuditRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await ai_service.audit_content(body, current_user.id, db)
    except ProviderError as e:
        code = status.HTTP_429_TOO_MANY_REQUESTS if isinstance(e, RateLimitError) else status.HTTP_502_BAD_GATEWAY
        raise HTTPException(code, detail=str(e))


@router.post("/rewrite", response_model=GenerateResponse)
async def rewrite_content(
    body: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await ai_service.rewrite_content(body, current_user.id, db)
    except ProviderError as e:
        code = status.HTTP_429_TOO_MANY_REQUESTS if isinstance(e, RateLimitError) else status.HTTP_502_BAD_GATEWAY
        raise HTTPException(code, detail=str(e))


@router.post("/estimate", response_model=EstimateCostResponse)
async def estimate_cost(body: EstimateCostRequest):
    est = cost_service.calculate_cost(
        body.model, body.input_tokens, body.output_tokens, body.cached_tokens
    )
    return EstimateCostResponse(model=body.model, estimate=est)


@router.get("/models", response_model=list[ModelInfo])
async def list_models(current_user: User = Depends(get_current_user)):
    return [ModelInfo(**m) for m in strategy_service.get_all_models()]


@router.get("/strategies", response_model=list[StrategyInfo])
async def list_strategies(current_user: User = Depends(get_current_user)):
    return [StrategyInfo(**s) for s in strategy_service.get_all_strategies()]
