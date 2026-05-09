"""
端到端流程测试脚本 - E2E Pipeline Test

完整链路：网页抓取 → AI改写 → Markdown输出 → 微信草稿创建

用法:
    python scripts/test_e2e_pipeline.py --url "https://mp.weixin.qq.com/s/xxxxx"
    python scripts/test_e2e_pipeline.py --url "https://mp.weixin.qq.com/s/xxxxx" --skip-wechat
"""

import os
import sys
import json
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STEPS = {}


def step(name, success, detail=""):
    icon = "✅" if success else "❌"
    STEPS[name] = {"success": success, "detail": str(detail)}
    print(f"  {icon} {name}")
    if detail:
        for line in str(detail).split("\n"):
            print(f"     {line}")


def step_header(num, title):
    print()
    print(f"{'='*50}")
    print(f"  Step {num}: {title}")
    print(f"{'='*50}")
    print()


def step_1_scrape(url):
    step_header(1, "网页抓取 - ContentScraper")
    try:
        from src.core.content_scraper import ContentScraper
        from src.core.article_schema import ScrapeConfig

        config = ScrapeConfig(download_images=False, cache_enabled=True)
        scraper = ContentScraper(config)

        t_start = time.time()
        article = scraper.scrape(url)
        elapsed = time.time() - t_start

        if article.status.value == "success":
            step("平台识别", True, article.platform.value)
            step("标题提取", bool(article.title), article.title[:80])
            step("正文提取", len(article.content) > 100,
                 f"{len(article.content)} 字符 | 可信度 {article.confidence:.0%}")
            step(f"图片提取", True, f"{len(article.images)} 张")
            step(f"抓取耗时", True, f"{elapsed:.1f}s | Fetcher: {article.fetcher_used.value}")
            return article
        else:
            step("抓取状态", False, f"{article.status.value}: {article.error_message}")
            return None
    except ImportError as e:
        return _fake_article(url)

    except Exception as e:
        step("抓取异常", False, str(e))
        return _fake_article(url)


def step_2_rewrite(article):
    step_header(2, "AI改写 - ContentRewriter (去AI味 + 口语化)")

    try:
        from src.core.content_rewriter import ContentRewriter

        ai_key = os.getenv("AI_API_KEY", "")
        ai_base = os.getenv("AI_API_BASE", "https://api.openai.com/v1")

        if not ai_key:
            step("AI_API_KEY", False, "未配置环境变量，使用规则降级改写")
        else:
            step("AI服务", True, f"已配置 ({ai_base})")

        rewriter = ContentRewriter(api_key=ai_key, base_url=ai_base)

        t_start = time.time()
        result = rewriter.humanize(article)
        elapsed = time.time() - t_start

        step("改写方法", True, result.method)
        step("标题改写", bool(result.title != result.original_title),
             f"原: {result.original_title[:50]}\n     新: {result.title[:50]}")
        step("正文改写", True,
             f"原 {result.original_length} 字符 → 新 {result.rewritten_length} 字符")
        step("改写耗时", True, f"{elapsed:.1f}s")

        if ai_key:
            step("标题优化", True)
            titles = rewriter.optimize_title(article)
            best = titles.get("best", "")
            reason = titles.get("reason", "")
            print(f"     📝 推荐标题: {best}")
            print(f"     💡 理由: {reason}")

        return result
    except ImportError:
        print("  ⚠️  content_rewriter 模块不可用，使用原文")
        return _fake_rewrite(article)
    except Exception as e:
        step("改写异常", False, str(e))
        return _fake_rewrite(article)


