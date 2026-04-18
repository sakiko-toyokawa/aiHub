# 计划：前端 AI Agent 命令面板（分阶段实现）

## 总体目标

为 AI Knowledge Hub 前端增加一个 **Command Palette（命令面板）** 式的 AI 助手入口。用户通过 `Cmd/Ctrl+K` 或点击顶部搜索栏呼出面板，输入自然语言命令或选择快捷操作，调用后端 API 完成操作。

## 架构方案（贯穿5个阶段）

采用**混合解析（Hybrid）**：
- **简单/快捷命令**：前端本地硬编码匹配，零延迟执行
- **复杂自然语言**：调用后端 `POST /api/agent/parse`，由 `LLMClient` 解析为结构化 action，前端执行对应 API

## 阶段0：基础设施搭建（所有后续阶段依赖）

### 目标
建立命令面板的基础 UI、全局状态、键盘监听、后端 Agent 解析路由。

### 新增文件
1. `frontend/src/types/agent.ts` — Agent 相关 TS 类型
2. `frontend/src/components/CommandPaletteProvider.tsx` — 全局 Provider，`Cmd/Ctrl+K` 监听
3. `frontend/src/components/CommandPalette.tsx` — 命令面板壳子（输入框、loading、error 状态展示）
4. `frontend/src/hooks/useAgentExecutor.ts` — action 执行器框架（先留空 switch case，后续阶段填充）
5. `backend/app/routers/agent.py` — `POST /api/agent/parse` 路由

### 修改文件
- `frontend/src/main.tsx` — 包裹 `<CommandPaletteProvider>`
- `frontend/src/components/Layout.tsx` — 搜索栏替换为命令面板触发器
- `backend/summarizer/llm_client.py` — 新增通用 `chat()` 方法
- `backend/app/main.py` — 注册 `agent` router

### 验证
- 按 `Ctrl+K` / `Cmd+K` 能呼出/关闭面板
- 后端 curl 测试 `"hello"` 返回 `unknown` action
- 无 mock 数据，无 TypeScript 报错

---

## 阶段1：接入内容管理功能

### 目标
在命令面板中支持摘要的查看、标记、收藏、删除、清理。

### 涉及的 Action
- `list_summaries` — 列出摘要（带筛选/分页）
- `get_summary` — 查看摘要详情
- `mark_read` — 标记已读
- `toggle_favorite` — 切换收藏
- `delete_summary` — 删除摘要（需二次确认）
- `cleanup` — 清理旧摘要（需二次确认）

### 修改文件
- `frontend/src/hooks/useAgentExecutor.ts` — 填充上述 6 个 case，调用 `summariesApi`
- `frontend/src/components/CommandPalette.tsx` — 增加快捷操作："查看全部摘要"、"标记第一条为已读"、"清理旧摘要"
- `backend/app/routers/agent.py` — prompt 中增加内容管理相关 action 说明

### 验证
- 输入"查看 GitHub 摘要" → 面板展示摘要列表
- 输入"标记第一条为已读" → 成功标记并刷新 Dashboard
- 选择"清理旧摘要" → 弹出确认 → 执行后展示删除数量
- 输入"删除摘要 5" → 确认后删除并刷新

---

## 阶段2：接入爬虫与任务功能

### 目标
在命令面板中支持手动触发爬虫、查看任务状态、列出历史任务。

### 涉及的 Action
- `trigger_crawl` — 异步触发抓取
- `get_crawl_status` — 查看指定任务状态
- `list_tasks` — 列出所有爬虫任务

### 新增/修改文件
- `frontend/src/api/client.ts` — 补齐缺失的 crawler API：
  - `crawlerApi.getTaskStatus(task_id)`
  - `crawlerApi.listTasks()`
- `frontend/src/hooks/useAgentExecutor.ts` — 填充上述 3 个 case
- `frontend/src/components/CommandPalette.tsx` — 增加快捷操作："立即抓取"
- `backend/app/routers/agent.py` — prompt 中增加爬虫相关 action 说明

