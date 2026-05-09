"""
微信公众号官方MCP服务 - WeChat Official Account MCP Server

基于 MCP (Model Context Protocol) 标准协议，提供微信公众号全套API。
兼容 Trae AI、Claude Desktop、Cursor 等所有MCP客户端。

MCP工具列表：
- wechat_get_access_token
- wechat_create_draft
- wechat_publish_draft
- wechat_upload_image
- wechat_content_check
- wechat_search_images
- wechat_ai_draw
- wechat_generate_cover
- scrape_article
- scrape_batch
- scrape_preview
"""

import os
import sys
import json
import asyncio
from typing import Any
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class WeChatMCPServer:
    """微信公众号 MCP Server - JSON-RPC 2.0 协议"""

    def __init__(self):
        self._skills_loaded = False

    def _load_skills(self):
        if self._skills_loaded:
            return
        from skills.wechat_ecosystem import WeChatEcosystemSkills
        from skills.content_compliance import ContentComplianceSkills
        from skills.copyright_free_images import CopyrightFreeImageSkills
        from skills.ai_drawing import AIDrawingSkills

        self.wechat = WeChatEcosystemSkills(
            app_id=os.getenv("WECHAT_APP_ID", ""),
            app_secret=os.getenv("WECHAT_APP_SECRET", ""),
        )
        self.compliance = ContentComplianceSkills(
            ai_api_key=os.getenv("AI_API_KEY", ""),
            ai_base_url=os.getenv("AI_API_BASE", "https://api.openai.com/v1"),
        )
        self.images = CopyrightFreeImageSkills(
            unsplash_key=os.getenv("UNSPLASH_ACCESS_KEY", ""),
            pexels_key=os.getenv("PEXELS_API_KEY", ""),
            pixabay_key=os.getenv("PIXABAY_API_KEY", ""),
        )
        self.drawing = AIDrawingSkills(
            openai_api_key=os.getenv("AI_API_KEY", ""),
            openai_base_url=os.getenv("AI_API_BASE", "https://api.openai.com/v1"),
        )
        self._skills_loaded = True

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "wechat_get_access_token",
                "description": "获取微信公众号Access Token",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            {
                "name": "wechat_create_draft",
                "description": "创建微信公众号文章草稿",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "文章标题"},
                        "content": {"type": "string", "description": "文章正文(HTML格式)"},
                        "thumb_media_id": {"type": "string", "description": "封面图media_id"},
                        "digest": {"type": "string", "description": "文章摘要"},
                        "author": {"type": "string", "description": "作者名称"},
                    },
                    "required": ["title", "content"],
                },
            },
            {
                "name": "wechat_publish_draft",
                "description": "发布微信公众号草稿",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "media_id": {"type": "string", "description": "草稿media_id"},
                    },
                    "required": ["media_id"],
                },
            },
            {
                "name": "wechat_upload_image",
                "description": "上传图片到微信公众号素材库",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "本地图片文件路径"},
                    },
                    "required": ["file_path"],
                },
            },
            {
                "name": "wechat_content_check",
                "description": "对文章内容进行合规检查（敏感词+广告法+AI审核）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "待检查的文章内容"},
                        "check_type": {
                            "type": "string",
                            "enum": ["quick", "full"],
                            "description": "quick=规则检查，full=规则+AI检查",
                        },
                    },
                    "required": ["content"],
                },
            },
            {
                "name": "wechat_search_images",
                "description": "搜索无版权商用图片素材（Unsplash/Pexels/Pixabay）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索关键词"},
                        "count": {"type": "integer", "description": "返回数量，默认10"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "wechat_ai_draw",
                "description": "使用AI生成图片（DALL-E）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "图片描述(prompt)"},
                        "size": {"type": "string", "description": "图片尺寸，默认1024x1024"},
                    },
                    "required": ["prompt"],
                },
            },
            {
                "name": "wechat_generate_cover",
                "description": "为文章生成公众号封面图",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "文章标题"},
                        "style": {
                            "type": "string",
                            "enum": ["professional", "creative", "tech"],
                            "description": "封面风格",
                        },
                    },
                    "required": ["title"],
                },
            },
            {
                "name": "scrape_article",
                "description": "抓取任意文章链接（公众号/知乎/头条/新闻站），自动提取标题+正文+图片，输出干净Markdown",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "文章URL"},
                        "platform_hint": {"type": "string", "description": "平台提示(可选): wechat/zhihu_article/toutiao/sohu等"},
                        "download_images": {"type": "boolean", "description": "是否下载图片到本地"},
                        "output_dir": {"type": "string", "description": "Markdown输出目录，默认data/articles"},
                    },
                    "required": ["url"],
                },
            },
            {
                "name": "scrape_batch",
                "description": "批量抓取多个文章链接，返回每篇结果+汇总统计",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "urls": {"type": "array", "items": {"type": "string"}, "description": "文章URL列表"},
                        "output_dir": {"type": "string", "description": "输出目录"},
                    },
                    "required": ["urls"],
                },
            },
            {
                "name": "scrape_preview",
                "description": "快速预览文章元数据（标题+摘要+图片数），不下载图片，正文截断500字",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "文章URL"},
                    },
                    "required": ["url"],
                },
            },
        ]

    async def handle_request(self, request: dict) -> dict:
        """处理MCP JSON-RPC请求"""
        self._load_skills()
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id")

        try:
            if method == "tools/list":
                result = {"tools": self.get_tools()}
            elif method == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                result = await self._call_tool(tool_name, arguments)
            else:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"未知方法: {method}"}}

            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": str(e)}}

    async def _call_tool(self, name: str, args: dict) -> dict:
        """执行工具调用"""
        if name == "wechat_get_access_token":
            token = self.wechat.token_manager.get_token()
            return {"content": [{"type": "text", "text": f"Access Token: {token[:20]}..."}]}

        elif name == "wechat_create_draft":
            article = {
                "title": args["title"],
                "content": args["content"],
                "thumb_media_id": args.get("thumb_media_id", ""),
                "digest": args.get("digest", ""),
                "author": args.get("author", ""),
            }
            result = self.wechat.draft.create_draft([article])
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}

        elif name == "wechat_publish_draft":
            result = self.wechat.draft.publish_draft(args["media_id"])
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}

        elif name == "wechat_upload_image":
            result = self.wechat.material.upload_image(args["file_path"])
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}

        elif name == "wechat_content_check":
            check_type = args.get("check_type", "quick")
            if check_type == "full":
                result = self.compliance.full_check(args["content"])
            else:
                result = self.compliance.quick_check(args["content"])
            return {"content": [{
                "type": "text",
                "text": json.dumps({
                    "passed": result.passed,
                    "score": result.score,
                    "violations": result.violations,
                    "suggestions": result.suggestions,
                    "risk_level": result.risk_level,
                }, ensure_ascii=False),
            }]}

        elif name == "wechat_search_images":
            results = self.images.search_all(args["query"], per_page=args.get("count", 10))
            return {"content": [{
                "type": "text",
                "text": json.dumps([
                    {"id": r.id, "url": r.url, "source": r.source, "description": r.description}
                    for r in results[:10]
                ], ensure_ascii=False),
            }]}

        elif name == "wechat_ai_draw":
            results = self.drawing.text_to_image(args["prompt"])
            return {"content": [{
                "type": "text",
                "text": json.dumps([
                    {"url": r.url, "revised_prompt": r.revised_prompt}
                    for r in results
                ], ensure_ascii=False),
            }]}

        elif name == "wechat_generate_cover":
            result = self.drawing.generate_article_cover(
                title=args["title"],
                style=args.get("style", "professional"),
            )
            text = json.dumps({
                "url": result.url if result else "",
                "local_path": result.local_path if result else "",
            }, ensure_ascii=False) if result else "封面生成失败"
            return {"content": [{"type": "text", "text": text}]}

        elif name == "scrape_article":
            from src.core.content_scraper import ContentScraper
            scraper = ContentScraper()
            output_dir = args.get("output_dir", "data/articles")
            article = scraper.scrape(
                url=args["url"],
                platform_hint=args.get("platform_hint", ""),
                download_images=args.get("download_images", False),
            )
            report = scraper.formatter.to_dict(article)
            report["markdown_preview"] = article.content[:300] if article.content else ""
            return {"content": [{"type": "text", "text": json.dumps(report, ensure_ascii=False)}]}

        elif name == "scrape_batch":
            from src.core.content_scraper import ContentScraper
            scraper = ContentScraper()
            urls = args.get("urls", [])
            articles = scraper.scrape_batch(urls)
            results = []
            for a in articles:
                results.append({
                    "url": a.url,
                    "platform": a.platform.value,
                    "title": a.title,
                    "status": a.status.value,
                    "confidence": a.confidence,
                    "content_length": len(a.content),
                })
            summary = {
                "total": len(urls),
                "success": sum(1 for a in articles if a.status.value == "success"),
                "failed": sum(1 for a in articles if a.status.value != "success"),
                "results": results,
            }
            return {"content": [{"type": "text", "text": json.dumps(summary, ensure_ascii=False)}]}

        elif name == "scrape_preview":
            from src.core.content_scraper import ContentScraper
            scraper = ContentScraper()
            article = scraper.scrape_preview(url=args["url"])
            preview = {
                "url": article.url,
                "platform": article.platform.value,
                "title": article.title,
                "author": article.author,
                "publish_time": article.publish_time,
                "summary": article.summary,
                "content_preview": article.content[:500] if article.content else "",
                "image_count": len(article.images),
                "confidence": article.confidence,
            }
            return {"content": [{"type": "text", "text": json.dumps(preview, ensure_ascii=False)}]}

        return {"content": [{"type": "text", "text": f"未知工具: {name}"}]}


async def _main():
    """MCP Server stdio 入口"""
    server = WeChatMCPServer()
    print("WeChat Official Account MCP Server v1.0.0", file=sys.stderr)
    print("Waiting for MCP requests on stdio...", file=sys.stderr)

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            request = json.loads(line.strip())
            response = await server.handle_request(request)
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except json.JSONDecodeError:
            continue
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    asyncio.run(_main())
