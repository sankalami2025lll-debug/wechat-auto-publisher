"""
无版权商用图片素材技能模块 - Copyright-Free Commercial Image Skills

提供多渠道无版权图片搜索与下载能力：
- Unsplash API（高质量摄影作品）
- Pexels API（商业用途免费）
- Pixabay API（无版权要求）
- 图片尺寸筛选
- 批量下载与缓存
"""

import os
import time
from typing import Optional
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote_plus


@dataclass
class ImageResult:
    id: str
    url: str
    thumb_url: str
    download_url: str
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

    def search(self, query: str, per_page: int = 10, page: int = 1, orientation: str = "landscape") -> list[ImageResult]:
        import requests
        url = f"{self.BASE_URL}/search/photos"
        headers = {"Authorization": f"Client-ID {self.access_key}"} if self.access_key else {}
        params = {
            "query": query,
            "per_page": per_page,
            "page": page,
            "orientation": orientation,
        }
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

    def download(self, image: ImageResult, save_dir: str) -> Optional[str]:
        import requests
        os.makedirs(save_dir, exist_ok=True)
        filename = f"{image.id}.jpg"
        filepath = os.path.join(save_dir, filename)
        resp = requests.get(image.download_url, timeout=30)
        if resp.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return filepath
        return None


class PexelsClient:
    """Pexels API 客户端"""

    BASE_URL = "https://api.pexels.com/v1"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def search(self, query: str, per_page: int = 10, page: int = 1, orientation: str = "landscape") -> list[ImageResult]:
        import requests
        url = f"{self.BASE_URL}/search"
        headers = {"Authorization": self.api_key}
        params = {
            "query": query,
            "per_page": per_page,
            "page": page,
            "orientation": orientation,
        }
        resp = requests.get(url, headers=headers, params=params, timeout=15)
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

    def download(self, image: ImageResult, save_dir: str) -> Optional[str]:
        import requests
        os.makedirs(save_dir, exist_ok=True)
        filename = f"pexels_{image.id}.jpg"
        filepath = os.path.join(save_dir, filename)
        resp = requests.get(image.download_url, timeout=30)
        if resp.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return filepath
        return None


class PixabayClient:
    """Pixabay API 客户端"""

    BASE_URL = "https://pixabay.com/api"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def search(self, query: str, per_page: int = 10, page: int = 1, orientation: str = "horizontal") -> list[ImageResult]:
        import requests
        params = {
            "key": self.api_key,
            "q": query,
            "per_page": per_page,
            "page": page,
            "orientation": orientation,
            "safesearch": "true",
        }
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

    def download(self, image: ImageResult, save_dir: str) -> Optional[str]:
        import requests
        os.makedirs(save_dir, exist_ok=True)
        filename = f"pixabay_{image.id}.jpg"
        filepath = os.path.join(save_dir, filename)
        resp = requests.get(image.download_url, timeout=30)
        if resp.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return filepath
        return None


class CopyrightFreeImageSkills:
    """无版权商用图片素材技能 - 统一入口"""

    def __init__(self,
                 unsplash_key: str = "",
                 pexels_key: str = "",
                 pixabay_key: str = ""):
        self.unsplash = UnsplashClient(unsplash_key)
        self.pexels = PexelsClient(pexels_key)
        self.pixabay = PixabayClient(pixabay_key)

    def search_all(self, query: str, per_page: int = 30,
                   orientation: str = "landscape",
                   min_width: int = 800, min_height: int = 600) -> list[ImageResult]:
        """跨平台搜索图片"""
        all_results = []
        if self.unsplash.access_key:
            results = self.unsplash.search(query, per_page=min(per_page, 10))
            all_results.extend(results)
        if self.pexels.api_key:
            results = self.pexels.search(query, per_page=min(per_page, 10))
            all_results.extend([r for r in results if r not in all_results])
        if self.pixabay.api_key:
            results = self.pixabay.search(query, per_page=min(per_page, 10))
            all_results.extend([r for r in results if r not in all_results])
        filtered = [
            r for r in all_results
            if r.width >= min_width and r.height >= min_height
        ]
        return filtered[:per_page]

    def download_best(self, query: str, save_dir: str, count: int = 3) -> list[str]:
        """搜索并下载最佳图片"""
        results = self.search_all(query, per_page=count)
        saved = []
        for img in results:
            if img.source == "unsplash":
                path = self.unsplash.download(img, save_dir)
            elif img.source == "pexels":
                path = self.pexels.download(img, save_dir)
            elif img.source == "pixabay":
                path = self.pixabay.download(img, save_dir)
            else:
                continue
            if path:
                saved.append(path)
        return saved

    def status(self) -> dict:
        return {
            "skill": "copyright-free-images",
            "version": "1.0.0",
            "sources": {
                "unsplash": bool(self.unsplash.access_key),
                "pexels": bool(self.pexels.api_key),
                "pixabay": bool(self.pixabay.api_key),
            },
            "active_sources": sum([
                bool(self.unsplash.access_key),
                bool(self.pexels.api_key),
                bool(self.pixabay.api_key),
            ]),
            "status": "ready" if any([
                self.unsplash.access_key,
                self.pexels.api_key,
                self.pixabay.api_key,
            ]) else "pending_config",
        }
