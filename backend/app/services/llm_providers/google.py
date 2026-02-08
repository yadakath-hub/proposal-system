"""
Google Gemini provider with Context Caching and Thinking Budget.
"""

import google.generativeai as genai
from typing import AsyncIterator

from app.services.llm_providers.base import (
    BaseLLMProvider, LLMMessage, LLMResponse,
    ProviderError, RateLimitError,
)


class GeminiPrompts:
    BASIC = "你是文件助理，請根據提供的資訊生成簡潔的章節內容。使用繁體中文。"
    STANDARD = "你是專業的建議書撰寫助手，請根據需求撰寫完整、專業的章節內容。使用繁體中文。"
    COMPLIANCE = "你是合規審查助手，請檢查內容是否符合法規要求並提出修改建議。使用繁體中文。"


class GoogleGeminiProvider(BaseLLMProvider):
    provider_name = "google"

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self._api_key = api_key

    async def generate(
        self,
        messages: list[LLMMessage],
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        thinking_budget: int = 0,
    ) -> LLMResponse:
        system_text = "\n".join(m.content for m in messages if m.role == "system")
        chat_msgs = [m for m in messages if m.role != "system"]

        gen_config: dict = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }
        if thinking_budget > 0:
            gen_config["thinking_config"] = {"thinking_budget": thinking_budget}

        try:
            gm = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_text or None,
                generation_config=gen_config,
            )
            contents = []
            for m in chat_msgs:
                role = "model" if m.role == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": m.content}]})

            response = await gm.generate_content_async(contents)
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "quota" in err_msg.lower():
                raise RateLimitError(err_msg, provider="google")
            raise ProviderError(err_msg, provider="google")

        usage = getattr(response, "usage_metadata", None)
        input_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
        output_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0
        cached = getattr(usage, "cached_content_token_count", 0) if usage else 0
        thinking = getattr(usage, "thinking_token_count", 0) if usage else 0

        return LLMResponse(
            content=response.text,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached,
            thinking_tokens=thinking,
        )

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        thinking_budget: int = 0,
    ) -> AsyncIterator[str]:
        system_text = "\n".join(m.content for m in messages if m.role == "system")
        chat_msgs = [m for m in messages if m.role != "system"]

        gen_config: dict = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }
        if thinking_budget > 0:
            gen_config["thinking_config"] = {"thinking_budget": thinking_budget}

        try:
            gm = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_text or None,
                generation_config=gen_config,
            )
            contents = []
            for m in chat_msgs:
                role = "model" if m.role == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": m.content}]})

            response = await gm.generate_content_async(contents, stream=True)
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "quota" in err_msg.lower():
                raise RateLimitError(err_msg, provider="google")
            raise ProviderError(err_msg, provider="google")
