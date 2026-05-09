# 微信公众号全自动发布智能体

基于AI的微信公众号全流程自动化发布系统，实现从内容策划、AI生成、自动排版到定时发布的全链路自动化。

## 功能特性

- **AI内容生成**：基于大语言模型，根据主题/关键词自动生成高质量文章
- **多风格支持**：新闻资讯、深度分析、教程指南、故事叙述等多种写作风格
- **自动排版**：Markdown到微信公众号富文本的自动转换
- **智能发布**：通过微信公众号API实现自动发布
- **人工审核**：发布前支持人工审核确认，确保内容质量
- **定时调度**：支持Cron表达式设置定时发布计划

## 快速开始

### 环境要求
- Python >= 3.10
- 微信公众号AppID和AppSecret

### 安装

```bash
# 克隆项目
git clone <repo-url>
cd 微信公众号自动发文

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp config/.env.example .env
# 编辑 .env 填入你的API密钥
```

### 使用

```bash
# 交互模式
python src/main.py interactive

# 直接生成并发布
python src/main.py generate --topic "AI最新发展" --style professional
```

## 项目结构

```
微信公众号自动发文/
├── docs/               # 项目文档
│   ├── project_rules.md
│   ├── requirements.md
│   └── tasks.md
├── src/                # 源代码
│   ├── core/           # 核心模块
│   ├── services/       # 服务层
│   ├── models/         # 数据模型
│   └── utils/          # 工具函数
├── tests/              # 测试
├── config/             # 配置文件
├── data/               # 数据目录
└── scripts/            # 脚本
```

## 开发状态

当前版本：v0.1.0 (项目初始化阶段)

详见 [docs/tasks.md](docs/tasks.md) 了解开发进度。

## 许可证

MIT License
