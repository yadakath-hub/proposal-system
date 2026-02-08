"""
OpenAI GPT provider.
"""

import openai
from typing import AsyncIterator

from app.services.llm_providers.base import (
    BaseLLMProvider, LLMMessage, LLMResponse,
    ProviderError, RateLimitError,
)


class GPTPrompts:
    BASIC = "你是文件助理，請根據提供的資訊生成簡潔的章節內容。使用繁體中文。"
    STANDARD = (
        "你是專業的建議書撰寫助手，請根據需求撰寫完整、專業的章節內容。"
        "特別注意中文表達的流暢與專業性。使用繁體中文。"
    )


class OpenAIProvider(BaseLLMProvider):
    provider_name = "openai"

    def __init__(self, api_key: str):
        self.client = openai.AsyncOpenAI(api_key=api_key)

    async def generate(
        self,
        messages: list[LLMMessage],
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        thinking_budget: int = 0,
    ) -> LLMResponse:
        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=api_messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except openai.RateLimitError as e:
            raise RateLimitError(str(e), provider="openai")
        except openai.APIError as e:
            raise ProviderError(
                str(e), provider="openai",
                status_code=getattr(e, "status_code", 500),
            )

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            cached_tokens=0,
            thinking_tokens=0,
            finish_reason=choice.finish_reason or "stop",
        )

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        thinking_budget: int = 0,
    ) -> AsyncIterator[str]:
        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=api_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except openai.RateLimitError as e:
            raise RateLimitError(str(e), provider="openai")
        except openai.APIError as e:
            raise ProviderError(str(e), provider="openai")

    async def close(self) -> None:
        await self.client.close()
