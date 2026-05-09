"""
Markdown格式化器 - 将ArticleData输出为结构化Markdown + JSON元数据
"""

import json
import os
from datetime import datetime

from src.core.article_schema import ArticleData, ScrapeStatus


class MarkdownFormatter:

    def to_markdown(self, article: ArticleData, include_metadata: bool = True,
                    include_images: bool = True) -> str:
        lines = []

        if article.status != ScrapeStatus.SUCCESS:
            return self._error_markdown(article)

        if include_metadata:
            lines.append(f"# {article.title}")
            lines.append("")
            lines.append(f"> **来源**: {article.platform.value} · [{article.url}]({article.url})")
            if article.author:
                lines.append(f"> **作者**: {article.author} · **时间**: {article.publish_time}")
            lines.append(f"> **提取方式**: {article.fetcher_used.value} · **可信度**: {article.confidence:.0%}")
            if article.cached:
                lines.append("> ⚡ *来自缓存*")
            lines.append("")
            lines.append("---")
            lines.append("")

        lines.append(article.content)
        lines.append("")

        if include_images and article.images:
            lines.append("---")
            lines.append("")
            lines.append("## 🖼️ 图片列表")
            lines.append("")
            for i, img in enumerate(article.images):
                lines.append(f"{i + 1}. ![{img.alt or f'图片{i+1}'}]({img.url})")

        return "\n".join(lines)

    def to_json(self, article: ArticleData) -> str:
        return json.dumps(self.to_dict(article), ensure_ascii=False, indent=2)

    def to_dict(self, article: ArticleData) -> dict:
        return {
            "url": article.url,
            "platform": article.platform.value,
            "title": article.title,
            "author": article.author,
            "publish_time": article.publish_time,
            "content_length": len(article.content),
            "content_preview": article.content[:200],
            "images": [{"url": i.url, "alt": i.alt, "local_path": i.local_path} for i in article.images],
            "image_count": len(article.images),
            "fetcher_used": article.fetcher_used.value,
            "fetch_time_ms": article.fetch_time_ms,
            "retries": article.retries,
            "confidence": round(article.confidence, 3),
            "status": article.status.value,
            "cached": article.cached,
            "warnings": article.warnings,
            "extracted_at": datetime.now().isoformat(),
        }

    def save(self, article: ArticleData, output_dir: str = "data/articles") -> dict:
        os.makedirs(output_dir, exist_ok=True)
        safe_title = "".join(c for c in article.title[:40] if c.isalnum() or c in " _-").strip() or "article"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = os.path.join(output_dir, f"{timestamp}_{safe_title}")

        md_path = base + ".md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self.to_markdown(article))

        json_path = base + ".json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(self.to_json(article))

        return {"markdown": md_path, "json": json_path}

    def _error_markdown(self, article: ArticleData) -> str:
        lines = [
            f"# 抓取失败",
            "",
            f"> **URL**: {article.url}",
            f"> **状态**: {article.status.value}",
            "",
        ]
        if article.error_message:
            lines.append(f"**错误**: {article.error_message}")
        if article.warnings:
            lines.append("")
            lines.append("**警告**:")
            for w in article.warnings:
                lines.append(f"- {w}")
        return "\n".join(lines)
