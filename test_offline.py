from src.core import ContentScraper
from skills.ai_drawing import AIDrawingSkills
from skills.content_compliance import ContentComplianceSkills
import os

# 1. 初始化模块
scraper = ContentScraper()
ai_drawer = AIDrawingSkills()
compliance_checker = ContentComplianceSkills()

# 2. 测试：抓取一篇公开的公众号文章（替换成你自己的测试链接）
test_url = "https://mp.weixin.qq.com/s/你的测试文章链接"
print(f"正在抓取：{test_url}")
article = scraper.scrape(test_url)
print(f"✅ 抓取成功！标题：{article.title}")
print(f"✅ 正文长度：{len(article.content)} 字")

# 3. 测试：AI改写（去AI味+口语化，保留核心观点）
from skills.chinese_rewriter import ChineseRewriter
rewriter = ChineseRewriter()
rewritten_content = rewriter.humanize(article.content, style="conversational", originality="high")
print(f"✅ 改写完成！新正文长度：{len(rewritten_content)} 字")

# 4. 测试：生成公众号封面图
cover_image_path = ai_drawer.generate_article_cover(article.title, style="minimal")
print(f"✅ 封面图生成成功！路径：{cover_image_path}")

# 5. 测试：内容合规校验
check_result = compliance_checker.full_check(rewritten_content)
print(f"✅ 合规校验结果：{check_result['status']}")
if check_result['violations']:
    print(f"⚠️ 检测到问题：{check_result['violations']}")

# 6. 测试：保存改写后的文章为Markdown文件（本地查看）
output_dir = "test_output"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, f"{article.title[:20]}_改写版.md")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(f"# {article.title}\n\n{rewritten_content}")
print(f"✅ 文章已保存到本地：{output_path}")
print("="*50)
print("🎉 离线测试全部完成！等公众号绑定好，再跑发布草稿的步骤即可")