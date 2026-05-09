"""
抓取规则库 - 平台选择器 + 噪声过滤规则

定义各主流内容平台的正文字段定位选择器和噪声元素过滤规则
"""

from src.core.article_schema import PlatformRule, PlatformType

PLATFORM_RULES: dict[PlatformType, PlatformRule] = {
    PlatformType.WECHAT: PlatformRule(
        platform=PlatformType.WECHAT,
        title_selectors=[
            "#activity-name",
            ".rich_media_title",
            "h1.rich_media_title",
        ],
        content_selectors=[
            "#js_content",
            ".rich_media_content",
            ".rich_media_area_primary_inner",
        ],
        author_selectors=[
            "#js_name",
            ".rich_media_meta_text",
            ".profile_nickname",
        ],
        time_selectors=[
            "#publish_time",
            ".rich_media_meta_text[data-v-*]",
            "#meta_content > .rich_media_meta_text:last-child",
        ],
        needs_dynamic=True,
        noise_selectors=[
            ".rich_media_area_extra",
            ".reward_area",
            ".like_comment_wrp",
            "#js_pc_qr_code",
            ".qr_code_pc_outer",
        ],
    ),
    PlatformType.ZHIHU_ARTICLE: PlatformRule(
        platform=PlatformType.ZHIHU_ARTICLE,
        title_selectors=[
            ".Post-Title",
            "h1.Post-Title",
            ".Article-Title",
        ],
        content_selectors=[
            ".Post-RichText",
            ".RichText",
            "article.Post-content",
        ],
        author_selectors=[
            ".AuthorInfo-name",
            ".Post-Author .AuthorInfo .name",
        ],
        time_selectors=[
            ".ContentItem-time",
            ".Post-Header .ContentItem-time",
            "time",
        ],
        needs_stealth=True,
        noise_selectors=[
            ".Post-SideActions",
            ".Post-Actions",
            ".Post-NormalSub",
            ".CornerButtons",
            ".Reward",
            ".Post-AuthorFollowButton",
        ],
    ),
    PlatformType.ZHIHU_ANSWER: PlatformRule(
        platform=PlatformType.ZHIHU_ANSWER,
        title_selectors=[
            "h1.QuestionHeader-title",
            ".QuestionHeader-title",
        ],
        content_selectors=[
            ".RichContent-inner",
            ".AnswerItem .RichContent",
            ".RichContent",
        ],
        author_selectors=[
            ".AuthorInfo-name",
            ".AnswerItem-authorInfo .name",
        ],
        time_selectors=[
            ".ContentItem-time",
            ".AnswerItem-time",
        ],
        needs_stealth=True,
        noise_selectors=[
            ".AnswerItem-actions",
            ".AnswerItem-voteBar",
            ".AnswerItem-extraInfo",
            ".Reward",
        ],
    ),
    PlatformType.TOUTIAO: PlatformRule(
        platform=PlatformType.TOUTIAO,
        title_selectors=[
            "h1.article-title",
            ".article-title",
            "h1.article-header-title",
        ],
        content_selectors=[
            ".article-content",
            "article",
            ".article-body",
        ],
        author_selectors=[
            ".article-info .name",
            ".author-name",
            ".article-meta .author",
        ],
        time_selectors=[
            ".article-info .time",
            ".article-meta .time",
            ".publish-time",
        ],
        needs_dynamic=True,
        noise_selectors=[
            ".ad-item",
            ".feed-card-article-l",
            ".article-ext-info",
            ".comment-list",
            ".recommend-list",
            ".related-articles",
        ],
    ),
    PlatformType.SOHU: PlatformRule(
        platform=PlatformType.SOHU,
        title_selectors=[
            ".article-title",
            "h1",
            ".text-title",
        ],
        content_selectors=[
            ".article",
            "article",
            ".article-container",
        ],
        author_selectors=[
            ".user-name",
            ".author-name",
            ".article-editor",
        ],
        time_selectors=[
            ".time",
            ".article-time",
            ".pub-date",
        ],
        noise_selectors=[
            ".article-banner",
            ".recommend-list",
            ".comment-area",
            ".article-bottom-ad",
        ],
    ),
    PlatformType.BAIDU_BAIJIA: PlatformRule(
        platform=PlatformType.BAIDU_BAIJIA,
        title_selectors=[
            ".index-module_articleTitle",
            ".article-title",
            "h1",
        ],
        content_selectors=[
            ".index-module_articleContent",
            ".article-content",
            "article",
        ],
        author_selectors=[
            ".author-name",
            ".index-module_userInfo",
        ],
        time_selectors=[
            ".index-module_date",
            ".article-date",
            ".publish-time",
        ],
        noise_selectors=[
            ".article-bottom-bar",
            ".recommend-wrapper",
            ".comment-container",
            ".ad-space",
        ],
    ),
    PlatformType.WANGYI: PlatformRule(
        platform=PlatformType.WANGYI,
        title_selectors=[
            ".post_title",
            ".article_title",
            "h1",
        ],
        content_selectors=[
            ".post_body",
            ".article_body",
            ".post-content",
        ],
        author_selectors=[
            ".post_info .post_author",
            ".article-info .author",
        ],
        time_selectors=[
            ".post_info .post_time",
            ".article-info .time",
        ],
        noise_selectors=[
            ".post_recommend",
            ".post_comment",
            ".article-sidebar",
        ],
    ),
    PlatformType.SINA: PlatformRule(
        platform=PlatformType.SINA,
        title_selectors=[
            "h1.main-title",
            ".article-title",
            "h1",
        ],
        content_selectors=[
            ".article-content",
            ".art_p",
            "#artibody",
        ],
        author_selectors=[
            ".article-editor",
            ".source",
            "meta[name=\"author\"]",
        ],
        time_selectors=[
            ".article-time",
            ".date",
            "meta[name=\"pubdate\"]",
        ],
        noise_selectors=[
            ".article-related",
            ".article-bottom-ad",
            ".comment-wrapper",
        ],
    ),
    PlatformType.PENGPAI: PlatformRule(
        platform=PlatformType.PENGPAI,
        title_selectors=[
            ".news_txt h1",
            ".news_title",
            "h1",
        ],
        content_selectors=[
            ".news_txt",
            ".news_content",
            ".article-content",
        ],
        author_selectors=[
            ".news_about .author",
            ".news_editor",
        ],
        time_selectors=[
            ".news_about .time",
            ".news_date",
        ],
        noise_selectors=[
            ".news_recommend",
            ".news_comment",
            ".news_related",
        ],
    ),
    PlatformType.TEN_NEWS: PlatformRule(
        platform=PlatformType.TEN_NEWS,
        title_selectors=[
            "h1",
            ".article-title",
            ".title",
        ],
        content_selectors=[
            ".content-article",
            ".article-content",
            "#article-content",
        ],
        author_selectors=[
            ".source",
            ".author",
            "meta[name=\"author\"]",
        ],
        time_selectors=[
            ".time",
            ".date",
            "meta[name=\"pubdate\"]",
        ],
        noise_selectors=[
            ".article-related",
            ".comment-box",
            ".recommend",
        ],
    ),
    PlatformType.UNKNOWN: PlatformRule(
        platform=PlatformType.UNKNOWN,
        title_selectors=[
            "h1",
            ".title",
            "meta[property=\"og:title\"]",
        ],
        content_selectors=[
            "article",
            "main",
            ".content",
            ".article",
            ".post-body",
            ".post-content",
        ],
        author_selectors=[
            "meta[name=\"author\"]",
            ".author",
            ".byline",
            "a[rel=\"author\"]",
        ],
        time_selectors=[
            "meta[name=\"pubdate\"]",
            "meta[property=\"article:published_time\"]",
            "time",
            ".date",
            ".publish-date",
        ],
    ),
}

