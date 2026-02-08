"""
Pydantic v2 schemas for AI generation, audit, and cost estimation.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Generate
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    project_id: uuid.UUID
    section_id: uuid.UUID | None = None
    prompt: str
    context: str | None = None
    template: str | None = None
    section_level: str = "L3"
    generation_mode: str = "generate"
    model_override: str | None = None
    thinking_budget: int | None = None
    use_cache: bool = True
    temperature: float | None = None
    max_tokens: int = 4096
    persona_id: uuid.UUID | None = None


class GenerateResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    success: bool
    content: str
    model_used: str
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    thinking_tokens: int = 0
    cost: CostEstimate | None = None
    generation_time_ms: int = 0
    section_level: str = ""
    cache_hit: bool = False


# ---------------------------------------------------------------------------
# Audit (L2)
# ---------------------------------------------------------------------------

class AuditRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    project_id: uuid.UUID
    section_id: uuid.UUID | None = None
    template_content: str
    requirement_content: str
    audit_type: str = "compliance"
    strict_mode: bool = True
    model_override: str | None = None


class AuditModification(BaseModel):
    original: str
    suggested: str
    reason: str


class AuditResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    needs_modification: bool
    modifications: list[AuditModification] = []
    modified_content: str | None = None
    model_used: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    cost: CostEstimate | None = None


# ---------------------------------------------------------------------------
# Cost
# ---------------------------------------------------------------------------

class CostEstimate(BaseModel):
    input_cost: float = 0.0
    output_cost: float = 0.0
    cache_savings: float = 0.0
    total_cost: float = 0.0


class EstimateCostRequest(BaseModel):
    model: str
    input_tokens: int
    output_tokens: int
    cached_tokens: int = 0


class EstimateCostResponse(BaseModel):
    model: str
    estimate: CostEstimate


# ---------------------------------------------------------------------------
# Model info
# ---------------------------------------------------------------------------

class ModelInfo(BaseModel):
    name: str
    provider: str
    input_price: float
    output_price: float
    cached_price: float = 0.0
    supports_caching: bool = False
    supports_thinking: bool = False
    max_output_tokens: int = 8192


class StrategyInfo(BaseModel):
    level: str
    description: str
    primary_model: str
    fallback_model: str
    thinking_budget: int
    temperature: float


# ---------------------------------------------------------------------------
# Persona
# ---------------------------------------------------------------------------

class PersonaCreate(BaseModel):
    name: str
    description: str | None = None
    system_prompt: str
    preferred_model: str = "gpt-4o"
    parameters: dict | None = None
    default_max_tokens: int = 4096
    is_active: bool = True


class PersonaUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    preferred_model: str | None = None
    parameters: dict | None = None
    default_max_tokens: int | None = None
    is_active: bool | None = None


class PersonaResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    system_prompt: str
    preferred_model: str
    parameters: dict | None = None
    default_max_tokens: int
    is_active: bool
    is_system: bool
    created_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Resolve forward references
GenerateResponse.model_rebuild()
AuditResponse.model_rebuild()
