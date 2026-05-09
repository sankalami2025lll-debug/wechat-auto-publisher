"""
微信生态全量技能模块 - WeChat Ecosystem Full Skills

提供微信公众号全生命周期管理能力：
- 素材管理（上传/下载/删除）
- 草稿管理（创建/编辑/发布）
- 文章发布与群发
- 用户消息处理
- 二维码生成
- 菜单管理
"""

import json
import time
import hashlib
from typing import Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class WeChatConfig:
    app_id: str = ""
    app_secret: str = ""
    token: str = ""
    encoding_aes_key: str = ""
    base_url: str = "https://api.weixin.qq.com"


class WeChatTokenManager:
    """Access Token 管理器 - 自动获取、缓存、刷新"""

    def __init__(self, config: WeChatConfig):
        self.config = config
        self._token: Optional[str] = None
        self._expires_at: float = 0

    def get_token(self) -> str:
        if self._token and time.time() < self._expires_at - 300:
            return self._token
        self._refresh_token()
        return self._token

    def _refresh_token(self) -> None:
        import requests
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
        else:
            raise Exception(f"获取Access Token失败: {data}")


class WeChatMaterialManager:
    """素材管理器 - 上传/获取/删除永久和临时素材"""

    def __init__(self, token_manager: WeChatTokenManager, config: WeChatConfig):
        self.token_manager = token_manager
        self.config = config

    def upload_image(self, file_path: str) -> dict:
        """上传图片素材（永久），返回 media_id 和 url"""
        import requests
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/material/add_material?access_token={token}&type=image"
        with open(file_path, "rb") as f:
            resp = requests.post(url, files={"media": f}, timeout=30)
        return resp.json()

    def upload_thumb(self, file_path: str) -> dict:
        """上传缩略图（永久）"""
        import requests
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/material/add_material?access_token={token}&type=thumb"
        with open(file_path, "rb") as f:
            resp = requests.post(url, files={"media": f}, timeout=30)
        return resp.json()

    def upload_temp_image(self, file_path: str) -> dict:
        """上传临时图片素材（3天有效）"""
        import requests
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/media/upload?access_token={token}&type=image"
        with open(file_path, "rb") as f:
            resp = requests.post(url, files={"media": f}, timeout=30)
        return resp.json()

    def get_material_list(self, material_type: str = "image", offset: int = 0, count: int = 20) -> dict:
        """获取素材列表"""
        import requests
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/material/batchget_material?access_token={token}"
        payload = {"type": material_type, "offset": offset, "count": count}
        resp = requests.post(url, json=payload, timeout=10)
        return resp.json()

    def delete_material(self, media_id: str) -> dict:
        """删除永久素材"""
        import requests
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/material/del_material?access_token={token}"
        resp = requests.post(url, json={"media_id": media_id}, timeout=10)
        return resp.json()


class WeChatDraftManager:
    """草稿管理器 - 创建/编辑/发布草稿"""

    def __init__(self, token_manager: WeChatTokenManager, config: WeChatConfig):
        self.token_manager = token_manager
        self.config = config

    def create_draft(self, articles: list[dict]) -> dict:
        """创建草稿
        articles: [{"title": "", "content": "", "thumb_media_id": "", "digest": "", ...}]
        """
        import requests
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/draft/add?access_token={token}"
        payload = {"articles": articles}
        resp = requests.post(url, json=payload, timeout=30)
        return resp.json()

    def get_draft(self, media_id: str) -> dict:
        """获取草稿详情"""
        import requests
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/draft/get?access_token={token}"
        resp = requests.post(url, json={"media_id": media_id}, timeout=10)
        return resp.json()

    def delete_draft(self, media_id: str) -> dict:
        """删除草稿"""
        import requests
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/draft/delete?access_token={token}"
        resp = requests.post(url, json={"media_id": media_id}, timeout=10)
        return resp.json()

    def publish_draft(self, media_id: str) -> dict:
        """发布草稿"""
        import requests
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/freepublish/submit?access_token={token}"
        resp = requests.post(url, json={"media_id": media_id}, timeout=30)
        return resp.json()

    def get_publish_status(self, publish_id: str) -> dict:
        """查询发布状态"""
        import requests
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/freepublish/get?access_token={token}"
        resp = requests.post(url, json={"publish_id": publish_id}, timeout=10)
        return resp.json()


class WeChatQRCodeGenerator:
    """二维码生成器"""

    def __init__(self, token_manager: WeChatTokenManager, config: WeChatConfig):
        self.token_manager = token_manager
        self.config = config

    def create_qrcode(self, action_name: str = "QR_STR_SCENE", expire_seconds: int = 2592000,
                      scene_id: int = 0, scene_str: str = "") -> dict:
        """创建临时/永久二维码 ticket"""
        import requests
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/qrcode/create?access_token={token}"
        payload = {
            "expire_seconds": expire_seconds,
            "action_name": action_name,
            "action_info": {"scene": {}},
        }
        if action_name == "QR_STR_SCENE":
            payload["action_info"]["scene"]["scene_str"] = scene_str
        else:
            payload["action_info"]["scene"]["scene_id"] = scene_id
        resp = requests.post(url, json=payload, timeout=10)
        return resp.json()

    def get_qrcode_url(self, ticket: str) -> str:
        """通过 ticket 获取二维码图片 URL"""
        import requests
        return f"https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket={requests.utils.quote(ticket)}"


class WeChatMenuManager:
    """自定义菜单管理器"""

    def __init__(self, token_manager: WeChatTokenManager, config: WeChatConfig):
        self.token_manager = token_manager
        self.config = config

    def create_menu(self, menu_data: dict) -> dict:
        """创建自定义菜单"""
        import requests
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/menu/create?access_token={token}"
        resp = requests.post(url, json=menu_data, timeout=10)
        return resp.json()

    def get_menu(self) -> dict:
        """获取当前菜单"""
        import requests
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/menu/get?access_token={token}"
        resp = requests.get(url, timeout=10)
        return resp.json()

    def delete_menu(self) -> dict:
        """删除菜单"""
        import requests
        token = self.token_manager.get_token()
        url = f"{self.config.base_url}/cgi-bin/menu/delete?access_token={token}"
        resp = requests.get(url, timeout=10)
        return resp.json()


class WeChatEcosystemSkills:
    """微信生态全量技能 - 统一入口"""

    def __init__(self, app_id: str = "", app_secret: str = "", token: str = "", encoding_aes_key: str = ""):
        self.config = WeChatConfig(
            app_id=app_id,
            app_secret=app_secret,
            token=token,
            encoding_aes_key=encoding_aes_key,
        )
        self.token_manager = WeChatTokenManager(self.config)
        self.material = WeChatMaterialManager(self.token_manager, self.config)
        self.draft = WeChatDraftManager(self.token_manager, self.config)
        self.qrcode = WeChatQRCodeGenerator(self.token_manager, self.config)
        self.menu = WeChatMenuManager(self.token_manager, self.config)

    def status(self) -> dict:
        """获取技能状态"""
        return {
            "skill": "wechat-ecosystem",
            "version": "1.0.0",
            "capabilities": [
                "素材管理 (material)",
                "草稿管理 (draft)",
                "文章发布 (publish)",
                "二维码生成 (qrcode)",
                "菜单管理 (menu)",
                "Token管理 (token)",
            ],
            "status": "ready",
            "requires_config": bool(self.config.app_id and self.config.app_secret),
        }
