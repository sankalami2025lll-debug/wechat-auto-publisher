"""
正文内容提取器 - 使用平台专属CSS/XPath选择器精准定位正文

对未识别平台使用heuristics评分算法定位正文区域
"""

import re
from typing import Optional
from urllib.parse import urljoin
from html import unescape

from src.core.article_schema import ArticleData, PlatformType, ImageItem
from src.core.scraping_rules import PLATFORM_RULES

_HTML_TAG = re.compile(r"<[^>]+>")


class ContentExtractor:

    def extract(self, html: str, url: str, platform: PlatformType) -> ArticleData:
        rule = PLATFORM_RULES.get(platform, PLATFORM_RULES[PlatformType.UNKNOWN])
        article = ArticleData(url=url, platform=platform)

        article.title = self._extract_field(html, rule.title_selectors)
        article.author = self._extract_field(html, rule.author_selectors)
        article.publish_time = self._extract_field(html, rule.time_selectors)

        if rule.content_selectors:
            article.content_html = self._extract_content_html(html, rule.content_selectors)
        if not article.content_html:
            article.content_html = self._heuristic_extract(html)

        article.content = self._html_to_text(article.content_html)
        article.summary = self._generate_summary(article.content)

        article.images = self._extract_images(article.content_html, url)

        article.confidence = self._calculate_confidence(article)
        return article

    def _extract_field(self, html: str, selectors: list[str]) -> str:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        for sel in selectors:
            if sel.startswith("meta"):
                match = re.search(r'\[(.*?)\]', sel)
                if match:
                    attr, value = match.group(1).split("=", 1)
                    value = value.strip("\"'")
                    tag = soup.find("meta", attrs={attr.strip(): value})
                    if tag and tag.get("content"):
                        return unescape(tag["content"].strip())
                continue
            element = soup.select_one(sel) or soup.find("h1") if sel == "h1" else None
            if not element:
                continue
            text = element.get_text(strip=True)
            if text and len(text) > 1:
                return unescape(text)
        return ""

    def _extract_content_html(self, html: str, selectors: list[str]) -> str:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        for sel in selectors:
            element = soup.select_one(sel)
            if element:
                return str(element)
        return ""

    def _heuristic_extract(self, html: str) -> str:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        candidates = soup.find_all(["article", "main", "section", "div"])

        best_score = 0
        best_element = None

        for el in candidates:
            score = 0
            text = el.get_text()
            text_len = len(text)

            score += len(el.find_all("p")) * 3
            score += text_len / 100
            score += len(el.find_all(["h1", "h2", "h3"])) * 5

            link_text_len = sum(len(a.get_text()) for a in el.find_all("a"))
            if text_len > 0 and link_text_len / text_len > 0.3:
                score -= 20

            class_id = str(el.get("class", "")) + str(el.get("id", ""))
            noise_keywords = ["nav", "footer", "sidebar", "comment", "share", "ad"]
            for kw in noise_keywords:
                if kw in class_id.lower():
                    score -= 10

            if score > best_score:
                best_score = score
                best_element = el

        return str(best_element) if best_element else ""

    def _html_to_text(self, html: str) -> str:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        for tag in soup.find_all("br"):
            tag.replace_with("\n")
        for tag in soup.find_all(["p", "div", "li", "h1", "h2", "h3", "h4", "section"]):
            tag.insert_after("\n")
        text = soup.get_text()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n\n".join(lines)

    def _generate_summary(self, text: str, max_len: int = 200) -> str:
        cleaned = re.sub(r"\s+", " ", text).strip()
        if len(cleaned) <= max_len:
            return cleaned
        return cleaned[:max_len] + "..."

    def _extract_images(self, html: str, base_url: str) -> list[ImageItem]:
        from bs4 import BeautifulSoup
        from src.core.scraping_rules import SMALL_IMAGE_PATTERNS
        soup = BeautifulSoup(html, "lxml")
        images = []
        seen = set()

        for img in soup.find_all("img"):
            src = img.get("src", "") or img.get("data-src", "")
            if not src:
                continue

            if any(p in src.lower() for p in SMALL_IMAGE_PATTERNS):
                continue

            if src.startswith("data:image/svg"):
                continue

            if src.startswith("//"):
                src = "https:" + src
            elif not src.startswith("http"):
                src = urljoin(base_url, src)

            if src in seen:
                continue
            seen.add(src)

            width = self._parse_int(img.get("width", "0"))
            height = self._parse_int(img.get("height", "0"))

            if width > 0 and height > 0 and (width < 50 or height < 50):
                continue

            images.append(ImageItem(
                url=src,
                alt=img.get("alt", ""),
                width=width,
                height=height,
            ))

        return images

    def _parse_int(self, val: str) -> int:
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return 0

    def _calculate_confidence(self, article: ArticleData) -> float:
        score = 0.0
        if article.title:
            score += 0.3
        if article.content and len(article.content) > 200:
            score += 0.3
        if article.author:
            score += 0.1
        if article.publish_time:
            score += 0.1
        if article.images:
            score += 0.1
        if article.platform != PlatformType.UNKNOWN:
            score += 0.1
        return min(score, 1.0)