GLOBAL_NOISE_SELECTORS = [
    "nav", "header[role=\"banner\"]", ".navbar", ".nav-bar",
    "footer", ".footer", ".copyright",
    "aside", ".sidebar", ".side-bar",
    "[class*=\"ad\"]", "[id*=\"ad\"]",
    "[class*=\"advert\"]", ".banner-ad", ".promo", ".advertisement",
    ".share", ".social", ".social-share",
    ".comment", ".comments", "#comments", ".discuss", "[class*=\"reply\"]",
    ".related", ".recommend", ".hot-news", "[class*=\"popular\"]",
    "script", "style", "link[rel=\"stylesheet\"]",
    "iframe", "noscript",
    ".qrcode", ".qr-code",
    ".modal", ".popup", ".overlay",
    "[role=\"complementary\"]",
    ".follow-btn", ".subscribe",
]

NOISE_CLASS_KEYWORDS = [
    "ad", "advert", "banner", "promo", "sponsor",
    "nav", "navbar", "menu", "navigation",
    "footer", "copyright", "legal",
    "sidebar", "side-bar", "aside",
    "comment", "reply", "discuss",
    "share", "social", "follow", "subscribe",
    "related", "recommend", "popular", "hot",
    "popup", "modal", "overlay",
    "qrcode", "qr-code", "wechat",
    "pagination", "pager",
]

SMALL_IMAGE_PATTERNS = ["pixel", "1x1", "track", "icon", "emoji", "avatar", "logo"]
