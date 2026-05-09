## 常见坑与解决方案

### 坑1：Python 环境问题

**症状**：`pip install` 报错 或者 `python` 命令找不到

**解决**：
1. 确认 Python 已安装且加入 PATH：在命令行输入 `python --version`
2. 如果报错"无法识别"，重新安装 Python 并勾选"Add Python to PATH"
3. 确保在虚拟环境中执行：命令行前面有 `(venv)` 标识
4. 如果虚拟环境无法激活，尝试用 `python -m venv venv --clear` 重建

### 坑2：Playwright 安装失败

**症状**：运行爬虫时报 `playwright._impl._api_types.Error: Executable doesn't exist`

**解决**：
```powershell
# 手动安装 Chromium 浏览器
playwright install chromium

# 如果下载太慢，可以设置镜像
set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/
playwright install chromium
```

### 坑3：微信 Access Token 获取失败

**症状**：`{"errcode": 40125, "errmsg": "invalid appsecret"}`

**解决**：
1. 检查 `.env` 文件中 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET` 是否正确（注意不要有多余空格）
2. AppSecret 是否已经重置过（微信公众号后台 → 设置与开发 → 基本配置 → 重置）
3. IP白名单是否配置（如果是企业号，需要在后台配置服务器IP白名单）

### 坑4：微信草稿创建失败

**症状**：`{"errcode": 40007, "errmsg": "invalid media_id"}` 或其他错误码

**常见错误码对照**：
| 错误码 | 含义 | 解决 |
|--------|------|------|
| 40007 | media_id无效 | 封面图上传失败或media_id过期 |
| 40001 | Access Token无效 | 重新获取Token |
| 45009 | 接口调用频率超限 | 等待后重试 |
| 45103 | 文章标题过长 | 标题限制64个字符(32个汉字) |

### 坑5：AI返回的 JSON 格式不对

**症状**：`json.decoder.JSONDecodeError`

**解决**：
1. 在 `_call_llm` 方法中已经做了清理（去掉 ```json``` 标记）
2. 如果仍然失败，尝试降低 temperature（如改为 0.3）
3. 在 Prompt 中加入更多格式示例
4. 如果模型能力不足（比如用了太便宜的模型），偶尔会输出不规范的JSON，可以尝试换一个更强的模型。

### 坑6：文章抓取失败（403/空内容）

**症状**：抓取微信文章返回空内容或 403 错误

**解决**：
1. 微信文章**必须**用 Playwright 的浏览器模式抓取（`_fetch_dynamic`），普通 requests 获取不到内容
2. 某些文章需要登录才能查看，这类文章无法直接抓取
3. 微信号如果被封禁过，部分文章会受限
4. 解决方案：使用隐身模式（StealthyFetcher）或更换 User-Agent

### 坑7：环境变量加载失败

**症状**：`WECHAT_APP_ID` 或 `AI_API_KEY` 获取不到

**解决**：
1. 确认 `.env` 文件在项目根目录且格式正确（`KEY=value`，没有引号）
2. 确认代码中使用了 `load_dotenv()` 加载
3. 注意 `.env` 中的值不要加引号：`AI_API_KEY=sk-abc123` ✅ 而非 `AI_API_KEY="sk-abc123"` ❌

### 坑8：中文乱码问题

**症状**：发布到微信的文章出现乱码

**解决**：
在 `create_draft` 中使用 `json.dumps(payload, ensure_ascii=False).encode("utf-8")` 手动序列化，不要用 `requests.post(url, json=payload)` 的自动序列化（会导致中文被转义成 `\uXXXX`）。

---

## 进阶优化方向

当你成功跑通基础流程后，可以考虑以下进阶优化：

### 1. 多内容源支持
目前只接入了微信公众号，可以扩展到：
- 知乎文章
- 今日头条
- 百度百家号
- 36氪 / 虎嗅

只需在 `platform_router.py` 中添加对应的 URL 识别规则和 CSS 选择器。

### 2. 模型切换
本教程默认使用 DeepSeek 和 Kimi，如果你想换成其他模型（只要支持 OpenAI 兼容接口就行），只需修改 `.env` 中的 `AI_API_BASE` 和 `AI_MODEL` 两行配置，代码不需要改。

### 3. 定时自动发布
在 `scripts/` 下添加一个定时任务脚本，配合 Windows 的"任务计划程序"或 Linux 的 `cron`：
- 每天早上 8 点自动抓取热门文章
- 自动改写
- 自动发布

### 4. 发布前端界面
用 Flask 或 Streamlit 做一个简单的 Web 界面：
- 输入文章链接
- 预览改写结果
- 一键发布

### 5. 更丰富的排版
- 代码高亮
- 表情包插入
- 引导关注/点赞的模板
- 文末"推荐阅读"模块

### 6. 数据分析
- Token 消耗统计（控制成本）
- 发布成功率
- 文章阅读量追踪（需要额外接入微信数据统计API）

---

## 总结

恭喜你！如果你跟着教程一步步做完了，你现在拥有一个：

- ✅ 能自动抓取微信公众号文章（模式一：洗稿）
- ✅ 能根据主题自动搜索资料并原创生成文章（模式二：主题原创）
- ✅ 能用 AI 深度改写去 AI 味
- ✅ 能搜索无版权图片或 AI 生成封面图
- ✅ 能自动检查内容合规性
- ✅ 能自动创建草稿并发布到微信公众号
- ✅ 能通过 MCP 协议让 AI 助手直接调用

的**全自动发文智能体**。

> **最后想说**：这个系统的灵魂不是代码，而是 **Prompt（提示词）**。不管是洗稿别人的好文章，还是根据主题从零原创，花时间打磨你的 Prompt，让 AI 的写作风格无限接近你自己的风格，这才是做出差异化内容的关键。代码只是骨架，Prompt 才是血肉。

如果你在搭建过程中遇到任何问题，欢迎随时向 AI 助手提问！

---

*文档版本：v1.1 | 更新日期：2026年5月*