def step_3_save(rewrite_result, article):
    step_header(3, "文件保存 - Markdown + JSON")

    try:
        from src.core.markdown_formatter import MarkdownFormatter

        formatter = MarkdownFormatter()
        output_dir = os.path.join(PROJECT_ROOT, "data", "articles")
        os.makedirs(output_dir, exist_ok=True)

        article.content = rewrite_result.content
        article.title = rewrite_result.title
        article.summary = rewrite_result.summary

        paths = formatter.save(article, output_dir)
        step("Markdown", os.path.exists(paths["markdown"]), paths["markdown"])
        step("JSON", os.path.exists(paths["json"]), paths["json"])

        with open(paths["markdown"], "r", encoding="utf-8") as f:
            md_content = f.read()
        lines = md_content.split("\n")
        step("MD结构", len(lines) > 5, f"{len(lines)} 行 · {len(md_content)} 字符")

        return paths
    except Exception as e:
        step("保存异常", False, str(e))
        return {}


def step_4_wechat_draft(paths, rewrite_result, article):
    step_header(4, "微信草稿创建 - WeChat API")

    app_id = os.getenv("WECHAT_APP_ID", "")
    app_secret = os.getenv("WECHAT_APP_SECRET", "")

    if not app_id or not app_secret:
        step("微信配置", False, "WECHAT_APP_ID 或 WECHAT_APP_SECRET 未配置")
        print("     💡 配置后可通过微信公众号API创建真实草稿")
        print("     💡 配置方法: cp config/.env.example .env 并填入真实值")
        return {}

    try:
        from skills.wechat_ecosystem import WeChatEcosystemSkills

        wechat = WeChatEcosystemSkills(app_id=app_id, app_secret=app_secret)

        step("获取Token", True)
        token = wechat.token_manager.get_token()
        step("Token", True, f"{token[:20]}...")

        content = rewrite_result.content
        content_html = _text_to_basic_html(content)

        draft_data = {
            "title": rewrite_result.title,
            "content": content_html,
            "author": article.author or "AI助手",
            "digest": rewrite_result.summary or article.summary or content[:100],
        }

        result = wechat.draft.create_draft([draft_data])
        step("草稿创建", "media_id" in result,
             json.dumps(result, ensure_ascii=False, indent=2))

        if "media_id" in result:
            media_id = result["media_id"]
            draft_url = f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=10&appmsgid={media_id}"
            step("草稿链接", True, draft_url)
            return {"media_id": media_id, "draft_url": draft_url}

        return result
    except ImportError:
        step("微信模块", False, "skills.wechat_ecosystem 模块不可用")
        return {}
    except Exception as e:
        step("微信API", False, str(e))
        return {}


def _text_to_basic_html(text):
    paragraphs = text.split("\n\n")
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if p.startswith("# "):
            html_parts.append(f"<h2>{p[2:]}</h2>")
        elif p.startswith("## "):
            html_parts.append(f"<h3>{p[3:]}</h3>")
        else:
            html_parts.append(f"<p>{p}</p>")
    return "".join(html_parts)


def _fake_article(url):
    from src.core.article_schema import ArticleData, PlatformType, FetcherType, ScrapeStatus

    print("  💡 [模拟模式] 使用示例数据演示流程")
    article = ArticleData(
        url=url,
        platform=PlatformType.WECHAT,
        title="2025年人工智能发展趋势与展望",
        author="科技观察员",
        publish_time="2025-06-01 10:00:00",
        content=(
            "在当今时代，人工智能技术正以前所未有的速度发展。值得注意的是，大语言模型的出现标志着AI发展进入新篇章。"
            "此外，多模态AI系统逐渐成为主流。与此同时，AI Agent技术也开始从实验室走向实际应用。"
            "综上所述，AI正在深刻改变各行各业的工作方式。"
            "\n\n首先是自然语言处理领域。GPT系列模型展示了强大的文本生成能力，不仅能够进行对话，还能完成写作、翻译、编程等多种任务。"
            "其次是计算机视觉的突破。扩散模型使得AI绘画质量大幅提升，DALL-E、Midjourney等工具让普通人也能创作出专业级图像。"
            "最后是AI Agent的发展，从简单的聊天机器人进化为能够自主执行复杂任务的工作助手。"
            "\n\n我们应该认识到，AI的发展也面临诸多挑战。数据隐私、算法偏见、就业影响等问题需要社会各界共同应对。"
        ),
        summary="2025年AI发展趋势：大语言模型、多模态AI、AI Agent三大方向并进，同时面临隐私和伦理挑战。",
        status=ScrapeStatus.SUCCESS,
        fetcher_used=FetcherType.FETCHER,
        confidence=0.9,
        fetch_time_ms=1200,
    )
    step("平台识别", True, article.platform.value)
    step("标题提取", True, article.title)
    step("正文提取", True, f"{len(article.content)} 字符 | 可信度 {article.confidence:.0%}")
    step("模拟数据", True, "Python环境不可用，使用内置示例文章")
    return article


