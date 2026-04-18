# 架构决策记录

## 项目概述

AI Knowledge Hub 是一个自动化的 AI 知识聚合平台，从 GitHub、知乎、Bilibili、Twitter 等平台抓取 AI 相关内容，使用大模型进行智能总结，并通过邮件定时推送。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Vite + Tailwind CSS + TanStack Query |
| 后端 | FastAPI + SQLAlchemy 2.0 + SQLite + APScheduler |
| 爬虫 | Playwright + 平台特定第三方库（如 `bilibili-api-python`、`httpx`） |
| AI | LiteLLM（统一接口，支持 OpenAI / Claude / DeepSeek / GLM / Kimi / MiniMax） |
| 邮件 | FastAPI-Mail |
| 容器 | Docker Compose |

---

## 系统架构

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
                   │  SQLite      │   │ Playwright   │
                   │ (数据存储)    │   │ (网页抓取)   │
                   └──────────────┘   └──────────────┘
```

---

## 核心模块职责

### 前端 (`frontend/`)

| 目录/文件 | 职责 |
|-----------|------|
| `src/api/client.ts` | 统一 axios 实例及所有 API 封装 |
| `src/components/` | 可复用 UI 组件（Layout、Sidebar、SummaryCard 等） |
| `src/pages/` | 路由级页面（Dashboard、Favorites、SummaryDetail、Settings） |
| `src/types/index.ts` | TypeScript 类型定义 |

### 后端 (`backend/`)

| 目录 | 职责 |
|------|------|
| `app/routers/` | FastAPI 路由（summaries、sources、stats、config） |
| `app/models/` | SQLAlchemy 数据库模型 |
| `app/schemas/` | Pydantic 请求/响应校验模型 |
| `crawler/` | 各平台爬虫实现（GitHub、知乎、Bilibili、Twitter） |
| `summarizer/` | LLMClient，封装 LiteLLM 调用 |
| `scheduler/` | APScheduler 定时任务（抓取、总结、邮件） |
| `notifier/` | 邮件发送与日报生成 |
| `scripts/` | 初始化脚本（首次启动生成示例数据） |

---

## 数据流

1. **定时抓取**：APScheduler 每 2 小时触发爬虫，将原始内容写入 `raw_contents` 表
2. **定时总结**：APScheduler 每 3 小时读取未总结的原始内容，调用 LLM 生成摘要写入 `summaries` 表
3. **用户浏览**：前端通过 `/api/summaries/` 获取分页列表，支持平台筛选、收藏、已读标记
4. **定时邮件**：每晚 22:00 汇总当日高质摘要，发送 HTML 日报

---

## 关键设计决策

### 1. 使用 SQLite 作为默认数据库

- 降低本地开发和部署门槛
- 生产环境可通过环境变量切换为 PostgreSQL

### 2. 前端禁用 Mock 数据

- 所有数据必须走真实 API
- 开发时后端接口优先实现
- 确保错误处理和类型定义在真实环境中验证

### 3. 统一 AI 接口 via LiteLLM

- 通过 `summarizer/llm_client.py` 统一封装
- 新增 AI 服务商只需在配置中注册 provider 和 model，无需改动业务代码

### 4. 示例数据初始化

- `scripts/init_data.py` 在首次启动时自动运行
- 提供 3 个 source、5 条 raw content、5 条 summary，便于前端立刻看到效果
