## 核心模块开发：AI内容改写

这是整个系统**最核心**的部分——用AI把抓取来的文章进行深度改写，达到"去AI味、口语化、提高原创度"的效果。

### AI改写的核心思路

很多AI生成的文章都有一个共同的问题：**有"AI味"**。比如：

- 每段都以"首先...其次...最后"开头
- 充斥着"在当今时代""值得注意的是""综上所述"等套话
- 喜欢用"标志着新篇章""具有里程碑意义"等夸张表达
- 大量使用破折号和冒号

这个模块通过精心设计的 **Prompt（提示词）** 来引导AI进行深度改写。

创建 `src\core\content_rewriter.py`：

```python
"""
AI内容改写模块 - Content Rewriter
基于LLM的文本改写：去AI味/口语化/提高原创度/风格转换/标题优化
"""

import os
import json
import logging
from typing import Optional
from dataclasses import dataclass

from src.core.article_schema import ArticleData

logger = logging.getLogger(__name__)


@dataclass
class RewriteResult:
    """改写结果"""
    title: str
    content: str
    summary: str
    original_title: str = ""
    original_length: int = 0
    rewritten_length: int = 0


# ============================================================
# Prompt 模板（这是整个系统的"灵魂"）
# ============================================================

HUMANIZE_PROMPT = """你是一位资深中文编辑，擅长将生硬的文字改写为自然流畅、有人情味的中文。

## 改写要求
1. **去AI味**：删除"在当今时代""值得注意的是""综上所述""此外""与此同时"等套话
2. **口语化**：使用更自然的表达，像朋友聊天一样，但保持专业性
3. **提高原创度**：改变句式结构，重新组织段落，用不同的词汇表达相同的意思
4. **保留核心信息**：不改变原文的事实、数据和观点
5. **优化结构**：使用小标题分隔，每段不宜过长（手机阅读友好）

## 禁止事项
- 不要添加原文没有的信息
- 不要使用"在这个快速发展的时代""标志着新篇章""具有里程碑意义"等AI常用套话
- 不要每段都以"首先/其次/最后"开头
- 不要过度使用破折号和冒号
- 不要使用"重磅""震惊""深度好文"等标题党词汇

## 输出格式
请以JSON格式返回（不要加```json标记）：
{{"title": "改写后的标题（20-30字）", "content": "改写后的正文（Markdown格式，使用##做小标题）", "summary": "100字以内的文章摘要"}}

## 原文标题
{title}

## 原文内容
{content}"""


TITLE_OPTIMIZE_PROMPT = """你是一位公众号标题优化专家。请为以下文章生成3个标题。

要求：
1. 包含核心关键词但不能堆砌
2. 有吸引力但不标题党（禁用"重磅""震惊""深度好文"）
3. 20-30字以内
4. 适合微信公众号传播

## 文章主题
{title}

## 文章摘要
{summary}

## 输出格式
{{"titles": ["标题1", "标题2", "标题3"], "best": "最佳标题", "reason": "推荐理由"}}"""


class ContentRewriter:
    """AI内容改写器"""

    def __init__(self, api_key: str = "", base_url: str = "https://api.deepseek.com/v1",
                 model: str = "deepseek-chat"):
        self.api_key = api_key or os.getenv("AI_API_KEY", "")
        self.base_url = base_url or os.getenv("AI_API_BASE", "https://api.deepseek.com/v1")
        self.model = model or os.getenv("AI_MODEL", "deepseek-chat")

    def humanize(self, article: ArticleData, max_chars: int = 6000) -> RewriteResult:
        """
        去AI味改写
        注意：如果文章太长，会截取前max_chars字进行改写
        """
        if not self.api_key:
            return RewriteResult(
                title=article.title,
                content=article.content,
                summary=article.content[:100] if article.content else "",
                original_title=article.title,
                original_length=len(article.content) if article.content else 0,
                rewritten_length=len(article.content) if article.content else 0,
            )

        content = article.content[:max_chars] if article.content else ""
        prompt = HUMANIZE_PROMPT.format(
            title=article.title,
            content=content,
        )

        result = self._call_llm(prompt)
        if result:
            return RewriteResult(
                title=result.get("title", article.title),
                content=result.get("content", content),
                summary=result.get("summary", content[:100]),
                original_title=article.title,
                original_length=len(content),
                rewritten_length=len(result.get("content", "")),
            )
        else:
            return RewriteResult(
                title=article.title,
                content=content,
                summary=content[:100],
                original_title=article.title,
                original_length=len(content),
                rewritten_length=len(content),
            )

    def optimize_titles(self, article: ArticleData) -> dict:
        """生成多个标题方案"""
        if not self.api_key:
            return {"titles": [article.title], "best": article.title, "reason": "API未配置"}

        prompt = TITLE_OPTIMIZE_PROMPT.format(
            title=article.title,
            summary=article.summary or article.content[:200],
        )
        result = self._call_llm(prompt)
        return result if result else {"titles": [article.title], "best": article.title, "reason": "生成失败"}

    def _call_llm(self, prompt: str, temperature: float = 0.7, max_tokens: int = 4000) -> Optional[dict]:
        """调用LLM API"""
        import requests
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个专业的中文内容编辑助手，请始终以JSON格式返回结果。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            if resp.status_code != 200:
                logger.error(f"LLM API错误: {resp.status_code} {resp.text[:200]}")
                return None

            data = resp.json()
            content = data["choices"][0]["message"]["content"]

            # 尝试解析JSON（AI有时会多输出```json标记）
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content[:-3]

            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}\n原始内容: {content[:500]}")
            return None
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return None
```

> ⚠️ **新手重点理解**：
> 1. `HUMANIZE_PROMPT` 是整个系统的核心，它决定了改写质量。你可以根据自己的写作风格来调整这个 Prompt。
> 2. `temperature: 0.7` 控制AI的"创造性"，0.0=非常保守，1.0=非常自由。改写类任务建议 0.7-0.8。
> 3. `_call_llm` 方法做了 `json.loads` 错误处理，因为AI有时候返回的JSON格式不完美。

---

