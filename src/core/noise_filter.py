"""
噪声过滤器 - 从正文HTML中移除广告、导航、评论、侧栏等噪声
"""

from bs4 import BeautifulSoup

from src.core.scraping_rules import GLOBAL_NOISE_SELECTORS, NOISE_CLASS_KEYWORDS


class NoiseFilter:

    WECHAT_CLASS_PATTERNS = [
        "reward_area", "like_comment", "qr_code", "rich_media_area_extra",
        "img_loading", "js_pc_qr_code",
    ]

    ZHIHU_CLASS_PATTERNS = [
        "CornerButtons", "Reward", "Post-Actions", "Post-SideActions",
        "Post-NormalSub", "ContentItem-actions", "AnswerItem-actions",
        "AnswerItem-voteBar", "AuthorFollowButton", "MCNLinkCard",
    ]

    TOUTIAO_CLASS_PATTERNS = [
        "ad-item", "feed-card", "article-ext-info", "comment-list",
        "recommend-list", "related-articles",
    ]

    PATTERN_MAP = {
        "wechat": WECHAT_CLASS_PATTERNS,
        "zhihu": ZHIHU_CLASS_PATTERNS,
        "toutiao": TOUTIAO_CLASS_PATTERNS,
    }

    def filter(self, html: str, platform: str = "") -> str:
        if not html:
            return ""
        soup = BeautifulSoup(html, "lxml")

        self._remove_by_selectors(soup)
        self._remove_by_class_keywords(soup)
        self._remove_empty_tags(soup)
        self._remove_platform_noise(soup, platform)
        self._remove_scripts_and_styles(soup)

        return str(soup)

    def _remove_by_selectors(self, soup: BeautifulSoup):
        for selector in GLOBAL_NOISE_SELECTORS:
            try:
                for el in soup.select(selector):
                    el.decompose()
            except Exception:
                pass

    def _remove_by_class_keywords(self, soup: BeautifulSoup):
        for el in soup.find_all(True):
            classes = el.get("class", [])
            el_id = el.get("id", "")
            combined = " ".join(classes) + " " + el_id
            combined_lower = combined.lower()

            if any(kw in combined_lower for kw in NOISE_CLASS_KEYWORDS):
                el.decompose()

    def _remove_empty_tags(self, soup: BeautifulSoup):
        empty_tags = []
        for el in soup.find_all(["div", "p", "span"]):
            text = el.get_text(strip=True)
            if not text and not el.find("img") and not el.find("video"):
                empty_tags.append(el)
        for el in empty_tags:
            try:
                el.decompose()
            except Exception:
                pass

    def _remove_platform_noise(self, soup: BeautifulSoup, platform: str):
        patterns = self.PATTERN_MAP.get(platform, [])
        for el in soup.find_all(True):
            classes = " ".join(el.get("class", []))
            el_id = el.get("id", "")
            combined = (classes + " " + el_id).lower()
            if any(p.lower() in combined for p in patterns):
                el.decompose()

    def _remove_scripts_and_styles(self, soup: BeautifulSoup):
        for tag in soup.find_all(["script", "style", "link", "meta", "noscript", "iframe"]):
            tag.decompose()
