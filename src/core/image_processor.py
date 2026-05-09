"""
图片处理器 - 提取、去重、下载
"""

import os
import hashlib
from urllib.parse import urlparse

from src.core.article_schema import ImageItem


class ImageProcessor:

    def __init__(self, download_dir: str = "data/images", max_count: int = 20, min_size: int = 50):
        self.download_dir = download_dir
        self.max_count = max_count
        self.min_size = min_size

    def deduplicate(self, images: list[ImageItem]) -> list[ImageItem]:
        seen_urls = set()
        unique = []
        for img in images:
            if img.url in seen_urls:
                continue
            seen_urls.add(img.url)
            if img.width > 0 and img.height > 0:
                if img.width < self.min_size or img.height < self.min_size:
                    continue
            unique.append(img)
        return unique[:self.max_count]

    def download(self, images: list[ImageItem]) -> list[ImageItem]:
        import requests
        os.makedirs(self.download_dir, exist_ok=True)
        downloaded = []
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})
        for img in images:
            try:
                resp = session.get(img.url, timeout=10)
                if resp.status_code != 200:
                    continue
                ext = self._guess_ext(img.url, resp.headers.get("content-type", ""))
                filename = f"{hashlib.md5(img.url.encode()).hexdigest()[:12]}{ext}"
                filepath = os.path.join(self.download_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                img.local_path = filepath
                downloaded.append(img)
            except Exception:
                downloaded.append(img)
        return downloaded

    @staticmethod
    def _guess_ext(url: str, content_type: str) -> str:
        parsed = urlparse(url)
        path = parsed.path.lower()
        for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]:
            if path.endswith(ext):
                return ext
        ct_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "image/svg+xml": ".svg",
        }
        return ct_map.get(content_type.split(";")[0], ".jpg")
