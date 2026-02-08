"""
Section-level strategy service — recommend models and build prompts.
"""

from app.core.ai_config import (
    MODEL_CONFIG,
    SECTION_LEVEL_STRATEGY,
    SectionLevel,
    recommend_model_for_section,
)
from app.services.llm_providers.anthropic import ClaudePrompts
from app.services.llm_providers.google import GeminiPrompts
from app.services.llm_providers.openai import GPTPrompts

SYSTEM_PROMPTS: dict[str, dict[str, str]] = {
    "basic": {
        "anthropic": ClaudePrompts.BASIC,
        "google": GeminiPrompts.BASIC,
        "openai": GPTPrompts.BASIC,
    },
    "compliance": {
        "anthropic": ClaudePrompts.AUDIT,
        "google": GeminiPrompts.COMPLIANCE,
        "openai": GPTPrompts.STANDARD,
    },
    "standard": {
        "anthropic": ClaudePrompts.STANDARD,
        "google": GeminiPrompts.STANDARD,
        "openai": GPTPrompts.STANDARD,
    },
    "strategic": {
        "anthropic": ClaudePrompts.STRATEGIC,
        "google": GeminiPrompts.STANDARD,
        "openai": GPTPrompts.STANDARD,
    },
}


def get_strategy(level: str) -> dict:
    strategy = SECTION_LEVEL_STRATEGY.get(level)
    if strategy is None:
        strategy = SECTION_LEVEL_STRATEGY["L3"]
    model_cfg = MODEL_CONFIG.get(strategy.primary_model)
    provider = model_cfg.provider if model_cfg else "google"
    prompt_key = strategy.system_prompt_key
    system_prompt = SYSTEM_PROMPTS.get(prompt_key, {}).get(provider, "")
    return {
        "model": strategy.primary_model,
        "fallback_model": strategy.fallback_model,
        "thinking_budget": strategy.thinking_budget,
        "temperature": strategy.temperature,
        "system_prompt": system_prompt,
        "provider": provider,
        "description": strategy.description,
    }


def get_all_strategies() -> list[dict]:
    results = []
    for level, strategy in SECTION_LEVEL_STRATEGY.items():
        results.append({
            "level": level,
            "description": strategy.description,
            "primary_model": strategy.primary_model,
            "fallback_model": strategy.fallback_model,
            "thinking_budget": strategy.thinking_budget,
            "temperature": strategy.temperature,
        })
    return results


def get_all_models() -> list[dict]:
    results = []
    for name, cfg in MODEL_CONFIG.items():
        results.append({
            "name": name,
            "provider": cfg.provider,
            "input_price": cfg.input_per_million,
            "output_price": cfg.output_per_million,
            "cached_price": cfg.cached_per_million,
            "supports_caching": cfg.supports_caching,
            "supports_thinking": cfg.supports_thinking,
            "max_output_tokens": cfg.max_output_tokens,
        })
    return results


def recommend_level(chapter_number: str, title: str, depth_level: int) -> str:
    return recommend_model_for_section(chapter_number, title, depth_level)
