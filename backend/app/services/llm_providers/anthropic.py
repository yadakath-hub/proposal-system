"""
Anthropic Claude provider with Prompt Caching and Extended Thinking.
"""

import anthropic
from typing import AsyncIterator

from app.services.llm_providers.base import (
    BaseLLMProvider, LLMMessage, LLMResponse,
    ProviderError, RateLimitError,
)


AUDIT_PROMPT = """你是資安/合規稽核專家。
請比對「公司標準範本」與「招標需求」：
1. 若範本已符合需求 → 回覆「【無需調整】」
2. 若有衝突 → 僅列出需修改處，使用 diff 格式：
```diff
- 原文：xxx
+ 建議：xxx
  原因：xxx
```
3. 嚴禁大幅重寫，只做最小必要修改
4. 保留原範本的專業術語與格式"""

STRATEGIC_PROMPT = """你是頂尖的政府標案建議書撰寫專家。
請根據招標需求和專案背景，撰寫具有競爭力的建議書內容。
要求：
1. 使用正式、專業的繁體中文
2. 突出技術創新與差異化優勢
3. 內容具體可執行，避免空泛描述
4. 結構清晰，有邏輯層次
5. 適當引用業界標準與最佳實踐"""


class ClaudePrompts:
    AUDIT = AUDIT_PROMPT
    STRATEGIC = STRATEGIC_PROMPT
    BASIC = "你是文件助理，請根據提供的資訊生成簡潔的章節內容。使用繁體中文。"
    STANDARD = "你是專業的建議書撰寫助手，請根據需求撰寫完整、專業的章節內容。使用繁體中文。"


class AnthropicProvider(BaseLLMProvider):
    provider_name = "anthropic"

    def __init__(self, api_key: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def generate(
        self,
        messages: list[LLMMessage],
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        thinking_budget: int = 0,
    ) -> LLMResponse:
        system_msgs = [m for m in messages if m.role == "system"]
        chat_msgs = [m for m in messages if m.role != "system"]

        # Build system blocks with optional cache_control
        system_content = None
        if system_msgs:
            blocks = []
            for m in system_msgs:
                block: dict = {"type": "text", "text": m.content}
                if m.cache_control:
                    block["cache_control"] = m.cache_control
                blocks.append(block)
            system_content = blocks

        api_messages = [{"role": m.role, "content": m.content} for m in chat_msgs]

        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": api_messages,
        }
        if system_content:
            kwargs["system"] = system_content

        # Extended Thinking: temperature must not be set when thinking is enabled
        if thinking_budget > 0:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": thinking_budget,
            }
        else:
            kwargs["temperature"] = temperature

        try:
            response = await self.client.messages.create(**kwargs)
        except anthropic.RateLimitError as e:
            raise RateLimitError(str(e), provider="anthropic")
        except anthropic.APIError as e:
            raise ProviderError(
                str(e), provider="anthropic",
                status_code=getattr(e, "status_code", 500),
            )

        content_parts = []
        thinking_tokens_used = 0
        for block in response.content:
            if block.type == "text":
                content_parts.append(block.text)
            elif block.type == "thinking":
                thinking_tokens_used += getattr(block, "tokens", 0)

        cached = getattr(response.usage, "cache_read_input_tokens", 0) or 0

        return LLMResponse(
            content="".join(content_parts),
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cached_tokens=cached,
            thinking_tokens=thinking_tokens_used,
            finish_reason=response.stop_reason or "stop",
        )

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        thinking_budget: int = 0,
    ) -> AsyncIterator[str]:
        system_msgs = [m for m in messages if m.role == "system"]
        chat_msgs = [m for m in messages if m.role != "system"]

        system_content = None
        if system_msgs:
            blocks = []
            for m in system_msgs:
                block: dict = {"type": "text", "text": m.content}
                if m.cache_control:
                    block["cache_control"] = m.cache_control
                blocks.append(block)
            system_content = blocks

        api_messages = [{"role": m.role, "content": m.content} for m in chat_msgs]

        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": api_messages,
        }
        if system_content:
            kwargs["system"] = system_content
        if thinking_budget > 0:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": thinking_budget,
            }
        else:
            kwargs["temperature"] = temperature

        try:
            async with self.client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    yield text
        except anthropic.RateLimitError as e:
            raise RateLimitError(str(e), provider="anthropic")
        except anthropic.APIError as e:
            raise ProviderError(str(e), provider="anthropic")

    async def close(self) -> None:
        await self.client.close()
