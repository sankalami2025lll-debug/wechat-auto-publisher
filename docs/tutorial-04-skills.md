## 技能模块：图片素材

这个模块负责从 Unsplash、Pexels、Pixabay 三个无版权图库搜索和下载图片。

创建 `skills\copyright_free_images\__init__.py`：

```python
"""
无版权商用图片素材技能模块
多渠道无版权图片搜索与下载：Unsplash、Pexels、Pixabay
"""

import os
import requests
from typing import Optional
from dataclasses import dataclass, field
from urllib.parse import quote_plus


@dataclass
class ImageResult:
    """图片搜索结果"""
    id: str
    url: str              # 预览图URL
    thumb_url: str        # 缩略图URL
    download_url: str     # 高清原图URL
    width: int
    height: int
    photographer: str = ""
    description: str = ""
    source: str = "unsplash"


class UnsplashClient:
    """Unsplash API 客户端"""
    BASE_URL = "https://api.unsplash.com"

    def __init__(self, access_key: str = ""):
        self.access_key = access_key

    def search(self, query: str, per_page: int = 10) -> list[ImageResult]:
        if not self.access_key:
            return []
        url = f"{self.BASE_URL}/search/photos"
        headers = {"Authorization": f"Client-ID {self.access_key}"}
        params = {"query": query, "per_page": per_page, "orientation": "landscape"}
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            data = resp.json()
            results = []
            for item in data.get("results", []):
                results.append(ImageResult(
                    id=item["id"],
                    url=item["urls"]["regular"],
                    thumb_url=item["urls"]["thumb"],
                    download_url=item["urls"]["full"],
                    width=item.get("width", 0),
                    height=item.get("height", 0),
                    photographer=item["user"]["name"],
                    description=item.get("description") or item.get("alt_description", ""),
                    source="unsplash",
                ))
            return results
        except Exception as e:
            print(f"Unsplash搜索失败: {e}")
            return []

    def download(self, image: ImageResult, save_dir: str) -> Optional[str]:
        """下载图片到本地"""
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, f"unsplash_{image.id}.jpg")
        try:
            resp = requests.get(image.download_url, timeout=30)
            if resp.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                return filepath
        except Exception as e:
            print(f"下载失败: {e}")
        return None


class PexelsClient:
    """Pexels API 客户端"""
    BASE_URL = "https://api.pexels.com/v1"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def search(self, query: str, per_page: int = 10) -> list[ImageResult]:
        if not self.api_key:
            return []
        headers = {"Authorization": self.api_key}
        params = {"query": query, "per_page": per_page, "orientation": "landscape"}
        try:
            resp = requests.get(f"{self.BASE_URL}/search", headers=headers, params=params, timeout=15)
            data = resp.json()
            results = []
            for item in data.get("photos", []):
                results.append(ImageResult(
                    id=str(item["id"]),
                    url=item["src"]["large"],
                    thumb_url=item["src"]["small"],
                    download_url=item["src"]["original"],
                    width=item.get("width", 0),
                    height=item.get("height", 0),
                    photographer=item["photographer"],
                    description=item.get("alt", ""),
                    source="pexels",
                ))
            return results
        except Exception as e:
            print(f"Pexels搜索失败: {e}")
            return []

    def download(self, image: ImageResult, save_dir: str) -> Optional[str]:
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, f"pexels_{image.id}.jpg")
        try:
            resp = requests.get(image.download_url, timeout=30)
            if resp.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                return filepath
        except Exception as e:
            print(f"下载失败: {e}")
        return None


class PixabayClient:
    """Pixabay API 客户端"""
    BASE_URL = "https://pixabay.com/api"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def search(self, query: str, per_page: int = 10) -> list[ImageResult]:
        if not self.api_key:
            return []
        params = {
            "key": self.api_key, "q": query,
            "per_page": per_page, "orientation": "horizontal",
            "safesearch": "true",
        }
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=15)
            data = resp.json()
            results = []
            for item in data.get("hits", []):
                results.append(ImageResult(
                    id=str(item["id"]),
                    url=item["webformatURL"],
                    thumb_url=item["previewURL"],
                    download_url=item["largeImageURL"],
                    width=item.get("imageWidth", 0),
                    height=item.get("imageHeight", 0),
                    photographer=item.get("user", ""),
                    description=", ".join(filter(None, item.get("tags", "").split(", ")[:5])),
                    source="pixabay",
                ))
            return results
        except Exception as e:
            print(f"Pixabay搜索失败: {e}")
            return []

    def download(self, image: ImageResult, save_dir: str) -> Optional[str]:
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, f"pixabay_{image.id}.jpg")
        try:
            resp = requests.get(image.download_url, timeout=30)
            if resp.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                return filepath
        except Exception as e:
            print(f"下载失败: {e}")
        return None


class CopyrightFreeImageSkills:
    """无版权图片技能 - 统一入口"""

    def __init__(self, unsplash_key: str = "", pexels_key: str = "",
                 pixabay_key: str = ""):
        self.unsplash = UnsplashClient(unsplash_key)
        self.pexels = PexelsClient(pexels_key)
        self.pixabay = PixabayClient(pixabay_key)

    def search_all(self, query: str, per_page: int = 30,
                   min_width: int = 800) -> list[ImageResult]:
        """跨平台搜索（聚合三个图库的结果）"""
        all_results = []

        # 从每个渠道搜索
        for client in [self.unsplash, self.pexels, self.pixabay]:
            try:
                results = client.search(query, per_page=min(per_page, 10))
                all_results.extend(results)
            except Exception:
                continue

        # 按最小宽度筛选
        if min_width:
            all_results = [r for r in all_results if r.width >= min_width]

        return all_results

    def download_best(self, images: list[ImageResult], save_dir: str,
                      max_count: int = 5) -> list[str]:
        """批量下载最好的几张图片"""
        downloaded = []
        for img in images[:max_count]:
            path = None
            if img.source == "unsplash":
                path = self.unsplash.download(img, save_dir)
            elif img.source == "pexels":
                path = self.pexels.download(img, save_dir)
            elif img.source == "pixabay":
                path = self.pixabay.download(img, save_dir)

            if path:
                downloaded.append(path)
        return downloaded

    def status(self) -> dict:
        return {
            "skill": "copyright-free-images",
            "version": "1.0.0",
            "channels": {
                "unsplash": bool(self.unsplash.access_key),
                "pexels": bool(self.pexels.api_key),
                "pixabay": bool(self.pixabay.api_key),
            },
            "status": "ready",
        }
```

