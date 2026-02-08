"""
AI-powered template recommendation service.
"""

import json
import re
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import template_library_service
from app.services.llm_providers import get_provider_for_model
from app.services.llm_providers.base import LLMMessage, ProviderError
from app.services import requirement_service

logger = logging.getLogger(__name__)

RECOMMEND_PROMPT = """你是專業的政府標案建議書撰寫顧問。請根據以下資訊，從候選範本中推薦最適合的範本。

## 章節資訊
- 章節標題：{section_title}
- 章節類型：{section_type}

## 相關需求
{requirements}

## 專案背景
{project_context}

## 候選範本
{templates}

請分析每個範本與需求的匹配程度，按適合程度排序推薦。

回覆格式（JSON）：
```json
{{
  "analysis": "簡要分析說明（100字以內）",
  "recommendations": [
    {{
      "template_id": "uuid-string",
      "score": 95,
      "reason": "推薦理由（50字以內）"
    }}
  ]
}}
```

評分標準：
- 90-100: 高度匹配，可直接使用
- 70-89: 良好匹配，需少量調整
- 50-69: 部分匹配，需較多修改
- 50以下: 不推薦
"""


async def recommend_templates(
    db: AsyncSession,
    section_id,
    section_title: str,
    section_type: str | None = None,
    requirement_content: str | None = None,
    project_context: str | None = None,
    top_k: int = 3,
) -> dict:
    """AI-powered template recommendation."""
    try:
        # 1. Gather requirement info
        requirements_text = requirement_content or ""
        if not requirements_text:
            try:
                reqs = await requirement_service.get_section_requirements(
                    db, section_id
                )
                if reqs:
                    requirements_text = "\n".join(
                        f"- [{r['requirement_type']}] {r['content']}"
                        for r in reqs[:5]
                    )
            except Exception:
                pass
        if not requirements_text:
            requirements_text = "（無特定需求）"

        # 2. Get candidate templates via semantic search
        category = template_library_service.SECTION_TYPE_TO_CATEGORY.get(
            section_type
        )
        search_query = f"{section_title} {requirements_text[:200]}"
        similar = await template_library_service.search_similar(
            db, search_query, category=category, top_k=10
        )

        if not similar:
            templates, _ = await template_library_service.get_templates(
                db, category=category, limit=10
            )
            similar = [(t, 0.5) for t in templates]

        if not similar:
            return {
                "recommendations": [],
                "analysis": "目前沒有適合此章節類型的範本，建議新增範本",
            }

        # 3. Build template info for prompt
        templates_info = "\n\n".join(
            f"### 範本 ID: {t.id}\n"
            f"名稱：{t.name}\n"
            f"分類：{t.category}\n"
            f"描述：{t.description or '無'}\n"
            f"字數：{t.word_count}\n"
            f"使用次數：{t.usage_count}\n"
            f"內容摘要：{t.content[:300]}..."
            for t, _ in similar
        )

        # 4. Call AI
        model = "gemini-2.5-flash"
        try:
            provider = get_provider_for_model(model)
        except ProviderError:
            for fallback in ("gpt-4o-mini", "claude-3.5-sonnet"):
                try:
                    provider = get_provider_for_model(fallback)
                    model = fallback
                    break
                except ProviderError:
                    continue
            else:
                raise ProviderError("No LLM provider available")

        prompt = RECOMMEND_PROMPT.format(
            section_title=section_title,
            section_type=section_type or "未指定",
            requirements=requirements_text,
            project_context=project_context or "（無特定背景）",
            templates=templates_info,
        )

        response = await provider.generate(
            messages=[LLMMessage(role="user", content=prompt)],
            model=model,
            max_tokens=1000,
            temperature=0.3,
        )

        # 5. Parse response
        return _parse_recommendation(response.content, similar)

    except Exception as e:
        logger.error(f"Template recommendation error: {e}")
        # Fallback to similarity-based recommendations
        if similar:
            return {
                "recommendations": [
                    {
                        "template_id": str(t.id),
                        "name": t.name,
                        "category": t.category,
                        "score": int(score * 100),
                        "reason": f"語意相似度 {int(score * 100)}%",
                        "word_count": t.word_count,
                        "usage_count": t.usage_count,
                    }
                    for t, score in similar[:top_k]
                ],
                "analysis": "基於語意相似度推薦",
            }
        return {"recommendations": [], "analysis": "推薦失敗"}


def _parse_recommendation(
    response: str, templates: list
) -> dict:
    try:
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", response)
        json_str = json_match.group(1) if json_match else response
        brace_match = re.search(r"\{[\s\S]*\}", json_str)
        if brace_match:
            json_str = brace_match.group(0)
        data = json.loads(json_str)

        template_map = {str(t.id): t for t, _ in templates}

        recommendations = []
        for rec in data.get("recommendations", []):
            tid = str(rec.get("template_id", ""))
            if tid in template_map:
                t = template_map[tid]
                recommendations.append({
                    "template_id": tid,
                    "name": t.name,
                    "category": t.category,
                    "description": t.description,
                    "score": rec.get("score", 0),
                    "reason": rec.get("reason", ""),
                    "word_count": t.word_count,
                    "usage_count": t.usage_count,
                })

        return {
            "recommendations": recommendations,
            "analysis": data.get("analysis", ""),
        }

    except json.JSONDecodeError:
        logger.error(f"Failed to parse recommendation response")
        return {"recommendations": [], "analysis": "解析失敗"}