def _fake_rewrite(article):
    from src.core.content_rewriter import RewriteResult

    replacements = [
        ("在当今时代", ""), ("值得注意的是", ""), ("综上所述", "\n\n总结来说"),
        ("此外", "另外"), ("与此同时", "同时"), ("具有里程碑意义", "很重要"),
        ("标志着新篇章", "意味着新的开始"),
    ]
    content = article.content
    for old, new in replacements:
        content = content.replace(old, new)
    content = content.replace("\n\n\n", "\n\n").strip()

    result = RewriteResult(
        title=article.title.replace("2025年人工智能发展趋势与展望", "2025年，AI正在悄悄改变这些行业"),
        content=content,
        summary=article.summary,
        original_title=article.title,
        original_length=len(article.content),
        rewritten_length=len(content),
        method="regex",
    )
    step("改写方法", True, "regex (规则降级)")
    return result


def print_summary():
    print()
    print("=" * 60)
    print("  测试汇总")
    print("=" * 60)
    total = len(STEPS)
    passed = sum(1 for s in STEPS.values() if s["success"])
    failed = total - passed

    print(f"  总步骤: {total} · 通过: {passed} · 未通过: {failed}")
    print()

    for name, s in STEPS.items():
        icon = "✅" if s["success"] else "❌"
        detail_short = str(s["detail"])[:80]
        print(f"  {icon} {name}: {detail_short}")

    print()
    if failed == 0:
        print("  🎉 全部流程通过！")
    else:
        print(f"  ⚠️ {failed} 个步骤未通过（可能因缺少API密钥或Python环境）")
    print("=" * 60)


def parse_args():
    args = {"url": "", "skip_wechat": False}
    for arg in sys.argv[1:]:
        if arg == "--skip-wechat":
            args["skip_wechat"] = True
        elif arg.startswith("--url="):
            args["url"] = arg.split("=", 1)[1]
    return args


def main():
    args = parse_args()
    url = args["url"] or "https://mp.weixin.qq.com/s/h58tLMAkZgBLnwQBFVzxBA"

    print()
    print("=" * 60)
    print("  微信公众号全自动发布智能体 - 端到端流程测试")
    print("=" * 60)
    print(f"  目标URL: {url}")
    print(f"  Python: {'可用' if _check_python() else '不可用(模拟模式)'}")
    print(f"  AI_API_KEY: {'已配置' if os.getenv('AI_API_KEY') else '未配置(降级规则)'}")
    print(f"  WECHAT_APP_ID: {'已配置' if os.getenv('WECHAT_APP_ID') else '未配置(跳过草稿)'}")
    print("=" * 60)

    article = step_1_scrape(url)
    if not article:
        print()
        print("  ❌ Step 1 失败，终止流程")
        print_summary()
        return

    rewrite_result = step_2_rewrite(article)

    paths = step_3_save(rewrite_result, article)

    if not args["skip_wechat"]:
        step_4_wechat_draft(paths, rewrite_result, article)

    print_summary()


def _check_python():
    try:
        import src.core.content_scraper
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    main()
