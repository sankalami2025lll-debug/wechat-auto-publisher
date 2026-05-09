"""
微信公众号全自动发布 · 端到端流程
步骤：下载封面图 → 上传素材库 → 创建草稿 → 返回链接
"""
import os
import sys
import json
import requests
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

APP_ID = os.getenv("WECHAT_APP_ID", "")
APP_SECRET = os.getenv("WECHAT_APP_SECRET", "")

BASE_URL = "https://api.weixin.qq.com"

def get_token():
    url = f"{BASE_URL}/cgi-bin/token"
    params = {"grant_type": "client_credential", "appid": APP_ID, "secret": APP_SECRET}
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    if "access_token" in data:
        return data["access_token"]
    raise Exception(f"Token获取失败: {data}")

def download_cover():
    """下载封面图到本地"""
    cover_url = "https://images.pexels.com/photos/534229/pexels-photo-534229.jpeg?auto=compress&cs=tinysrgb&w=1200"
    save_dir = PROJECT_ROOT / "data" / "covers"
    save_dir.mkdir(parents=True, exist_ok=True)
    filepath = save_dir / "cover_ai_resell.jpg"

    if filepath.exists():
        return str(filepath)

    resp = requests.get(cover_url, timeout=30)
    with open(filepath, "wb") as f:
        f.write(resp.content)
    return str(filepath)

def upload_cover_image(token, filepath):
    """上传封面图到微信永久素材库，返回 media_id 和 url"""
    url = f"{BASE_URL}/cgi-bin/material/add_material?access_token={token}&type=image"
    with open(filepath, "rb") as f:
        resp = requests.post(url, files={"media": f}, timeout=30)
    return resp.json()

def create_draft(token, title, content, thumb_media_id, digest, author):
    """创建草稿（手动序列化避免中文被转义）"""
    url = f"{BASE_URL}/cgi-bin/draft/add?access_token={token}"
    payload = {
        "articles": [{
            "title": title,
            "content": content,
            "thumb_media_id": thumb_media_id,
            "digest": digest,
            "author": author,
            "content_source_url": "",
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }]
    }
    payload_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    resp = requests.post(url, data=payload_bytes, headers={"Content-Type": "application/json; charset=utf-8"}, timeout=30)
    return resp.json()

