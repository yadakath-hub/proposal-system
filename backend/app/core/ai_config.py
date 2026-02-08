"""
AI configuration: model pricing, section-level strategies, cost estimation.
"""

from enum import Enum
from dataclasses import dataclass


class SectionLevel(str, Enum):
    L1_BASIC = "L1"
    L2_COMPLIANCE = "L2"
    L3_STANDARD = "L3"
    L4_STRATEGIC = "L4"


class AIProvider(str, Enum):
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OPENAI = "openai"


class GenerationMode(str, Enum):
    GENERATE = "generate"
    REWRITE = "rewrite"
    AUDIT = "audit"
    SUMMARIZE = "summarize"
    EXPAND = "expand"


@dataclass(frozen=True)
class ModelPricing:
    input_per_million: float
    output_per_million: float
    cached_per_million: float = 0.0
    provider: str = ""
    supports_caching: bool = False
    supports_thinking: bool = False
    max_output_tokens: int = 8192


MODEL_CONFIG: dict[str, ModelPricing] = {
    "claude-4.5-sonnet": ModelPricing(
        input_per_million=3.00,
        output_per_million=15.00,
        cached_per_million=0.30,
        provider="anthropic",
        supports_caching=True,
        supports_thinking=True,
        max_output_tokens=16384,
    ),
    "claude-3.5-sonnet": ModelPricing(
        input_per_million=3.00,
        output_per_million=15.00,
        cached_per_million=0.30,
        provider="anthropic",
        supports_caching=True,
        supports_thinking=False,
        max_output_tokens=8192,
    ),
    "gemini-2.5-flash": ModelPricing(
        input_per_million=0.30,
        output_per_million=2.50,
        cached_per_million=0.03,
        provider="google",
        supports_caching=True,
        supports_thinking=True,
        max_output_tokens=8192,
    ),
    "gemini-2.5-flash-lite": ModelPricing(
        input_per_million=0.10,
        output_per_million=0.40,
        cached_per_million=0.0,
        provider="google",
        supports_caching=False,
        supports_thinking=False,
        max_output_tokens=8192,
    ),
    "gpt-4o-mini": ModelPricing(
        input_per_million=0.15,
        output_per_million=0.60,
        cached_per_million=0.0,
        provider="openai",
        supports_caching=False,
        supports_thinking=False,
        max_output_tokens=4096,
    ),
}


@dataclass(frozen=True)
class LevelStrategy:
    primary_model: str
    fallback_model: str
    thinking_budget: int
    temperature: float
    system_prompt_key: str
    description: str


SECTION_LEVEL_STRATEGY: dict[str, LevelStrategy] = {
    "L1": LevelStrategy(
        primary_model="gemini-2.5-flash-lite",
        fallback_model="gpt-4o-mini",
        thinking_budget=0,
        temperature=0.3,
        system_prompt_key="basic",
        description="基礎層：目錄、簡介、基本格式文字",
    ),
    "L2": LevelStrategy(
        primary_model="claude-3.5-sonnet",
        fallback_model="gemini-2.5-flash",
        thinking_budget=0,
        temperature=0.2,
        system_prompt_key="compliance",
        description="合規層：資安、法規、合規性審查（稽核模式）",
    ),
    "L3": LevelStrategy(
        primary_model="gemini-2.5-flash",
        fallback_model="gpt-4o-mini",
        thinking_budget=1000,
        temperature=0.5,
        system_prompt_key="standard",
        description="標準層：專案管理、時程、人力配置",
    ),
    "L4": LevelStrategy(
        primary_model="claude-4.5-sonnet",
        fallback_model="claude-3.5-sonnet",
        thinking_budget=2000,
        temperature=0.7,
        system_prompt_key="strategic",
        description="決勝層：解決方案、技術架構、創新提案",
    ),
}


def estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int = 0,
) -> dict:
    pricing = MODEL_CONFIG.get(model)
    if pricing is None:
        return {"input_cost": 0, "output_cost": 0, "cache_savings": 0, "total_cost": 0}

    billable_input = input_tokens - cached_tokens
    input_cost = billable_input * pricing.input_per_million / 1_000_000
    cached_cost = cached_tokens * pricing.cached_per_million / 1_000_000
    output_cost = output_tokens * pricing.output_per_million / 1_000_000
    full_input_cost = input_tokens * pricing.input_per_million / 1_000_000
    cache_savings = full_input_cost - (input_cost + cached_cost) if cached_tokens > 0 else 0.0

    return {
        "input_cost": round(input_cost + cached_cost, 6),
        "output_cost": round(output_cost, 6),
        "cache_savings": round(cache_savings, 6),
        "total_cost": round(input_cost + cached_cost + output_cost, 6),
    }


def recommend_model_for_section(
    chapter_number: str,
    title: str,
    depth_level: int,
) -> str:
    title_lower = title.lower()
    compliance_kw = ["資安", "法規", "合規", "隱私", "安全", "稽核", "iso", "個資"]
    strategic_kw = ["解決方案", "技術架構", "創新", "策略", "核心", "設計"]
    basic_kw = ["目錄", "簡介", "封面", "附件", "附錄", "索引"]

    for kw in basic_kw:
        if kw in title_lower:
            return "L1"
    for kw in compliance_kw:
        if kw in title_lower:
            return "L2"
    for kw in strategic_kw:
        if kw in title_lower:
            return "L4"
    return "L3"