### 验证
- 选择"立即抓取" → 面板显示"后台任务已启动"，Dashboard 稍后刷新
- 输入"查看抓取任务状态 xxx" → 展示任务进度
- 输入"列出所有抓取任务" → 展示任务列表

---

## 阶段3：接入数据源管理功能

### 目标
在命令面板中支持查看数据源列表、切换数据源的启用/暂停状态。

### 涉及的 Action
- `list_sources` — 列出所有数据源
- `toggle_source_active` — 切换数据源启用状态

### 修改文件
- `frontend/src/hooks/useAgentExecutor.ts` — 填充上述 2 个 case，调用 `sourcesApi`
- `frontend/src/components/CommandPalette.tsx` — 增加快捷操作："切换 GitHub 数据源"（前提是能获取到 source_id）
- `backend/app/routers/agent.py` — prompt 中增加数据源相关 action 说明

### 验证
- 输入"列出所有数据源" → 面板展示平台、URL、状态列表
- 输入"暂停知乎数据源" → 该数据源状态变为暂停，Sidebar 同步更新

---

## 阶段4：接入统计与洞察功能

### 目标
在命令面板中支持查看平台统计和热门标签。

### 涉及的 Action
- `get_stats` — 查看整体统计
- `get_trending_tags` — 查看热门标签

### 新增/修改文件
- `frontend/src/api/client.ts` — 补齐 `statsApi.getTrendingTags(limit)`
- `frontend/src/hooks/useAgentExecutor.ts` — 填充上述 2 个 case
- `frontend/src/components/CommandPalette.tsx` — 增加快捷操作："查看统计"、"查看热门标签"
- `backend/app/routers/agent.py` — prompt 中增加统计相关 action 说明

### 验证
- 输入"查看统计" → 面板展示总摘要数、已读数、收藏数、平台分布
- 输入"热门标签" → 面板展示前 N 个热门标签

---

## 阶段5：接入系统配置功能

### 目标
在命令面板中支持查看/修改配置、发送测试邮件、查看 AI 提供商和模型。

### 涉及的 Action
- `get_config` — 获取当前配置
- `update_config` — 更新配置项
- `test_email` — 发送测试邮件
- `get_providers` — 查看 AI 提供商列表
- `get_provider_models` — 查看指定提供商的模型

### 修改文件
- `frontend/src/hooks/useAgentExecutor.ts` — 填充上述 5 个 case，调用 `configApi`
- `frontend/src/components/CommandPalette.tsx` — 增加快捷操作："发送测试邮件"、"查看当前 AI 模型"
- `backend/app/routers/agent.py` — prompt 中增加配置相关 action 说明

### 验证
- 输入"查看配置" → 面板展示当前默认模型、邮件开关等
- 输入"发送测试邮件" → 面板提示"测试邮件已发送"
- 输入"查看 DeepSeek 有哪些模型" → 展示模型列表

---

## 跨阶段通用约束

1. **严禁 Mock 数据** — 所有结果必须来自真实 API
2. **API 调用走 `src/api/client.ts`** — 新增/补齐的方法必须在此文件中
3. **破坏性操作需二次确认** — `delete_summary`、`cleanup` 必须有确认弹层
4. **处理 loading/error/empty** — 每个 action 执行都要有状态反馈
5. **后端 pip 用清华镜像** — 若新增 Python 依赖
6. **不引入新依赖** — 优先复用现有 `framer-motion`、`lucide-react`、`TanStack Query`

---

## 进度追踪文件

计划完成后，将本计划的阶段列表转化为 `process.md` 待办事项：
- `process.md` 路径：`./claude/memory/process.md`
- 每个阶段对应一个可勾选的待办项
- 每个待办项包含：目标简述、关键文件、验证标准
- 实施过程中逐条更新完成状态