def main():
    print("=" * 55)
    print("  微信公众号全自动发布 · 端到端流程")
    print("=" * 55)

    # Step 1: Token
    print("\n[1/4] 获取 Access Token...")
    token = get_token()
    print(f"  ✅ Token: {token[:15]}...")

    # Step 2: 封面图
    print("\n[2/4] 下载封面图...")
    cover_path = download_cover()
    print(f"  ✅ 封面图: {cover_path}")

    print("  上传到微信素材库...")
    upload_result = upload_cover_image(token, cover_path)
    print(f"  📤 上传结果: {json.dumps(upload_result, ensure_ascii=False)}")
    thumb_media_id = upload_result.get("media_id", "")

    # Step 3: 读取改写文章
    print("\n[3/4] 读取改写文章...")
    article_path = PROJECT_ROOT / "data" / "articles" / "rewritten_AI中转站深度原创.md"
    if not article_path.exists():
        print("  ⚠️ 改写文章不存在，使用测试内容")
        title = "AI中转站测试文章"
        content = "<p>这是一篇测试文章，验证微信公众号自动发布链路是否畅通。</p>"
        digest = "验证全自动发布链路"
        author = ""
    else:
        with open(article_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        lines = md_content.split("\n")
        full_title = lines[0].replace("# ", "").strip()
        api_title = full_title
        max_bytes = 28

        # 优先读取 MD 中手动指定的短标题：> **短标题**: xxx
        if len(lines) > 1 and lines[1].strip().startswith("> **短标题**:"):
            manual = lines[1].strip().split(":", 1)[1].strip()
            if manual and len(manual.encode("utf-8")) <= max_bytes:
                api_title = manual
                print(f"  ✏️ 手动指定短标题: {api_title}")

        if api_title == full_title and len(full_title.encode("utf-8")) > max_bytes:
            # 智能截断：在标点处断开
            best = ""
            for ch in full_title:
                trial = (best + ch).encode("utf-8")
                if len(trial) <= max_bytes - 3:
                    best += ch
                else:
                    break
            for punct in ["？", "！", "。", "，", "：", "、", "—"]:
                pos = best.rfind(punct)
                if pos > 0:
                    best = best[:pos]
                    break
            api_title = best + "…"
        print(f"  📏 API标题: {len(api_title.encode('utf-8'))}B → {api_title}")

        # 先处理图片：下载→上传微信→替换URL
        image_map = {}
        img_idx = 0
        for line in lines:
            s = line.strip()
            if s.startswith("!["):
                end = s.index("]")
                start_paren = s.index("(", end)
                end_paren = s.index(")", start_paren)
                pexels_url = s[start_paren+1:end_paren]
                if pexels_url not in image_map:
                    print(f"  📥 下载图片 {img_idx+1}: {pexels_url[:60]}...")
                    img_resp = requests.get(pexels_url, timeout=30)
                    tmp_path = PROJECT_ROOT / "data" / "covers" / f"tmp_img_{img_idx}.jpg"
                    with open(tmp_path, "wb") as f:
                        f.write(img_resp.content)
                    print(f"  📤 上传到微信素材库...")
                    up = upload_cover_image(token, tmp_path)
                    wx_url = up.get("url", pexels_url)
                    print(f"  ✅ 微信URL: {wx_url[:60]}...")
                    image_map[pexels_url] = wx_url
                    img_idx += 1

        # Markdown → 微信HTML（含粗体、图片、排版、正文首行完整标题）
        def md_inline_to_html(text):
            import re
            return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

        STYLE = {
            "h1": "font-size:22px;font-weight:bold;color:#222;margin:0 0 24px 0;text-align:center;letter-spacing:1px;",
            "h2": "font-size:19px;font-weight:bold;color:#1a1a1a;margin:32px 0 12px 0;padding-left:10px;border-left:3px solid #07c160;",
            "h3": "font-size:17px;font-weight:bold;color:#333;margin:24px 0 10px 0;",
            "p": "font-size:16px;color:#3a3a3a;line-height:1.85;margin:0 0 14px 0;letter-spacing:0.5px;",
            "img": "max-width:100%;border-radius:4px;margin:12px 0;",
        }

        html_blocks = []
        # 正文首行：完整长标题
        html_blocks.append(f'<h1 style="{STYLE["h1"]}">{md_inline_to_html(full_title)}</h1>')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            if line.startswith("# ") or line == "---" or "**短标题**:" in line:
                i += 1
                continue
            if line.startswith("## "):
                html_blocks.append(f'<h2 style="{STYLE["h2"]}">{md_inline_to_html(line[3:])}</h2>')
            elif line.startswith("### "):
                html_blocks.append(f'<h3 style="{STYLE["h3"]}">{md_inline_to_html(line[4:])}</h3>')
            elif line.startswith("!["):
                end_br = line.index("]")
                alt = line[2:end_br]
                start_p = line.index("(", end_br)
                end_p = line.index(")", start_p)
                pexels_url = line[start_p+1:end_p]
                wx_url = image_map.get(pexels_url, pexels_url)
                html_blocks.append(f'<section style="text-align:center;margin:20px 0;"><img src="{wx_url}" alt="{alt}" style="{STYLE["img"]}"/></section>')
            elif line.startswith("> "):
                html_blocks.append(f'<blockquote style="background:#f6f8fa;border-left:4px solid #07c160;padding:12px 16px;margin:16px 0;border-radius:0 6px 6px 0;"><p style="font-size:15px;color:#666;line-height:1.7;margin:0;">{md_inline_to_html(line[2:])}</p></blockquote>')
            elif line.startswith("- "):
                items = []
                while i < len(lines) and lines[i].strip().startswith("- "):
                    it = lines[i].strip()[2:]
                    items.append(f'<li style="font-size:16px;color:#3a3a3a;line-height:1.85;margin-bottom:6px;">{md_inline_to_html(it)}</li>')
                    i += 1
                html_blocks.append(f'<ul style="padding-left:24px;margin:12px 0;">{"".join(items)}</ul>')
                continue
            elif line[0].isdigit() and ". " in line[:5]:
                items = []
                while i < len(lines) and lines[i].strip() and lines[i].strip()[0].isdigit() and ". " in lines[i].strip()[:5]:
                    dot_pos = lines[i].strip().index(". ")
                    it = lines[i].strip()[dot_pos+2:]
                    items.append(f'<li style="font-size:16px;color:#3a3a3a;line-height:1.85;margin-bottom:6px;">{md_inline_to_html(it)}</li>')
                    i += 1
                html_blocks.append(f'<ol style="padding-left:24px;margin:12px 0;">{"".join(items)}</ol>')
                continue
            else:
                para_lines = [md_inline_to_html(line)]
                i += 1
                while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(("#", "!", "-", ">")) and not (lines[i].strip()[0].isdigit() and ". " in lines[i].strip()[:5]):
                    if lines[i].strip() != "---":
                        para_lines.append(md_inline_to_html(lines[i].strip()))
                    i += 1
                html_blocks.append(f'<p style="{STYLE["p"]}">{"<br/>".join(para_lines)}</p>')
                continue
            i += 1
        content = "".join(html_blocks)
        digest = full_title[:100]
        author = ""

    print(f"  ✅ API标题: {api_title}")
    print(f"  ✅ 完整标题: {full_title}")
    print(f"  ✅ 摘要: {digest[:50]}...")
    print(f"  ✅ HTML: {len(content)} 字符")

    # Step 4: 创建草稿
    print("\n[4/4] 创建微信公众号草稿...")
    draft_result = create_draft(token, api_title, content, thumb_media_id, digest, author)
    print(f"  📝 草稿结果: {json.dumps(draft_result, ensure_ascii=False, indent=2)}")

    if "media_id" in draft_result:
        media_id = draft_result["media_id"]
        draft_url = f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=10&appmsgid={media_id}&token={token}&lang=zh_CN"
        print(f"\n{'='*55}")
        print(f"  🎉 草稿创建成功！")
        print(f"  📋 media_id: {media_id}")
        print(f"  🔗 预览链接: {draft_url}")
        print(f"{'='*55}")

        return {"media_id": media_id, "draft_url": draft_url}
    else:
        print(f"\n  ❌ 草稿创建失败: {draft_result}")
        return draft_result

if __name__ == "__main__":
    main()