> ⚠️ **小提示**：如果你不想注册三个图库的API，注册一个就够了。代码会自动跳过未配置的图库。

---

## 技能模块：AI绘图

这个模块使用 OpenAI 的 DALL-E 或兼容接口来生成文章封面图。

创建 `skills\ai_drawing\__init__.py`：

```python
"""
AI绘图技能模块 - 使用DALL-E生成图片和封面图
"""

import os
import time
import requests
import base64
from typing import Optional
from dataclasses import dataclass


@dataclass
class GeneratedImage:
    """生成的图片"""
    url: str = ""
    b64_json: str = ""
    revised_prompt: str = ""
    local_path: str = ""
    model: str = "dall-e-3"
    size: str = "1024x1024"


class DalleClient:
    """DALL-E API 客户端"""

    def __init__(self, api_key: str = "", base_url: str = "https://api.deepseek.com/v1"):
        self.api_key = api_key
        self.base_url = base_url

    def generate(self, prompt: str, model: str = "dall-e-3",
                 size: str = "1024x1024", quality: str = "standard",
                 style: str = "vivid") -> list[GeneratedImage]:
        """调用DALL-E生成图片"""
        url = f"{self.base_url}/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": quality,
            "style": style,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        if resp.status_code != 200:
            raise Exception(f"DALL-E API错误: {resp.status_code} - {resp.text}")

        data = resp.json()
        results = []
        for item in data.get("data", []):
            results.append(GeneratedImage(
                url=item.get("url", ""),
                b64_json=item.get("b64_json", ""),
                revised_prompt=item.get("revised_prompt", ""),
                model=model,
                size=size,
            ))
        return results

    def generate_and_save(self, prompt: str, save_dir: str,
                          filename: str = "", **kwargs) -> list[GeneratedImage]:
        """生成并保存到本地"""
        images = self.generate(prompt, **kwargs)
        os.makedirs(save_dir, exist_ok=True)
        for i, img in enumerate(images):
            fname = filename or f"dalle_{int(time.time())}_{i}.png"
            filepath = os.path.join(save_dir, fname)
            if img.url:
                img_data = requests.get(img.url, timeout=30).content
                with open(filepath, "wb") as f:
                    f.write(img_data)
                img.local_path = filepath
            elif img.b64_json:
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(img.b64_json))
                img.local_path = filepath
        return images


class CoverImageGenerator:
    """封面图生成器 - 专为微信公众号优化"""

    def __init__(self, dalle_client: DalleClient):
        self.dalle = dalle_client

    def generate_cover(self, title: str, style: str = "professional",
                       save_dir: str = "data/covers") -> Optional[GeneratedImage]:
        """根据文章标题自动生成封面图"""
        prompts = {
            "professional": (
                f"为标题为「{title}」的专业文章生成封面图。"
                "现代简约风格，商务配色（蓝/白/灰），几何图案装饰，"
                "适合微信公号封面。2.35:1比例，无水印，无文字。"
                "A professional cover image for a WeChat article. "
                "Modern minimalist style, business colors. No text, no watermark."
            ),
            "tech": (
                f"A futuristic tech-themed cover image for article '{title}'. "
                "Dark theme with neon accents, circuit patterns. "
                "2.35:1 aspect ratio, no text, no watermark."
            ),
            "creative": (
                f"为标题为「{title}」的创意文章生成封面图。"
                "色彩鲜艳，创意构图，插画风格。2.35:1比例，无水印，无文字。"
            ),
        }

        prompt = prompts.get(style, prompts["professional"])
        try:
            images = self.dalle.generate_and_save(
                prompt=prompt, save_dir=save_dir,
                filename=f"cover_{int(time.time())}.png",
                size="1792x1024",  # 微信封面比例接近2.35:1
                quality="standard",
                style="vivid",
            )
            return images[0] if images else None
        except Exception as e:
            print(f"封面图生成失败: {e}")
            return None


class AIDrawingSkills:
    """AI绘图技能 - 统一入口"""

    def __init__(self, api_key: str = "",
                 api_base: str = "https://api.deepseek.com/v1"):
        self.dalle = DalleClient(api_key=api_key, base_url=api_base)
        self.cover_generator = CoverImageGenerator(self.dalle)

    def text_to_image(self, prompt: str, **kwargs) -> list[GeneratedImage]:
        """文生图"""
        return self.dalle.generate(prompt, **kwargs)

    def generate_article_cover(self, title: str, style: str = "professional",
                               save_dir: str = "data/covers") -> Optional[GeneratedImage]:
        """根据标题生成文章封面"""
        return self.cover_generator.generate_cover(title, style, save_dir)

    def status(self) -> dict:
        return {
            "skill": "ai-drawing",
            "version": "1.0.0",
            "models": ["dall-e-2", "dall-e-3"],
            "capabilities": ["文生图", "封面图生成", "多风格支持"],
            "status": "ready" if self.dalle.api_key else "pending_config",
        }
```

