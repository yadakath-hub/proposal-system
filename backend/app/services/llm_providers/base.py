"""
Base LLM provider interface and shared types.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator


@dataclass
class LLMMessage:
    role: str  # "system", "user", "assistant"
    content: str
    cache_control: dict | None = None  # e.g. {"type": "ephemeral"}


@dataclass
class LLMResponse:
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    thinking_tokens: int = 0
    finish_reason: str = "stop"


class ProviderError(Exception):
    def __init__(self, message: str, provider: str = "", status_code: int = 500):
        self.provider = provider
        self.status_code = status_code
        super().__init__(message)


class RateLimitError(ProviderError):
    def __init__(self, message: str = "Rate limit exceeded", provider: str = ""):
        super().__init__(message, provider=provider, status_code=429)


class BaseLLMProvider(ABC):
    provider_name: str = ""

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        thinking_budget: int = 0,
    ) -> LLMResponse: ...

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[LLMMessage],
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        thinking_budget: int = 0,
    ) -> AsyncIterator[str]: ...

    async def close(self) -> None:
        pass
