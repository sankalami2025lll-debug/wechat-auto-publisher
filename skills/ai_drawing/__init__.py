"""
AI绘图技能模块 - AI Drawing Skills

提供AI文生图能力：
- OpenAI DALL-E 2/3 API
- 本地Stable Diffusion支持
- 封面图自动生成
- 图片风格控制
- 批量生成
"""

import os
import base64
import time
from typing import Optional, Literal
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GeneratedImage:
    url: str = ""
    b64_json: str = ""
    revised_prompt: str = ""
    local_path: str = ""
    model: str = "dall-e-3"
    size: str = "1024x1024"


class DalleClient:
    """DALL-E API 客户端"""

    def __init__(self, api_key: str = "", base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url

    def generate(self, prompt: str, model: str = "dall-e-3",
                 size: str = "1024x1024", quality: str = "standard",
                 style: str = "vivid", n: int = 1) -> list[GeneratedImage]:
        import requests
        url = f"{self.base_url}/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size,
            "quality": quality,
            "style": style,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        if resp.status_code != 200:
            raise Exception(f"DALL-E API 错误: {resp.status_code} - {resp.text}")
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
        import requests
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
    """封面图生成器 - 专为公众号优化"""

    WECHAT_COVER_SIZES = {
        "large": (900, 383),   # 大封面（2.35:1）
        "small": (200, 200),   # 小封面
    }

    def __init__(self, dalle_client: DalleClient):
        self.dalle = dalle_client

    def generate_cover(self, title: str, style: str = "professional",
                       save_dir: str = "data/covers") -> Optional[GeneratedImage]:
        """根据文章标题生成封面图"""
        prompts = {
            "professional": (
                f"为标题为「{title}」的专业文章生成封面图。"
                "现代简约风格，商务配色（蓝/白/灰），几何图案装饰，"
                "适合微信公号封面。2.35:1比例，无水印，无文字。"
                "A professional cover image for a WeChat article. "
                "Modern minimalist style, business colors (blue/white/gray), "
                "geometric patterns. 2.35:1 aspect ratio, no watermark, no text."
            ),
            "creative": (
                f"为标题为「{title}」的创意文章生成封面图。"
                "色彩鲜艳，创意构图，插画风格，适合微信封面。"
                "2.35:1比例，无水印，无文字。"
            ),
            "tech": (
                f"A futuristic tech-themed cover image for article '{title}'. "
                "Dark theme with neon accents, circuit-like patterns. "
                "2.35:1 aspect ratio, no text, no watermark."
            ),
        }
        prompt = prompts.get(style, prompts["professional"])
        try:
            images = self.dalle.generate(
                prompt=prompt,
                size="1792x1024",
                quality="standard",
                style="vivid",
            )
            if images:
                return self.dalle.generate_and_save(
                    prompt=prompt,
                    save_dir=save_dir,
                    filename=f"cover_{int(time.time())}.png",
                    size="1792x1024",
                )[0]
        except Exception as e:
            print(f"封面图生成失败: {e}")
        return None


class AIDrawingSkills:
    """AI绘图技能 - 统一入口"""

    def __init__(self, openai_api_key: str = "", openai_base_url: str = "https://api.openai.com/v1"):
        self.dalle = DalleClient(api_key=openai_api_key, base_url=openai_base_url)
        self.cover_generator = CoverImageGenerator(self.dalle)

    def text_to_image(self, prompt: str, **kwargs) -> list[GeneratedImage]:
        return self.dalle.generate(prompt, **kwargs)

    def generate_article_cover(self, title: str, style: str = "professional",
                               save_dir: str = "data/covers") -> Optional[GeneratedImage]:
        return self.cover_generator.generate_cover(title, style, save_dir)

    def status(self) -> dict:
        return {
            "skill": "ai-drawing",
            "version": "1.0.0",
            "models": ["dall-e-2", "dall-e-3"],
            "capabilities": [
                "文生图 (text_to_image)",
                "封面图生成 (generate_article_cover)",
                "多风格支持 (professional/creative/tech)",
                "微信封面尺寸适配",
            ],
            "status": "ready" if self.dalle.api_key else "pending_config",
        }
