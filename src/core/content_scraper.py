"""
网页内容自动抓取解析模块 - 主入口

完整的抓取链路：URL路由 → 抓取 → 提取 → 过滤 → 格式化

使用示例:
    scraper = ContentScraper()
    article = scraper.scrape("https://mp.weixin.qq.com/s/xxxxx")
    print(scraper.formatter.to_markdown(article))
"""

import time
import hashlib
import logging
from typing import Optional
from collections import OrderedDict

from src.core.article_schema import (
    ArticleData, FetchResult, FetcherType, PlatformType,
    ScrapeConfig, ScrapeStatus,
)
from src.core.platform_router import PlatformRouter
from src.core.fetch_engine import FetchEngine
from src.core.content_extractor import ContentExtractor
from src.core.noise_filter import NoiseFilter
from src.core.image_processor import ImageProcessor
from src.core.markdown_formatter import MarkdownFormatter

logger = logging.getLogger(__name__)
_cache_store: OrderedDict = OrderedDict()
CACHE_MAX_SIZE = 500


class ContentScraper:

    def __init__(self, config: ScrapeConfig = None):
        self.config = config or ScrapeConfig()
        self.router = PlatformRouter()
        self.fetcher = FetchEngine(self.config)
        self.extractor = ContentExtractor()
        self.noise_filter = NoiseFilter()
        self.image_processor = ImageProcessor(
            max_count=self.config.max_image_count,
            min_size=self.config.min_image_size,
        )
        self.formatter = MarkdownFormatter()

    def scrape(self, url: str, platform_hint: str = "",
               download_images: bool = False) -> ArticleData:
        valid, err = self.router.validate_url(url)
        if not valid:
            return ArticleData(url=url, status=ScrapeStatus.FAILED, error_message=err)

        if self.config.cache_enabled:
            cached = self._get_cache(url)
            if cached:
                cached.cached = True
                return cached

        platform = PlatformType(platform_hint) if platform_hint else self.router.identify(url)
        rule = self.router.get_rule(platform)

        t_start = time.time()
        fetch_result = self.fetcher.fetch(url, platform)

        if fetch_result.error:
            article = ArticleData(
                url=url, platform=platform,
                status=self._classify_status(fetch_result),
                fetcher_used=fetch_result.fetcher_type,
                error_message=fetch_result.error,
                fetch_time_ms=fetch_result.fetch_time_ms,
                retries=fetch_result.retries,
            )
            return article

        article = self.extractor.extract(fetch_result.page_html, url, platform)
        article.fetcher_used = fetch_result.fetcher_type
        article.fetch_time_ms = fetch_result.fetch_time_ms
        article.retries = fetch_result.retries

        article.content_html = self.noise_filter.filter(article.content_html, platform.value)
        article.content = self._html_to_text(article.content_html)
        article.summary = self._summary(article.content)

        article.images = self.image_processor.deduplicate(article.images)
        if download_images:
            article.images = self.image_processor.download(article.images)

        if self.config.cache_enabled:
            self._set_cache(url, article)

        return article

    def scrape_batch(self, urls: list[str], **kwargs) -> list[ArticleData]:
        return [self.scrape(url, **kwargs) for url in urls]

    def scrape_preview(self, url: str) -> ArticleData:
        article = self.scrape(url, download_images=False)
        if article.content and len(article.content) > 500:
            article.content = article.content[:500] + "..."
        return article

    def _html_to_text(self, html: str) -> str:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        return soup.get_text("\n", strip=True)

    def _summary(self, text: str, max_len: int = 200) -> str:
        import re
        cleaned = re.sub(r"\s+", " ", text).strip()
        return cleaned[:max_len] + "..." if len(cleaned) > max_len else cleaned

    @staticmethod
    def _classify_status(fetch_result: FetchResult) -> ScrapeStatus:
        if not fetch_result.error:
            return ScrapeStatus.SUCCESS
        error_lower = fetch_result.error.lower()
        if "timeout" in error_lower:
            return ScrapeStatus.TIMEOUT
        if "login" in error_lower:
            return ScrapeStatus.LOGIN_REQUIRED
        if "paywall" in error_lower or "subscribe" in error_lower:
            return ScrapeStatus.PAYWALL
        if "block" in error_lower or "cloudflare" in error_lower or "captcha" in error_lower:
            return ScrapeStatus.BLOCKED
        return ScrapeStatus.FAILED

    @staticmethod
    def _cache_key(url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()

    def _get_cache(self, url: str) -> Optional[ArticleData]:
        global _cache_store
        cached = _cache_store.get(self._cache_key(url))
        if cached:
            return cached[1]
        return None

    def _set_cache(self, url: str, article: ArticleData):
        global _cache_store, CACHE_MAX_SIZE
        key = self._cache_key(url)
        _cache_store[key] = (time.time(), article)
        while len(_cache_store) > CACHE_MAX_SIZE:
            _cache_store.popitem(last=False)