> ⚠️ **重要说明**：
> - DALL-E 是 OpenAI 的图片生成服务，如果你的 API Key 是 DeepSeek 或 Kimi 的，这个模块**不会生效**（因为这些模型不支持图片生成）。
> - **推荐替代方案**：直接用前面"图片素材"模块从 Unsplash/Pexels/Pixabay 免费图库搜索封面图，完全免费且版权无忧。本教程的端到端发布流程也是用免费图库下载封面图。
> - 如果你确实想用 AI 生成封面图，可以另外申请一个 OpenAI 的 API Key 并在代码中单独配置。

---

## 技能模块：内容合规检查

这个模块对改写后的文章进行合规检查，避免发布后触犯微信的内容规则。

创建 `skills\content_compliance\__init__.py`：

```python
"""
内容合规校验技能模块
敏感词检测 + 广告法检查 + AI内容安全审核
"""

import re
import json
import requests
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class ComplianceResult:
    """合规检查结果"""
    passed: bool
    score: float = 100.0
    violations: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    risk_level: str = "none"   # none / low / medium / high


class SensitiveWordDetector:
    """敏感词检测器（规则匹配）"""

    # 微信常见的违规内容正则模式
    SENSITIVE_PATTERNS = [
        (r"(赌博|博彩|赌场|六合彩|时时彩)", "赌博相关内容"),
        (r"(色情|黄色|成人|激情|一夜情|约炮)", "色情低俗内容"),
        (r"(贩卖|出售.*枪支|购买.*弹药)", "违禁物品"),
        (r"(吸毒|毒品|大麻|海洛因|冰毒|摇头丸)", "毒品相关内容"),
        (r"(传销|拉人头|下线|金字塔)", "传销内容"),
        (r"(高利贷|裸贷|校园贷|套路贷)", "非法借贷"),
        (r"(代孕|试管婴儿.*包成功)", "代孕相关"),
        (r"(翻墙|VPN.*免费|科学上网.*免费)", "网络工具违规推广"),
    ]

    # 广告法违禁词
    AD_LAW_PATTERNS = [
        (r"(最好|第一|唯一|最.*的|顶级|极品|国家级|世界级)", "广告法禁用极限词"),
        (r"(100%|百分百|绝对|彻底|完全.*有效)", "广告法禁用绝对化承诺"),
        (r"(永久|终身|永不|永远)", "广告法禁用时间无限词"),
        (r"(包治|根治|治愈|康复.*保证)", "医疗广告违规用语"),
        (r"(无效退款|保证有效|必有效|一定有效)", "疗效保证违规"),
    ]

    def detect(self, content: str) -> list[str]:
        """检测违规内容"""
        violations = []
        for pattern, desc in self.SENSITIVE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(f"[敏感内容] {desc}")
        for pattern, desc in self.AD_LAW_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(f"[广告法] {desc}")
        return violations


class AIContentChecker:
    """AI内容安全审核器（调用LLM进行深度审核）"""

    CHECK_PROMPT = """你是一个中文内容安全审核专家。请审查以下文章是否存在违规问题。

审查维度：
1. 政治敏感：是否涉及敏感政治话题、领导人负面言论
2. 色情低俗：是否包含性暗示、低俗内容
3. 暴力恐怖：是否包含暴力、血腥、恐怖主义内容
4. 谣言虚假：是否传播未经证实的谣言
5. 广告违规：是否违反广告法（极限词、虚假承诺）
6. 侵权风险：是否涉及抄袭、侵犯知识产权

文章内容：
---
{content}
---

请以JSON格式返回：
{{"passed": true/false, "violations": ["违规项"], "risk_level": "none/low/medium/high", "suggestions": ["修改建议"]}}"""

    def __init__(self, api_key: str = "", base_url: str = "https://api.deepseek.com/v1",
                 model: str = "deepseek-chat"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def check(self, content: str, max_length: int = 4000) -> ComplianceResult:
        if not self.api_key:
            return ComplianceResult(passed=True, score=80.0, risk_level="low",
                                    suggestions=["AI审核未配置API密钥，仅进行规则检查"])

        truncated = content[:max_length]
        prompt = self.CHECK_PROMPT.format(content=truncated)
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1000,
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code != 200:
                return ComplianceResult(passed=True, score=70.0, risk_level="low",
                                        suggestions=["AI审核服务暂时不可用"])
            data = resp.json()
            result = json.loads(data["choices"][0]["message"]["content"])
            return ComplianceResult(
                passed=result.get("passed", True),
                score=100.0 if result.get("passed") else 50.0,
                violations=result.get("violations", []),
                suggestions=result.get("suggestions", []),
                risk_level=result.get("risk_level", "none"),
            )
        except Exception as e:
            return ComplianceResult(passed=True, score=70.0, risk_level="low",
                                    suggestions=[f"AI审核异常: {str(e)}"])


class ContentComplianceSkills:
    """内容合规校验技能 - 统一入口"""

    def __init__(self, ai_api_key: str = "",
                 ai_base_url: str = "https://api.deepseek.com/v1",
                 ai_model: str = "deepseek-chat"):
        self.sensitive_detector = SensitiveWordDetector()
        self.ai_checker = AIContentChecker(
            api_key=ai_api_key, base_url=ai_base_url, model=ai_model
        )

    def quick_check(self, content: str) -> ComplianceResult:
        """快速检查（仅规则匹配，不调用AI）"""
        violations = self.sensitive_detector.detect(content)
        if violations:
            return ComplianceResult(
                passed=False,
                score=max(0, 100 - len(violations) * 15),
                violations=violations,
                suggestions=["请修改以上违规内容后重新提交"],
                risk_level="high" if len(violations) >= 3 else "medium",
            )
        return ComplianceResult(passed=True, score=100.0, risk_level="none")

    def full_check(self, content: str) -> ComplianceResult:
        """完整检查（规则 + AI深度审核）"""
        rule_result = self.quick_check(content)
        if not rule_result.passed:
            return rule_result

        ai_result = self.ai_checker.check(content)
        all_violations = rule_result.violations + ai_result.violations
        all_suggestions = rule_result.suggestions + ai_result.suggestions

        return ComplianceResult(
            passed=ai_result.passed and rule_result.passed,
            score=min(rule_result.score, ai_result.score),
            violations=all_violations,
            suggestions=all_suggestions,
            risk_level=ai_result.risk_level if ai_result.risk_level != "none" else rule_result.risk_level,
        )

    def check_title(self, title: str) -> ComplianceResult:
        """标题合规检查"""
        violations = self.sensitive_detector.detect(title)
        if violations:
            return ComplianceResult(
                passed=False, score=80.0, violations=violations,
                suggestions=["标题存在违规用词，请修改"],
                risk_level="medium",
            )
        return ComplianceResult(passed=True, score=100.0, risk_level="none")

    def status(self) -> dict:
        return {
            "skill": "content-compliance",
            "version": "1.0.0",
            "checkers": {
                "sensitive_word_detector": True,
                "ad_law_checker": True,
                "ai_content_checker": bool(self.ai_checker.api_key),
            },
            "status": "ready",
        }
```

