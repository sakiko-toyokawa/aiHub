# AI Knowledge Hub

一个聚合多平台 AI 相关内容（GitHub、知乎、Bilibili、Twitter）并提供 AI 总结的知识管理平台。

---

## ⚠️ 关键约束

违反以下规则将导致过度设计、无关改动或返工：

1. **前端严禁使用 Mock 数据** — 所有数据必须通过真实 API 获取
2. **前端必须使用 pnpm** — 严禁使用 npm 或 yarn
3. **后端 pip 必须使用清华镜像源** — `https://pypi.tuna.tsinghua.edu.cn/simple`
4. **测试类严禁接入前端** — 前端不得调用任何 `/api/test`、`/api/debug` 或测试模块

---

## 🧭 场景导航

| 如果你正在做... | 先读取 |
|---|---|
| 前端页面开发 / 组件审查 | [`.claude/rules/frontend.md`](.claude/rules/frontend.md) |
| 后端业务开发 / 代码审查 | [`.claude/rules/backend.md`](.claude/rules/backend.md) |
| 新增 / 修改 API 接口 | [`.claude/rules/interaction.md`](.claude/rules/interaction.md) |
| 编写或执行测试 | [`.claude/rules/testing.md`](.claude/rules/testing.md) |
| PR 审查（重点关注假数据与数据流） | [`.claude/skills/pr-review.md`](.claude/skills/pr-review.md) |
| 了解架构决策与技术选型 | [`docs/architecture.md`](docs/architecture.md) |

---

## 📁 目录索引

```
ai-knowledge-hub/
├── CLAUDE.md                 # 项目约定与索引
├── backend/                  # FastAPI 后端
│   ├── app/                  # API 路由、模型、Schema
│   ├── crawler/              # 各平台爬虫实现
│   ├── scheduler/            # APScheduler 定时任务
│   ├── summarizer/           # LiteLLM AI 总结
│   ├── notifier/             # 邮件通知
│   ├── data/                 # SQLite 数据文件
│   └── scripts/              # 运维脚本
├── frontend/                 # React 前端
│   ├── src/
│   │   ├── api/              # API 客户端封装
│   │   ├── components/       # 可复用组件
│   │   ├── pages/            # 页面级组件
│   │   └── types/            # TypeScript 类型定义
│   └── index.html
├── docs/                     # 人类可读的详细文档
└── .claude/                  # Claude Code 配置
    ├── rules/                # 条件加载的规范
    ├── skills/               # 可复用技能模块
    ├── memory/               # 工作记忆
    └── settings.json         # hooks 与权限配置
```

---

## 🛠️ 技术栈速览

- **前端**: React 18 + TypeScript + Vite + Tailwind CSS + TanStack Query
- **后端**: FastAPI + SQLAlchemy + SQLite + APScheduler
- **爬虫**: Playwright + 各平台第三方库/API
- **AI 总结**: LiteLLM（统一多服务商接口）

---

## 🚀 常用命令

```bash
# 启动后端
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动前端
cd frontend
pnpm run dev

# 构建前端
pnpm run build
```

---

## 📝 工作记忆约定

- **当日工作流** → 写入 `.claude/memory/daily/YYYY-MM-DD.md`
- **重要技术决策 / 会话总结** → 写入 `.claude/memory/sessions/{主题}.md`
- **进度更新** → 修改 `.claude/memory/progress.md`

---

## ✅ 提交前检查清单

- [ ] 前端无 mock / 假数据 / 硬编码 stats
- [ ] 前端 API 调用均通过 `src/api/client.ts`
- [ ] 无嵌套 `<a>` 标签
- [ ] 所有数据获取处理了 loading / error / empty 状态
- [ ] 前端 types 与后端 API 返回一致
- [ ] 后端 pip 安装使用了清华镜像
