"""
AI Service — orchestrates LLM generation with section-level strategy,
prompt caching, thinking budgets, fallback, and usage logging.
"""

import time
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_config import MODEL_CONFIG, GenerationMode
from app.models.usage_log import UsageLog
from app.schemas.ai import (
    AuditRequest, AuditResponse, AuditModification,
    CostEstimate, GenerateRequest, GenerateResponse,
)
from app.services import cost_service
from app.services.llm_providers import get_provider_for_model, get_provider
from app.services.llm_providers.base import (
    LLMMessage, LLMResponse, ProviderError, RateLimitError,
)
from app.services.llm_providers.anthropic import ClaudePrompts
from app.services import strategy_service


# ---------------------------------------------------------------------------
# Generate content
# ---------------------------------------------------------------------------

async def generate_content(
    request: GenerateRequest,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> GenerateResponse:
    start = time.monotonic()

    # Budget check
    budget = await cost_service.check_budget_alert(request.project_id, db)
    if not budget.get("allowed", True):
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, "Token 預算已用完")

    # Resolve strategy
    strat = strategy_service.get_strategy(request.section_level)
    model = request.model_override or strat["model"]
    thinking_budget = request.thinking_budget if request.thinking_budget is not None else strat["thinking_budget"]
    temperature = request.temperature if request.temperature is not None else strat["temperature"]
    system_prompt = strat["system_prompt"]

    # Build messages
    messages = _build_messages(system_prompt, request)

    # Try primary model, fallback on error
    try:
        provider = get_provider_for_model(model)
        llm_resp = await provider.generate(
            messages=messages,
            model=model,
            max_tokens=request.max_tokens,
            temperature=temperature,
            thinking_budget=thinking_budget,
        )
    except (ProviderError, RateLimitError):
        fallback = strat["fallback_model"]
        if fallback == model:
            raise
        provider = get_provider_for_model(fallback)
        model = fallback
        llm_resp = await provider.generate(
            messages=messages,
            model=model,
            max_tokens=request.max_tokens,
            temperature=temperature,
            thinking_budget=0,
        )

    elapsed_ms = int((time.monotonic() - start) * 1000)
    cost = cost_service.calculate_cost(
        model, llm_resp.input_tokens, llm_resp.output_tokens, llm_resp.cached_tokens
    )

    # Log usage
    await _log_usage(
        db=db,
        user_id=user_id,
        project_id=request.project_id,
        section_id=request.section_id,
        model_used=model,
        input_tokens=llm_resp.input_tokens,
        output_tokens=llm_resp.output_tokens,
        cost=cost,
        action_type=request.generation_mode,
        metadata={
            "section_level": request.section_level,
            "cached_tokens": llm_resp.cached_tokens,
            "thinking_tokens": llm_resp.thinking_tokens,
            "provider": MODEL_CONFIG[model].provider if model in MODEL_CONFIG else "",
        },
    )

    return GenerateResponse(
        success=True,
        content=llm_resp.content,
        model_used=model,
        input_tokens=llm_resp.input_tokens,
        output_tokens=llm_resp.output_tokens,
        cached_tokens=llm_resp.cached_tokens,
        thinking_tokens=llm_resp.thinking_tokens,
        cost=cost,
        generation_time_ms=elapsed_ms,
        section_level=request.section_level,
        cache_hit=llm_resp.cached_tokens > 0,
    )


# ---------------------------------------------------------------------------
# Stream content (returns async generator for SSE)
# ---------------------------------------------------------------------------

async def generate_stream(
    request: GenerateRequest,
    user_id: uuid.UUID,
    db: AsyncSession,
):
    budget = await cost_service.check_budget_alert(request.project_id, db)
    if not budget.get("allowed", True):
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, "Token 預算已用完")

    strat = strategy_service.get_strategy(request.section_level)
    model = request.model_override or strat["model"]
    thinking_budget = request.thinking_budget if request.thinking_budget is not None else strat["thinking_budget"]
    temperature = request.temperature if request.temperature is not None else strat["temperature"]
    system_prompt = strat["system_prompt"]
    messages = _build_messages(system_prompt, request)

    provider = get_provider_for_model(model)
    async for chunk in provider.generate_stream(
        messages=messages,
        model=model,
        max_tokens=request.max_tokens,
        temperature=temperature,
        thinking_budget=thinking_budget,
    ):
        yield chunk


