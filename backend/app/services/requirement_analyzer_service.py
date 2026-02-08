"""
AI-powered tender requirement analyzer.
Extracts, classifies, and maps requirements to proposal sections.
"""

import json
import re
import logging

from app.schemas.requirement import ExtractedRequirement, RequirementType
from app.services.llm_providers import get_provider_for_model
from app.services.llm_providers.base import LLMMessage, ProviderError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

ANALYSIS_PROMPT = """你是專業的招標文件分析專家。請仔細分析以下招標文件內容，提取所有需求項目。

請按照以下 JSON 格式輸出，不要輸出其他內容：
```json
{
  "summary": "整體需求摘要（100字以內）",
  "key_points": ["重點1", "重點2", "重點3"],
  "requirements": [
    {
      "id": "REQ-001",
      "content": "需求描述（精簡扼要）",
      "requirement_type": "functional|technical|security|management|qualification|deliverable|timeline|other",
      "source_text": "原文引用（保留原句）",
      "priority": "high|medium|low",
      "suggested_section": "建議放在哪個章節，如：技術規劃、專案管理、資安規劃",
      "keywords": ["關鍵字1", "關鍵字2"]
    }
  ]
}
```

需求分類：
- functional: 功能性需求
- technical: 技術規格需求
- security: 資安合規需求
- management: 專案管理需求
- qualification: 廠商資格需求
- deliverable: 交付項目需求
- timeline: 時程里程碑需求
- other: 其他需求

注意：
1. 每個需求必須有 source_text 原文引用
2. 不要遺漏任何需求
3. priority 根據文件強調程度判斷
4. suggested_section 要具體

以下是招標文件內容：
"""

SECTION_MATCHING_PROMPT = """請分析以下需求應該對應到哪個章節。

現有章節結構：
{sections}

需求內容：
{requirement}

請直接回覆最適合的章節編號（如 "1.1" 或 "2"），如果都不適合請回覆 "none"。
只需要回覆編號，不要其他內容。"""


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------

async def analyze_document(
    document_text: str,
    existing_sections: list[dict] | None = None,
) -> tuple[list[ExtractedRequirement], str, list[str]]:
    """Analyze a tender document and extract requirements."""
    # Pick a capable model
    model = "gemini-2.5-flash"
    try:
        provider = get_provider_for_model(model)
    except ProviderError:
        for fallback in ("claude-3.5-sonnet", "gpt-4o-mini"):
            try:
                provider = get_provider_for_model(fallback)
                model = fallback
                break
            except ProviderError:
                continue
        else:
            raise ProviderError("No LLM provider available")

    # Split long documents
    chunks = _split_document(document_text, max_chars=40000)

    all_requirements: list[ExtractedRequirement] = []
    summary = ""
    key_points: list[str] = []

    for i, chunk in enumerate(chunks):
        messages = [
            LLMMessage(role="user", content=ANALYSIS_PROMPT + chunk)
        ]

        response = await provider.generate(
            messages=messages,
            model=model,
            max_tokens=8000,
            temperature=0.1,
        )

        chunk_reqs, chunk_summary, chunk_points = _parse_analysis_response(
            response.content
        )
        all_requirements.extend(chunk_reqs)

        if i == 0:
            summary = chunk_summary
            key_points = chunk_points

    # Re-number requirements
    for idx, req in enumerate(all_requirements):
        req.id = f"REQ-{idx + 1:03d}"

    # Match to sections if available
    if existing_sections:
        all_requirements = await _match_sections(
            all_requirements, existing_sections
        )

    return all_requirements, summary, key_points


async def _match_sections(
    requirements: list[ExtractedRequirement],
    sections: list[dict],
) -> list[ExtractedRequirement]:
    """Try to match each requirement to a section by keyword/title overlap."""
    # Build lookup
    section_titles = {
        s.get("chapter_number", ""): s.get("title", "") for s in sections
    }

    for req in requirements:
        if req.suggested_section:
            # Already has a suggestion from AI — verify it's in the list
            matched = False
            for ch_num, title in section_titles.items():
                if (
                    req.suggested_section == ch_num
                    or req.suggested_section.lower() in title.lower()
                    or title.lower() in req.suggested_section.lower()
                ):
                    req.suggested_section = ch_num
                    matched = True
                    break
            if not matched:
                # Try keyword match
                best = _keyword_match(req, section_titles)
                if best:
                    req.suggested_section = best
        else:
            best = _keyword_match(req, section_titles)
            if best:
                req.suggested_section = best

    return requirements


def _keyword_match(
    req: ExtractedRequirement, section_titles: dict[str, str]
) -> str | None:
    """Simple keyword matching to find the best section."""
    TYPE_KEYWORDS = {
        "security": ["資安", "安全", "個資", "隱私", "合規"],
        "technical": ["技術", "架構", "系統", "規格", "效能"],
        "management": ["管理", "時程", "人力", "組織", "品質"],
        "qualification": ["資格", "經驗", "實績", "證照"],
        "deliverable": ["交付", "文件", "訓練", "教育"],
        "timeline": ["時程", "里程碑", "期程"],
    }

    keywords = req.keywords + TYPE_KEYWORDS.get(req.requirement_type.value, [])
    best_score = 0
    best_section = None

    for ch_num, title in section_titles.items():
        score = sum(1 for kw in keywords if kw in title)
        if score > best_score:
            best_score = score
            best_section = ch_num

    return best_section if best_score > 0 else None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _split_document(text: str, max_chars: int = 40000) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) < max_chars:
            current += para + "\n\n"
        else:
            if current:
                chunks.append(current)
            current = para + "\n\n"

    if current:
        chunks.append(current)
    return chunks


def _parse_analysis_response(
    response: str,
) -> tuple[list[ExtractedRequirement], str, list[str]]:
    json_match = re.search(r"```json\s*([\s\S]*?)\s*```", response)
    if json_match:
        json_str = json_match.group(1)
    else:
        brace_match = re.search(r"\{[\s\S]*\}", response)
        json_str = brace_match.group(0) if brace_match else response

    try:
        data = json.loads(json_str)

        requirements: list[ExtractedRequirement] = []
        for r in data.get("requirements", []):
            try:
                rtype = RequirementType(r.get("requirement_type", "other"))
            except ValueError:
                rtype = RequirementType.OTHER

            requirements.append(
                ExtractedRequirement(
                    id=r.get("id"),
                    content=r.get("content", ""),
                    requirement_type=rtype,
                    source_text=r.get("source_text", ""),
                    source_page=r.get("source_page"),
                    priority=r.get("priority", "medium"),
                    suggested_section=r.get("suggested_section"),
                    keywords=r.get("keywords", []),
                )
            )

        return (
            requirements,
            data.get("summary", ""),
            data.get("key_points", []),
        )

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        return [], "", []
