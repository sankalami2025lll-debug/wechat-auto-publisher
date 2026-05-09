"""
文章数据模型 - Article Schema

定义文章抓取全链路的结构化数据类型
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass, field


class PlatformType(str, Enum):
    WECHAT = "wechat"
    ZHIHU_ARTICLE = "zhihu_article"
    ZHIHU_ANSWER = "zhihu_answer"
    TOUTIAO = "toutiao"
    SOHU = "sohu"
    BAIDU_BAIJIA = "baidu_baijia"
    WANGYI = "wangyi"
    SINA = "sina"
    PENGPAI = "pengpai"
    TEN_NEWS = "tencent_news"
    UNKNOWN = "unknown"


class FetcherType(str, Enum):
    FETCHER = "Fetcher"
    STEALTHY = "StealthyFetcher"
    DYNAMIC = "DynamicFetcher"


class ScrapeStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    LOGIN_REQUIRED = "login_required"
    PAYWALL = "paywall"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"


@dataclass
class ImageItem:
    url: str
    alt: str = ""
    width: int = 0
    height: int = 0
    local_path: str = ""


@dataclass
class ArticleData:
    url: str
    platform: PlatformType = PlatformType.UNKNOWN
    title: str = ""
    author: str = ""
    publish_time: str = ""
    content: str = ""
    content_html: str = ""
    summary: str = ""
    images: list[ImageItem] = field(default_factory=list)
    status: ScrapeStatus = ScrapeStatus.SUCCESS
    fetcher_used: FetcherType = FetcherType.FETCHER
    confidence: float = 0.0
    fetch_time_ms: int = 0
    retries: int = 0
    warnings: list[str] = field(default_factory=list)
    error_message: str = ""
    cached: bool = False


@dataclass
class PlatformRule:
    platform: PlatformType
    title_selectors: list[str]
    content_selectors: list[str]
    author_selectors: list[str]
    time_selectors: list[str]
    needs_dynamic: bool = False
    needs_stealth: bool = False
    noise_selectors: list[str] = field(default_factory=list)


@dataclass
class FetchResult:
    url: str
    platform: PlatformType
    fetcher_type: FetcherType
    page_html: str
    http_status: int
    retries: int
    fetch_time_ms: int
    error: str = ""


@dataclass
class ScrapeConfig:
    timeout_default: int = 15
    timeout_dynamic: int = 30
    timeout_stealthy: int = 25
    max_retries_per_level: int = 1
    total_max_retries: int = 3
    backoff_base: float = 1.5
    rate_limit_rpm: int = 30
    delay_between_ms: int = 2000
    cache_enabled: bool = True
    cache_ttl: int = 3600
    cache_max_size: int = 500
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    impersonate: str = "chrome"
    headless: bool = True
    download_images: bool = False
    max_image_count: int = 20
    min_image_size: int = 50
    output_markdown: bool = True
    include_image_list: bool = True
