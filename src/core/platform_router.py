"""
URL平台识别器 - Platform Router

根据URL域名/路径特征自动识别内容平台类型
"""

import re
from urllib.parse import urlparse

from src.core.article_schema import PlatformType

ROUTE_PATTERNS: list[tuple[re.Pattern, PlatformType]] = [
    (re.compile(r"mp\.weixin\.qq\.com/s/"), PlatformType.WECHAT),
    (re.compile(r"zhuanlan\.zhihu\.com/p/"), PlatformType.ZHIHU_ARTICLE),
    (re.compile(r"zhihu\.com/question/\d+/answer/\d+"), PlatformType.ZHIHU_ANSWER),
    (re.compile(r"zhihu\.com/question/\d+"), PlatformType.ZHIHU_ANSWER),
    (re.compile(r"toutiao\.com/article/"), PlatformType.TOUTIAO),
    (re.compile(r"toutiao\.com/a/"), PlatformType.TOUTIAO),
    (re.compile(r"sohu\.com/a/"), PlatformType.SOHU),
    (re.compile(r"baijiahao\.baidu\.com/s"), PlatformType.BAIDU_BAIJIA),
    (re.compile(r"163\.com/dy/article/"), PlatformType.WANGYI),
    (re.compile(r"163\.com/news/"), PlatformType.WANGYI),
    (re.compile(r"news\.sina\.com\.cn"), PlatformType.SINA),
    (re.compile(r"thepaper\.cn/newsDetail"), PlatformType.PENGPAI),
    (re.compile(r"new\.qq\.com/rain/a/"), PlatformType.TEN_NEWS),
]


class PlatformRouter:

    @staticmethod
    def identify(url: str) -> PlatformType:
        for pattern, platform in ROUTE_PATTERNS:
            if pattern.search(url):
                return platform
        return PlatformType.UNKNOWN

    @staticmethod
    def get_rule(url_or_platform: PlatformType | str):
        from src.core.scraping_rules import PLATFORM_RULES as RULES
        if isinstance(url_or_platform, PlatformType):
            platform = url_or_platform
        else:
            platform = PlatformRouter.identify(url_or_platform)
        return RULES.get(platform, RULES[PlatformType.UNKNOWN])

    @staticmethod
    def validate_url(url: str) -> tuple[bool, str]:
        if not url or not url.strip():
            return False, "URL为空"
        try:
            parsed = urlparse(url.strip())
        except Exception:
            return False, f"URL解析失败: {url}"
        if parsed.scheme not in ("http", "https"):
            return False, f"不支持的协议: {parsed.scheme}，仅支持http/https"
        if not parsed.netloc:
            return False, "URL缺少域名"
        return True, ""