# ---------------------------------------------------------------------------
# Audit content (L2 compliance mode)
# ---------------------------------------------------------------------------

async def audit_content(
    request: AuditRequest,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> AuditResponse:
    start = time.monotonic()

    model = request.model_override or "claude-3.5-sonnet"
    system_prompt = ClaudePrompts.AUDIT

    messages = [
        LLMMessage(
            role="system",
            content=system_prompt,
            cache_control={"type": "ephemeral"},
        ),
        LLMMessage(
            role="user",
            content=(
                f"## 公司標準範本\n{request.template_content}\n\n"
                f"## 招標需求\n{request.requirement_content}\n\n"
                f"請進行{request.audit_type}稽核。"
                + (" 嚴格模式：任何不符合需求的內容都必須標記。" if request.strict_mode else "")
            ),
        ),
    ]

    try:
        provider = get_provider_for_model(model)
        llm_resp = await provider.generate(
            messages=messages,
            model=model,
            max_tokens=4096,
            temperature=0.2,
            thinking_budget=0,
        )
    except (ProviderError, RateLimitError):
        model = "gemini-2.5-flash"
        provider = get_provider_for_model(model)
        llm_resp = await provider.generate(
            messages=messages,
            model=model,
            max_tokens=4096,
            temperature=0.2,
        )

    cost = cost_service.calculate_cost(
        model, llm_resp.input_tokens, llm_resp.output_tokens, llm_resp.cached_tokens
    )

    await _log_usage(
        db=db,
        user_id=user_id,
        project_id=request.project_id,
        section_id=request.section_id,
        model_used=model,
        input_tokens=llm_resp.input_tokens,
        output_tokens=llm_resp.output_tokens,
        cost=cost,
        action_type="audit",
        metadata={
            "section_level": "L2",
            "audit_type": request.audit_type,
            "cached_tokens": llm_resp.cached_tokens,
            "provider": MODEL_CONFIG[model].provider if model in MODEL_CONFIG else "",
        },
    )

    needs_mod = "【無需調整】" not in llm_resp.content
    return AuditResponse(
        needs_modification=needs_mod,
        modified_content=llm_resp.content if needs_mod else None,
        model_used=model,
        input_tokens=llm_resp.input_tokens,
        output_tokens=llm_resp.output_tokens,
        cached_tokens=llm_resp.cached_tokens,
        cost=cost,
    )


# ---------------------------------------------------------------------------
# Rewrite content
# ---------------------------------------------------------------------------

async def rewrite_content(
    request: GenerateRequest,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> GenerateResponse:
    request.generation_mode = "rewrite"
    return await generate_content(request, user_id, db)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_messages(system_prompt: str, request: GenerateRequest) -> list[LLMMessage]:
    messages: list[LLMMessage] = []

    # System prompt with cache_control for Prompt Caching
    if system_prompt:
        messages.append(LLMMessage(
            role="system",
            content=system_prompt,
            cache_control={"type": "ephemeral"} if request.use_cache else None,
        ))

    # Tender document context (cacheable)
    if request.context:
        messages.append(LLMMessage(
            role="system",
            content=f"## 招標文件摘要\n{request.context}",
            cache_control={"type": "ephemeral"} if request.use_cache else None,
        ))

    # Template (cacheable)
    if request.template:
        messages.append(LLMMessage(
            role="system",
            content=f"## 參考範本\n{request.template}",
            cache_control={"type": "ephemeral"} if request.use_cache else None,
        ))

    # User prompt
    messages.append(LLMMessage(role="user", content=request.prompt))

    return messages


async def _log_usage(
    db: AsyncSession,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    section_id: uuid.UUID | None,
    model_used: str,
    input_tokens: int,
    output_tokens: int,
    cost: CostEstimate,
    action_type: str,
    metadata: dict | None = None,
) -> None:
    budget_info = await cost_service.check_budget_alert(project_id, db)
    log = UsageLog(
        user_id=user_id,
        project_id=project_id,
        section_id=section_id,
        model_used=model_used,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost.total_cost,
        action_type=action_type,
        budget_exceeded=not budget_info.get("allowed", True),
        metadata_=metadata or {},
    )
    db.add(log)
    await db.commit()
