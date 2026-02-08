"""
LLM Provider factory — instantiates providers lazily based on config.
"""

from app.core.config import settings
from app.core.ai_config import MODEL_CONFIG
from app.services.llm_providers.base import BaseLLMProvider, ProviderError

_providers: dict[str, BaseLLMProvider] = {}


def get_provider(provider_name: str) -> BaseLLMProvider:
    if provider_name in _providers:
        return _providers[provider_name]

    if provider_name == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise ProviderError("ANTHROPIC_API_KEY not configured", provider="anthropic")
        from app.services.llm_providers.anthropic import AnthropicProvider
        _providers["anthropic"] = AnthropicProvider(settings.ANTHROPIC_API_KEY)
    elif provider_name == "google":
        if not settings.GOOGLE_API_KEY:
            raise ProviderError("GOOGLE_API_KEY not configured", provider="google")
        from app.services.llm_providers.google import GoogleGeminiProvider
        _providers["google"] = GoogleGeminiProvider(settings.GOOGLE_API_KEY)
    elif provider_name == "openai":
        if not settings.OPENAI_API_KEY:
            raise ProviderError("OPENAI_API_KEY not configured", provider="openai")
        from app.services.llm_providers.openai import OpenAIProvider
        _providers["openai"] = OpenAIProvider(settings.OPENAI_API_KEY)
    else:
        raise ProviderError(f"Unknown provider: {provider_name}")

    return _providers[provider_name]


def get_provider_for_model(model: str) -> BaseLLMProvider:
    config = MODEL_CONFIG.get(model)
    if config is None:
        raise ProviderError(f"Unknown model: {model}")
    return get_provider(config.provider)


async def close_all_providers() -> None:
    for provider in _providers.values():
        await provider.close()
    _providers.clear()
