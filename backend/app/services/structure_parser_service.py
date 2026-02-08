"""
AI-powered section structure parser.
Extracts chapter structure from images, PDFs, or plain text.
"""

import json
import re
import logging

from app.core.config import settings
from app.schemas.structure import ParsedSection
from app.services.llm_providers import get_provider_for_model
from app.services.llm_providers.base import LLMMessage, ProviderError
from app.services.parser_service import parse_pdf

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

TEXT_PARSE_PROMPT = """你是專業的招標文件分析專家。請分析以下內容，提取出建議書的章節架構。

請按照以下 JSON 格式輸出，不要輸出其他內容：
```json
{
  "sections": [
    {"chapter_number": "1", "title": "章節標題", "depth_level": 0},
    {"chapter_number": "1.1", "title": "子章節標題", "depth_level": 1},
    {"chapter_number": "1.2", "title": "子章節標題", "depth_level": 1},
    {"chapter_number": "2", "title": "章節標題", "depth_level": 0}
  ]
}
```

規則：
1. chapter_number 必須是數字編號，如 "1", "1.1", "1.2.3"
2. depth_level 表示層級深度，頂層為 0
3. 保持原文的章節標題，不要修改
4. 如果有描述性文字，放在 description 欄位
5. 按照文件中的順序排列

以下是需要分析的內容：
"""

VISION_PARSE_PROMPT = """你是專業的招標文件分析專家。請分析這張圖片中的建議書章節架構。

請按照以下 JSON 格式輸出，不要輸出其他內容：
```json
{
  "sections": [
    {"chapter_number": "1", "title": "章節標題", "depth_level": 0},
    {"chapter_number": "1.1", "title": "子章節標題", "depth_level": 1}
  ]
}
```

規則：
1. 仔細識別圖片中的所有章節編號和標題
2. chapter_number 必須是數字編號格式
3. depth_level 表示層級深度，頂層為 0
4. 保持原文標題，繁體中文
5. 按照圖片中的順序排列"""


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

async def parse_from_text(text: str) -> tuple[list[ParsedSection], str, float]:
    """Parse section structure from plain text using LLM."""
    try:
        # Use a lightweight model for text parsing
        model = "gemini-2.5-flash-lite"
        try:
            provider = get_provider_for_model(model)
        except ProviderError:
            # Fallback to any available model
            for fallback in ("gpt-4o-mini", "claude-3.5-sonnet"):
                try:
                    provider = get_provider_for_model(fallback)
                    model = fallback
                    break
                except ProviderError:
                    continue
            else:
                raise ProviderError("No LLM provider available")

        messages = [
            LLMMessage(role="user", content=TEXT_PARSE_PROMPT + text)
        ]

        response = await provider.generate(
            messages=messages,
            model=model,
            max_tokens=4000,
            temperature=0.1,
        )

        sections, confidence = _parse_json_response(response.content)
        return sections, response.content, confidence

    except Exception as e:
        logger.error(f"Text parsing error: {e}")
        raise


async def parse_from_image(image_base64: str) -> tuple[list[ParsedSection], str, float]:
    """Parse section structure from an image using Anthropic vision API."""
    try:
        import anthropic

        if not settings.ANTHROPIC_API_KEY:
            raise ProviderError("ANTHROPIC_API_KEY not configured for vision parsing")

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        media_type = _detect_image_type(image_base64)

        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.1,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64,
                        },
                    },
                    {
                        "type": "text",
                        "text": VISION_PARSE_PROMPT,
                    },
                ],
            }],
        )

        await client.close()

        raw_text = response.content[0].text if response.content else ""
        sections, confidence = _parse_json_response(raw_text)
        return sections, raw_text, confidence

    except Exception as e:
        logger.error(f"Image parsing error: {e}")
        raise


async def parse_from_pdf(pdf_content: bytes) -> tuple[list[ParsedSection], str, float]:
    """Parse section structure from a PDF file."""
    # Extract text using existing parser
    text = parse_pdf(pdf_content)

    if len(text.strip()) < 50:
        raise ValueError("PDF 文字內容過少，無法解析章節架構。請嘗試上傳截圖。")

    return await parse_from_text(text)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _detect_image_type(base64_str: str) -> str:
    if base64_str.startswith("/9j/"):
        return "image/jpeg"
    if base64_str.startswith("iVBOR"):
        return "image/png"
    if base64_str.startswith("R0lGOD"):
        return "image/gif"
    return "image/png"


def _parse_json_response(
    response: str,
) -> tuple[list[ParsedSection], float]:
    """Extract section list from AI response JSON."""
    # Try to extract JSON from markdown code block
    json_match = re.search(r"```json\s*([\s\S]*?)\s*```", response)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find raw JSON object
        brace_match = re.search(r"\{[\s\S]*\}", response)
        json_str = brace_match.group(0) if brace_match else response

    try:
        data = json.loads(json_str)
        sections_data = data.get("sections", [])

        sections: list[ParsedSection] = []
        for s in sections_data:
            section = ParsedSection(
                chapter_number=str(s.get("chapter_number", s.get("section_number", ""))),
                title=s.get("title", ""),
                depth_level=int(s.get("depth_level", s.get("level", 0))),
                parent_number=s.get("parent_number"),
                description=s.get("description"),
            )
            sections.append(section)

        sections = _fill_parent_numbers(sections)
        confidence = 0.9 if sections else 0.0
        return sections, confidence

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        return _fallback_parse(response), 0.5


def _fill_parent_numbers(sections: list[ParsedSection]) -> list[ParsedSection]:
    """Auto-fill parent_number from chapter_number hierarchy."""
    for section in sections:
        if "." in section.chapter_number and not section.parent_number:
            parts = section.chapter_number.rsplit(".", 1)
            section.parent_number = parts[0]
    return sections


def _fallback_parse(text: str) -> list[ParsedSection]:
    """Regex-based fallback when AI JSON parsing fails."""
    sections: list[ParsedSection] = []

    patterns = [
        r"^(\d+(?:\.\d+)*)[.、\s]+(.+)",     # 1. 標題 or 1.1 標題
        r"^第([一二三四五六七八九十]+)章[.、\s]*(.+)",  # 第一章 標題
    ]

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                number = match.group(1)
                title = match.group(2).strip()
                depth = number.count(".") if "." in number else 0

                sections.append(
                    ParsedSection(
                        chapter_number=number,
                        title=title,
                        depth_level=depth,
                    )
                )
                break

    return _fill_parent_numbers(sections)
