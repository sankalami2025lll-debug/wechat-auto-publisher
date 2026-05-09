"""
抓取引擎 - 3级降级Fetcher + 重试 + 超时

Level 1: Fetcher (快速HTTP)
Level 2: StealthyFetcher (隐身+Cloudflare绕过)
Level 3: DynamicFetcher (完整浏览器渲�?
"""

import time
import logging
from typing import Optional

from src.core.article_schema import (
    FetcherType, FetchResult, PlatformType, ScrapeConfig
)

logger = logging.getLogger(__name__)


class FetchEngine:

    def __init__(self, config: ScrapeConfig = None):
        self.config = config or ScrapeConfig()

    def fetch(self, url: str, platform: PlatformType = PlatformType.UNKNOWN) -> FetchResult:
        rule = PLATFORM_RULES.get(platform, PLATFORM_RULES[PlatformType.UNKNOWN])
        strategies = self._build_strategies(url, rule)
        last_error = ""

        for fetcher_type, method in strategies:
            t_start = time.time()
            retries = 0
            for attempt in range(self.config.max_retries_per_level + 1):
                try:
                    logger.info(f"[FetchEngine] {fetcher_type.value} 第{attempt+1}次尝�? {url}")
                    html, status = method(url)
                    elapsed_ms = int((time.time() - t_start) * 1000)
                    return FetchResult(
                        url=url, platform=platform, fetcher_type=fetcher_type,
                        page_html=html, http_status=status, retries=retries,
                        fetch_time_ms=elapsed_ms,
                    )
                except Exception as e:
                    retries = attempt
                    last_error = str(e)
                    logger.warning(f"[FetchEngine] {fetcher_type.value} 失败(尝试{attempt+1}): {last_error}")
                    time.sleep(self.config.backoff_base ** attempt)

            logger.warning(f"[FetchEngine] 升级到下一级Fetcher")

        return FetchResult(
            url=url, platform=platform, fetcher_type=FetcherType.DYNAMIC,
            page_html="", http_status=0, retries=0, fetch_time_ms=0,
            error=f"3级抓取全部失�? {last_error}",
        )

    def _build_strategies(self, url: str, rule):
        strategies = []
        strategies.append((FetcherType.FETCHER, lambda u: self._fetch_with_fetcher(u)))
        if rule.needs_stealth:
            strategies.append((FetcherType.STEALTHY, lambda u: self._fetch_with_stealthy(u)))
        if rule.needs_dynamic:
            strategies.append((FetcherType.DYNAMIC, lambda u: self._fetch_with_dynamic(u)))
        return strategies

    def _fetch_with_fetcher(self, url: str) -> tuple[str, int]:
        try:
            from scrapling.fetchers import Fetcher
            page = Fetcher.get(
                url,
                impersonate=self.config.impersonate,
                stealthy_headers=True,
                timeout=self.config.timeout_default,
            )
            return page.html, 200
        except ImportError:
            import requests
            headers = {"User-Agent": self.config.user_agent}
            resp = requests.get(url, headers=headers, timeout=self.config.timeout_default)
            resp.raise_for_status()
            return resp.text, resp.status_code

    def _fetch_with_stealthy(self, url: str) -> tuple[str, int]:
        try:
            from scrapling.fetchers import StealthyFetcher
            page = StealthyFetcher.fetch(
                url,
                headless=self.config.headless,
                solve_cloudflare=True,
                network_idle=True,
                timeout=self.config.timeout_stealthy,
            )
            return page.html, 200
        except ImportError:
            import requests
            headers = {"User-Agent": self.config.user_agent}
            resp = requests.get(url, headers=headers, timeout=self.config.timeout_stealthy)
            resp.raise_for_status()
            return resp.text, resp.status_code

    def _fetch_with_dynamic(self, url: str) -> tuple[str, int]:
        try:
            from scrapling.fetchers import DynamicFetcher
            page = DynamicFetcher.fetch(
                url,
                headless=self.config.headless,
                network_idle=True,
                timeout=self.config.timeout_dynamic,
            )
            return page.html, 200
        except ImportError:
            import requests
            headers = {"User-Agent": self.config.user_agent}
            resp = requests.get(url, headers=headers, timeout=self.config.timeout_dynamic)
            resp.raise_for_status()
            return resp.text, resp.status_code

from src.core.scraping_rules import PLATFORM_RULES
