# 项目开发规则

## 1. 技术栈规范

| 层级 | 技术选型 | 版本要求 |
|------|---------|---------|
| 语言 | Python | >= 3.10 |
| AI框架 | LangChain / 自研 Agent | 最新稳定版 |
| LLM服务 | OpenAI API / 国内大模型 | GPT-4 / Claude / 文心一言 |
| 数据库 | SQLite (开发) / PostgreSQL (生产) | - |
| 配置管理 | python-dotenv + YAML | - |
| 日志 | loguru | - |
| 测试 | pytest + pytest-cov | - |
| 代码检查 | ruff + mypy | - |

## 2. 代码规范

### 2.1 命名规范
- 文件名：小写下划线 `wechat_service.py`
- 类名：大驼峰 `WeChatPublisher`
- 函数/方法：小写下划线 `publish_article()`
- 常量：大写下划线 `MAX_RETRY_COUNT`
- 私有成员：单下划线前缀 `_internal_method()`

### 2.2 类型注解
- 所有公共函数必须有完整类型注解
- 使用 `from __future__ import annotations` 启用延迟注解
- 复杂类型使用 `typing` 模块（Optional, Union, Literal 等）

### 2.3 文档字符串
- 使用 Google 风格的 docstring
- 每个公共模块、类、方法都必须有文档字符串
- 关键业务逻辑必须添加行内注释说明

### 2.4 代码格式化
- 使用 ruff 进行代码检查和格式化
- 行宽限制：120 字符
- 缩进：4 空格
- 文件编码：UTF-8

## 3. 项目结构规范

```
微信公众号自动发文/
├── docs/                    # 项目文档
│   ├── project_rules.md     # 开发规则(本文档)
│   ├── requirements.md      # 需求规格说明书
│   └── tasks.md             # 开发任务清单
├── src/                     # 源代码
│   ├── __init__.py
│   ├── main.py              # 程序主入口
│   ├── core/                # 核心模块
│   │   ├── __init__.py
│   │   ├── agent.py         # 智能体主逻辑
│   │   ├── content_generator.py  # 内容生成模块
│   │   └── publisher.py     # 发布模块
│   ├── services/            # 外部服务集成
│   │   ├── __init__.py
│   │   ├── wechat_service.py    # 微信公众号API
│   │   └── ai_service.py        # AI模型服务
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic数据模型
│   └── utils/               # 工具模块
│       ├── __init__.py
│       ├── config.py        # 配置加载
│       └── logger.py        # 日志配置
├── tests/                   # 测试
│   ├── __init__.py
│   ├── conftest.py          # pytest fixtures
│   ├── test_agent.py
│   ├── test_content_generator.py
│   └── test_publisher.py
├── config/                  # 配置文件
│   ├── config.yaml          # 应用配置
│   └── .env.example         # 环境变量模板
├── data/                    # 数据目录
│   ├── drafts/              # 草稿数据
│   ├── published/           # 已发布记录
│   └── templates/           # 模板文件
├── scripts/                 # 工具脚本
│   └── run.py               # 启动脚本
├── .gitignore
├── requirements.txt
└── README.md
```

## 4. Git 工作流规范

### 4.1 分支策略
- `main`：生产分支，始终可部署
- `develop`：开发主分支
- `feature/*`：功能分支，从 develop 切出
- `fix/*`：修复分支
- `release/*`：发布分支

### 4.2 Commit 规范
使用 Conventional Commits 格式：
- `feat: 新功能描述`
- `fix: 修复描述`
- `docs: 文档更新`
- `refactor: 重构描述`
- `test: 测试相关`
- `chore: 构建/工具变更`

### 4.3 代码审查
- 所有代码必须经过 PR 审查后合并
- PR 描述必须包含变更说明和测试情况
- 合并前必须通过 CI 检查（lint + test）

## 5. 安全规范

### 5.1 密钥管理
- 所有密钥/Token 必须通过环境变量获取，严禁硬编码
- `.env` 文件不得提交到 Git
- 使用 `.env.example` 作为配置模板
- 生产环境密钥通过密钥管理服务注入

### 5.2 API安全
- 所有外部API调用必须实现重试机制和超时设置
- 敏感API请求必须添加请求签名验证
- API响应必须验证数据完整性

### 5.3 数据安全
- 用户数据（Access Token、文章内容）必须加密存储
- 日志不得包含敏感信息（Token、密码等）
- 数据库访问必须使用参数化查询

## 6. AI集成规范

### 6.1 模型调用
- 所有LLM调用必须设置 `temperature`、`max_tokens` 参数
- 必须实现请求重试（指数退避）和速率限制
- 长文本生成必须分批处理，避免Token超限
- 必须记录每次调用的Token消耗和成本

### 6.2 Prompt管理
- 所有Prompt模板统一管理，不可散落在代码中
- Prompt必须版本化管理
- 输出格式必须通过Few-shot示例约束
- 必须对AI输出进行格式校验和内容安全审核

### 6.3 容错与降级
- AI服务不可用时必须有降级策略
- 生成内容质量不达标时自动重试或人工审核
- 关键决策点保留人工确认环节

## 7. 测试规范

### 7.1 测试覆盖率
- 核心业务逻辑测试覆盖率 >= 80%
- 工具类函数测试覆盖率 >= 90%
- 外部API调用必须Mock测试

### 7.2 测试分类
- 单元测试：测试独立函数和方法
- 集成测试：测试模块间交互
- 端到端测试：测试完整发布流程（使用测试公众号）

### 7.3 测试数据
- 使用 Fixture 管理测试数据
- 禁止在测试中使用真实API密钥
- 使用工厂模式生成测试数据

## 8. 日志与监控

### 8.1 日志规范
- 使用 loguru 统一日志输出
- 日志级别：DEBUG / INFO / WARNING / ERROR
- 关键操作必须记录（发布文章、API调用、错误）
- 日志文件按日期轮转，保留30天

### 8.2 监控指标
- 发布成功率
- AI响应时间
- Token消耗统计
- 错误率与类型分布

## 9. 部署规范

### 9.1 环境管理
- 使用虚拟环境（venv/conda）管理依赖
- requirements.txt 必须锁定版本号
- 区分开发/测试/生产环境配置

### 9.2 运行方式
- 支持命令行模式：`python src/main.py`
- 支持定时任务模式（cron/scheduled task）
- 支持交互模式（人工审核发布）
