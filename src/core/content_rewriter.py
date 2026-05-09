"""
AI内容改写模块 - Content Rewriter

基于LLM的文本改写能力：
- 去AI味/口语化/提高原创度
- 风格转换（专业→通俗、正式→活泼）
- 标题优化
- 摘要生成
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass

from src.core.article_schema import ArticleData

logger = logging.getLogger(__name__)


@dataclass
class RewriteResult:
    title: str
    content: str
    summary: str
    original_title: str = ""
    original_length: int = 0
    rewritten_length: int = 0
    method: str = "llm"


HUMANIZE_PROMPT = """你是一位资深中文编辑，擅长将机翻/生硬的文字改写为自然流畅、有人情味的中文。

## 改写要求
1. **去AI味**：删除"在当今时代""值得注意的是""综上所述""此外""与此同时"等套话
2. **口语化**：使用更自然的表达，像朋友聊天一样，但保持专业性
3. **提高原创度**：改变句式结构，重新组织段落，用不同的词汇表达相同的意思
4. **保留核心信息**：不改变原文的事实、数据和观点

## 禁止事项
- 不要添加原文没有的信息
- 不要使用"在这个快速发展的时代"/"标志着新篇章"/"具有里程碑意义"等AI常用套话
- 不要每段都以"首先/其次/最后"开头
- 不要过度使用破折号和冒号

## 输出格式
请以JSON格式返回：
{{"title": "改写后的标题", "content": "改写后的正文", "summary": "100字以内的文章摘要"}}

## 原文标题
{title}

## 原文内容
{content}"""


STYLE_CONVERT_PROMPT = """你是一位中文写作专家，请将以下文章从{from_style}风格改写为{to_style}风格。

风格说明：
- professional: 专业正式，适合商务/技术类公众号
- casual: 口语化轻松，适合生活/娱乐类公众号
- news: 新闻资讯体，简洁客观
- storytelling: 故事叙述体，有情节感
- tutorial: 教程指南体，步骤清晰

## 输出格式
请以JSON格式返回：
{{"title": "改写后的标题", "content": "改写后的正文", "summary": "100字以内的文章摘要"}}

## 原文
{content}"""


TITLE_OPTIMIZE_PROMPT = """你是一位公众号标题优化专家。请为以下文章生成3个优化标题。

要求：
1. 包含关键词但不能堆砌
2. 有吸引力但不标题党
3. 20-30字以内
4. 不使用"重磅""震惊""深度好文"等套路词

## 文章主题
{title}

## 文章摘要
{summary}

## 输出格式
{{"titles": ["标题1", "标题2", "标题3"], "best": "最佳标题", "reason": "推荐理由"}}"""


class ContentRewriter:

    def __init__(self, api_key: str = "", base_url: str = "https://api.openai.com/v1", model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("AI_API_KEY", "")
        self.base_url = base_url or os.getenv("AI_API_BASE", "https://api.openai.com/v1")
        self.model = model or os.getenv("AI_MODEL", "gpt-4")

    def humanize(self, article: ArticleData, max_chars: int = 6000) -> RewriteResult:
        content = article.content[:max_chars] if article.content else ""
        title = article.title or ""

        prompt = HUMANIZE_PROMPT.format(title=title, content=content)

        try:
            result = self._call_llm(prompt)
            if result:
                rewritten = RewriteResult(
                    title=result.get("title", title),
                    content=result.get("content", content),
                    summary=result.get("summary", article.summary),
                    original_title=title,
                    original_length=len(content),
                    rewritten_length=len(result.get("content", "")),
                    method="llm",
                )
                return rewritten
        except Exception as e:
            logger.warning(f"LLM改写失败，使用规则降级: {e}")

        return self._rule_based_rewrite(article)

    def convert_style(self, article: ArticleData, from_style: str = "professional",
                      to_style: str = "casual") -> RewriteResult:
        content = article.content[:6000] if article.content else ""
        prompt = STYLE_CONVERT_PROMPT.format(
            from_style=from_style,
            to_style=to_style,
            content=f"标题：{article.title}\n\n正文：{content}",
        )
        try:
            result = self._call_llm(prompt)
            if result:
                return RewriteResult(
                    title=result.get("title", article.title),
                    content=result.get("content", content),
                    summary=result.get("summary", article.summary),
                    original_title=article.title,
                    original_length=len(content),
                    rewritten_length=len(result.get("content", "")),
                )
        except Exception as e:
            logger.warning(f"风格转换失败: {e}")
        return self._rule_based_rewrite(article)

    def optimize_title(self, article: ArticleData) -> dict:
        prompt = TITLE_OPTIMIZE_PROMPT.format(
            title=article.title,
            summary=article.summary or article.content[:200],
        )
        try:
            result = self._call_llm(prompt)
            if result:
                return result
        except Exception as e:
            logger.warning(f"标题优化失败: {e}")
        return {"titles": [article.title], "best": article.title, "reason": "LLM不可用，返回原标题"}

    def _call_llm(self, prompt: str, temperature: float = 0.8, max_tokens: int = 4000) -> Optional[dict]:
        if not self.api_key:
            return None

        import requests
        import json as _json

        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一位专业的中文编辑。请始终以JSON格式返回结果。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        if resp.status_code != 200:
            raise Exception(f"API错误 {resp.status_code}: {resp.text[:200]}")

        content = resp.json()["choices"][0]["message"]["content"]
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0]
        return _json.loads(content)

    def _rule_based_rewrite(self, article: ArticleData) -> RewriteResult:
        content = article.content or ""
        title = article.title or ""

        # 12组AI常用套话替换规则
        replacements = [
            ("在当今时代", ""),
            ("值得注意的是", ""),
            ("综上所述", "\n\n总结一下"),
            ("此外", "另外"),
            ("与此同时", "同时"),
            ("具有里程碑意义", "很重要"),
            ("标志着新篇章", "意味着新的开始"),
            ("在这个快速发展的时代", ""),
            ("毋庸讳言", ""),
            ("可谓", "可以说是"),
            ("突显", "显示"),
            ("彰显", "展示"),
        ]

        rewritten_content = content
        for old, new in replacements:
            rewritten_content = rewritten_content.replace(old, new)

        rewritten_content = rewritten_content.replace("\n\n\n", "\n\n").strip()

        summary = article.summary
        if summary:
            for old, new in replacements:
                summary = summary.replace(old, new)

        new_title = title
        for old, new in replacements:
            new_title = new_title.replace(old, new)

        return RewriteResult(
            title=new_title,
            content=rewritten_content,
            summary=summary,
            original_title=title,
            original_length=len(content),
            rewritten_length=len(rewritten_content),
            method="regex",
        )