---

## 技能模块：微信生态

这是**最关键的模块**，负责与微信公众号后台 API 进行交互，包括：获取 Access Token、上传图片素材、创建草稿、发布文章。

创建 `skills\wechat_ecosystem\__init__.py`：

```python
"""
微信生态全量技能模块
微信公众号全生命周期管理：素材管理、草稿创建/发布、Token管理
"""

import requests
import time
from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class WeChatConfig:
    """微信配置"""
    app_id: str = ""
    app_secret: str = ""
    base_url: str = "https://api.weixin.qq.com"


class WeChatTokenManager:
    """Access Token 管理器 - 自动获取、缓存、刷新

    微信的Access Token有效期2小时，这个管理器会自动缓存并在过期前刷新。
    """

    def __init__(self, config: WeChatConfig):
        self.config = config
        self._token: Optional[str] = None
        self._expires_at: float = 0

    def get_token(self) -> str:
        """获取有效的Access Token"""
        # 如果Token存在且距离过期还有5分钟以上，直接返回
        if self._token and time.time() < self._expires_at - 300:
            return self._token
        self._refresh_token()
        return self._token

    def _refresh_token(self) -> None:
        """刷新Access Token"""
        url = f"{self.config.base_url}/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.config.app_id,
            "secret": self.config.app_secret,
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if "access_token" in data:
            self._token = data["access_token"]
            self._expires_at = time.time() + data.get("expires_in", 7200)
            print(f"✅ Token获取成功，有效期{data.get('expires_in', 7200)}秒")
        else:
            raise Exception(f"获取Access Token失败: {data}")


class WeChatMaterialManager:
    """素材管理器 - 上传图片/获取素材列表/删除素材"""

    def __init__(self, token_manager: WeChatTokenManager, config: WeChatConfig):
        self.token_manager = token_manager
        self.config = config

    def upload_image(self, file_path: str) -> dict:
        """上传图片为永久素材，返回 media_id 和 url"""
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/material/add_material?access_token={token}&type=image"
        with open(file_path, "rb") as f:
            resp = requests.post(url, files={"media": f}, timeout=30)
        return resp.json()

    def upload_temp_image(self, file_path: str) -> dict:
        """上传临时图片素材（3天有效，但速度快，适合草稿配图）"""
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/media/upload?access_token={token}&type=image"
        with open(file_path, "rb") as f:
            resp = requests.post(url, files={"media": f}, timeout=30)
        return resp.json()

    def get_material_list(self, material_type: str = "image",
                          offset: int = 0, count: int = 20) -> dict:
        """获取素材列表"""
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/material/batchget_material?access_token={token}"
        payload = {"type": material_type, "offset": offset, "count": count}
        resp = requests.post(url, json=payload, timeout=10)
        return resp.json()


class WeChatDraftManager:
    """草稿管理器 - 创建/获取/删除/发布草稿"""

    def __init__(self, token_manager: WeChatTokenManager, config: WeChatConfig):
        self.token_manager = token_manager
        self.config = config

    def create_draft(self, articles: list[dict]) -> dict:
        """
        创建草稿
        articles参数格式：
        [{
            "title": "文章标题",
            "content": "<p>文章正文HTML</p>",
            "thumb_media_id": "封面图media_id",
            "digest": "文章摘要（可选）",
            "author": "作者名（可选）",
            "content_source_url": "原文链接（可选）",
            "need_open_comment": 0,  # 是否开启评论
            "only_fans_can_comment": 0,  # 是否仅粉丝可评论
        }]
        """
        import json
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/draft/add?access_token={token}"

        # ⚠️ 关键：手动用 ensure_ascii=False 序列化，防止中文被转义
        payload_bytes = json.dumps(
            {"articles": articles},
            ensure_ascii=False
        ).encode("utf-8")

        headers = {"Content-Type": "application/json; charset=utf-8"}
        resp = requests.post(url, data=payload_bytes, headers=headers, timeout=30)
        return resp.json()

    def get_draft(self, media_id: str) -> dict:
        """获取草稿详情"""
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/draft/get?access_token={token}"
        resp = requests.post(url, json={"media_id": media_id}, timeout=10)
        return resp.json()

    def delete_draft(self, media_id: str) -> dict:
        """删除草稿"""
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/draft/delete?access_token={token}"
        resp = requests.post(url, json={"media_id": media_id}, timeout=10)
        return resp.json()

    def publish_draft(self, media_id: str) -> dict:
        """发布草稿"""
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/freepublish/submit?access_token={token}"
        resp = requests.post(url, json={"media_id": media_id}, timeout=30)
        return resp.json()

    def get_publish_status(self, publish_id: str) -> dict:
        """查询发布状态"""
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/freepublish/get?access_token={token}"
        resp = requests.post(url, json={"publish_id": publish_id}, timeout=10)
        return resp.json()


class WeChatEcosystemSkills:
    """微信生态技能 - 统一入口"""

    def __init__(self, app_id: str = "", app_secret: str = ""):
        self.config = WeChatConfig(app_id=app_id, app_secret=app_secret)
        self.token_manager = WeChatTokenManager(self.config)
        self.material = WeChatMaterialManager(self.token_manager, self.config)
        self.draft = WeChatDraftManager(self.token_manager, self.config)

    def get_access_token(self) -> str:
        """获取Access Token"""
        return self.token_manager.get_token()

    def upload_image(self, file_path: str) -> dict:
        """上传图片素材"""
        return self.material.upload_image(file_path)

    def create_draft(self, title: str, content: str,
                     thumb_media_id: str = "",
                     digest: str = "",
                     author: str = "",
                     content_source_url: str = "") -> dict:
        """创建草稿"""
        articles = [{
            "title": title,
            "content": content,
            "thumb_media_id": thumb_media_id,
            "digest": digest,
            "author": author,
            "content_source_url": content_source_url,
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }]
        return self.draft.create_draft(articles)

    def publish_draft(self, media_id: str) -> dict:
        """发布草稿"""
        return self.draft.publish_draft(media_id)

    def get_publish_status(self, publish_id: str) -> dict:
        """查询发布状态"""
        return self.draft.get_publish_status(publish_id)

    def status(self) -> dict:
        return {
            "skill": "wechat-ecosystem",
            "version": "1.0.0",
            "capabilities": [
                "素材管理", "草稿管理", "文章发布",
                "Access Token管理", "发布状态查询",
            ],
            "configured": bool(self.config.app_id and self.config.app_secret),
            "status": "ready" if self.config.app_id else "pending_config",
        }
```

> ⚠️ **微信公众号 API 的重要限制**：
> 1. Access Token 有效期只有 **2小时**，调用频率限制为每日 2000 次。
> 2. 订阅号每天只能群发 **1条** 消息（通过发布接口"发布"不限次数，但不推送粉丝）。
> 3. 图片素材上传接口限制：永久素材总量上限 5000 个（含图文）。
> 4. `create_draft` 中的 `content` 必须是 **HTML格式**，不是 Markdown！

---

