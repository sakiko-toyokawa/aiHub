# 🤖 AI Knowledge Hub

一个自动化的 AI 知识聚合平台，从多个社交平台抓取 AI 相关内容，使用 AI 进行智能总结，并通过邮件定时推送。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)
![React](https://img.shields.io/badge/React-18+-61DAFB.svg)

## ✨ 功能特性

- 🔍 **多平台抓取**: 支持 GitHub、知乎、Bilibili、X (Twitter)
- 🤖 **AI 智能总结**: 支持 OpenAI、Claude、DeepSeek、GLM、Kimi、MiniMax 等多个 AI 服务商
- 📧 **每日邮件推送**: 每晚 10 点自动发送当日摘要
- 🎨 **X 风格界面**: 现代化的深色主题设计
- 📊 **知识管理**: 收藏、标记已读、标签筛选
- ⏰ **定时调度**: 自动抓取和总结，无需人工干预

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Knowledge Hub                         │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐
│  React UI    │  │  FastAPI     │  │   Background Worker     │
│  (Dashboard) │──│  (REST API)  │──│   (Scheduler+Crawler)   │
└──────────────┘  └──────────────┘  └─────────────────────────┘
                          │                    │
                          ▼                    ▼
                   ┌──────────────┐   ┌──────────────┐
                   │ PostgreSQL   │   │ Playwright   │
                   │ (数据存储)    │   │ (网页抓取)   │
                   └──────────────┘   └──────────────┘
```

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd ai-knowledge-hub
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Keys 和账号信息
```

### 3. 使用 Docker Compose 启动

```bash
docker-compose up -d
```

### 4. 访问应用

- 前端界面: http://localhost:3000
- API 文档: http://localhost:8000/docs

## 🛠️ 技术栈

### 后端
- **FastAPI**: 高性能 Web 框架
- **SQLAlchemy + Alembic**: ORM 和数据库迁移
- **PostgreSQL**: 数据持久化
- **Playwright**: 网页抓取
- **LiteLLM**: 多 AI 服务商统一接口
- **APScheduler**: 定时任务调度
- **FastAPI-Mail**: 邮件发送

### 前端
- **React 18**: UI 框架
- **Tailwind CSS**: 样式
- **Framer Motion**: 动画
- **TanStack Query**: 数据获取和缓存
- **Lucide React**: 图标

## 📁 项目结构

```
ai-knowledge-hub/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy 模型
│   │   ├── routers/         # API 路由
│   │   ├── schemas/         # Pydantic 模型
│   │   └── main.py          # FastAPI 入口
│   ├── crawler/             # 爬虫模块
│   ├── summarizer/          # AI 总结模块
│   ├── scheduler/           # 定时任务
│   └── notifier/            # 邮件通知
├── frontend/
│   ├── src/
│   │   ├── components/      # UI 组件
│   │   ├── pages/           # 页面
│   │   └── types/           # TypeScript 类型
│   └── Dockerfile
└── docker-compose.yml
```

## ⚙️ 配置说明

### AI API Keys

在 `.env` 文件中配置至少一个 AI 服务商的 API Key:

```env
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
DEEPSEEK_API_KEY=sk-xxx
GLM_API_KEY=xxx
KIMI_API_KEY=sk-xxx
MINIMAX_API_KEY=xxx
```

### 平台账号

```env
# 知乎 Cookie
ZHIHU_COOKIE=z_c0=xxx

# Bilibili SESSDATA
BILIBILI_SESSDATA=xxx

# Twitter 账号
TWITTER_USERNAME=xxx
TWITTER_PASSWORD=xxx
```

### 邮件配置

```env
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
SMTP_USER=your_email@qq.com
SMTP_PASSWORD=your_auth_code
EMAIL_TO=recipient@example.com
```

## 📝 API 文档

启动后端后访问: http://localhost:8000/docs

### 主要接口

- `GET /api/summaries` - 获取总结列表
- `GET /api/summaries/{id}` - 获取单条详情
- `POST /api/summaries/{id}/read` - 标记已读
- `POST /api/summaries/{id}/favorite` - 收藏/取消收藏
- `GET /api/sources` - 获取数据源列表
- `GET /api/stats` - 获取统计数据

## 🎨 界面预览

### Dashboard
- X 风格深色主题
- 平台筛选标签
- 无限滚动内容流

### Summary Detail
- AI 总结高亮显示
- 关键要点展示
- 原文链接

### Settings
- AI 服务商配置
- 平台账号管理
- 邮件设置
- 调度配置

## 🧪 测试

```bash
cd backend
pytest -v
```

## 🚢 部署

### 使用 Docker Compose

```bash
docker-compose up -d
```

### 手动部署

1. 安装 PostgreSQL
2. 安装 Python 3.11+
3. 安装 Node.js 20+
4. 配置环境变量
5. 启动后端: `cd backend && uvicorn app.main:app`
6. 启动前端: `cd frontend && npm run dev`

## 📜 许可证

MIT License

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/)
- [Playwright](https://playwright.dev/)
- [LiteLLM](https://litellm.ai/)
- [Tailwind CSS](https://tailwindcss.com/)
