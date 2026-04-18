# AI Agent Command Palette 实施进度

> 项目：为前端增加命令面板式 AI 助手，分 5 个阶段 + 基础设施阶段逐步完成。

---

## 双主题系统（2026-04-17 新增）

### 已完成
- [x] **ThemeProvider** (`frontend/src/components/ThemeProvider.tsx`)
  - 支持 `light` / `dark` / `system` 三种模式
  - `system` 模式：自动跟随系统偏好 + 时间（6:00-18:00 亮色，其余暗色）
  - 手动切换：通过 `toggleTheme()` 或 `setTheme()`
  - 持久化：localStorage 保存用户选择
  - 提供 `useTheme()` hook
- [x] **CSS 变量双主题系统**
  - `:root` — Anthropic 亮色主题：暖白背景 #FAFAF8、Terracotta 橙强调色 #D97757、大量留白、圆角 0.75rem
  - `[data-theme="dark"]` — X 暗色主题：纯黑 #000000、X 蓝强调色 #1D9BF0、紧凑 pill 按钮
  - Tailwind `x-*` 颜色全部改为 CSS 变量引用
  - 引入 Geist Sans/Mono、Newsreader、Noto Serif SC 字体
  - 亮色模式添加径向渐变背景增强氛围
- [x] **主题切换 UI**
  - Layout 侧边栏新增"白天/夜间模式"切换按钮
  - 移动端头部也添加主题切换按钮
  - 使用 Sun/Moon 图标，颜色分别对应主题强调色
- [x] **组件适配**
  - 所有硬编码 `red-400`、`green-500`、`yellow-500` 替换为 `x-red`、`x-green`、`x-yellow`
  - 所有组件自动响应主题切换，无需额外条件类名

### 验证 Checklist
- [ ] 切换主题按钮在侧边栏和移动端均可见
- [ ] 亮色模式下背景为暖白色、强调色为 terracotta 橙
- [ ] 暗色模式下背景为纯黑、强调色为 X 蓝
- [ ] `system` 模式下，白天自动切换亮色、晚上自动切换暗色
- [ ] 刷新页面后，上次选择的主题被正确恢复

---

## 爬虫策略优化（2026-04-17 新增）

### 已完成
- [x] **关键词权重评分系统** (`backend/crawler/base.py`)
  - `AI_KEYWORD_WEIGHTS` 字典：agent/智能体=10, langchain/langgraph=9, MCP/RAG=8, LLM/大模型=7, ai/人工智能=3
  - `score_ai_relevance(text)` 返回 0-100 分数，累加命中关键词权重
  - `is_ai_related()` 改为基于阈值判断（默认 `SCORE_THRESHOLD = 15`）
  - `filter_ai_content()` 按分数降序排序，高相关内容优先
- [x] **各平台搜索词权重化**
  - GitHub: `TRENDING_TOPICS` 改为 weighted dict，按权重随机抽样
  - 知乎: `AI_TOPICS` 改为 weighted dict，移除 `_is_ai_related()` 重写
  - Bilibili: `SEARCH_KEYWORDS` 改为 weighted dict
- [x] **源强制覆盖策略** (`backend/scheduler/jobs.py`)
  - `run_crawl_job()` 中每个平台抓取后检查结果数
  - 若为 0 且平台配置有效，自动触发 `fetch(expanded=True)` 扩展抓取
  - 扩展模式：更多搜索词、更大时间窗口、更低质量门槛、更多采样
- [x] **增量抓取 - 内容哈希去重**
  - `CrawlResult` 增加 `content_hash` 字段
  - `RawContent` 表增加 `content_hash` 列（带索引）
  - `BaseCrawler.compute_hash()` 对 title+content 做 MD5
  - `run_crawl_job()` 保存前检查 hash 是否已存在，存在则跳过
  - 兼容旧数据库：若列不存在则跳过 hash 检查并记录警告
- [x] **扩展抓取支持** (`anthropic/builderio/hackernews` crawlers)
  - 所有爬虫支持 `expanded=True` 参数
  - 扩展模式下增加抓取数量/采样数

### 验证 Checklist
- [ ] 运行 `run_crawl_job()`，确认每个激活平台产出 >= 1 条
- [ ] 检查日志中出现 "扩展抓取成功" 或 "扩展抓取后仍无内容"
- [ ] 确认数据库 `raw_contents` 表中 `content_hash` 已填充
- [ ] 手动测试 `score_ai_relevance("Building an AI agent with LangChain")` >= 15

---

## 阶段0：基础设施搭建 ✅
- [x] 创建 `frontend/src/types/agent.ts`（AgentAction、PaletteState 类型）
- [x] 创建 `frontend/src/components/CommandPaletteProvider.tsx`（全局 Provider + Cmd/Ctrl+K 监听）
- [x] 创建 `frontend/src/components/CommandPalette.tsx`（面板壳子：输入框、loading/error 展示）
- [x] 创建 `frontend/src/hooks/useAgentExecutor.ts`（执行器框架）
- [x] 创建 `backend/app/routers/agent.py`（`POST /api/agent/parse` 路由）
- [x] 修改 `backend/summarizer/llm_client.py`（新增通用 `chat()` 方法）
- [x] 修改 `backend/app/main.py`（注册 agent router）
- [x] 修改 `frontend/src/main.tsx`（包裹 `<CommandPaletteProvider>`）
- [x] 修改 `frontend/src/components/Layout.tsx`（搜索栏替换为面板触发器）

## 阶段1：接入内容管理功能 ✅
- [x] 在 `useAgentExecutor.ts` 填充 `list_summaries` / `get_summary` / `mark_read` / `toggle_favorite` / `delete_summary` / `cleanup`
- [x] 在 `CommandPalette.tsx` 增加快捷操作："查看全部摘要"、"标记第一条为已读"、"清理旧摘要"
- [x] 在 `agent.py` prompt 中增加内容管理 action 说明
- [x] 实现 `delete_summary` / `cleanup` 的二次确认弹层

## 阶段2：接入爬虫与任务功能 ✅
- [x] 补齐 `frontend/src/api/client.ts`：`crawlerApi.getTaskStatus(task_id)`、`crawlerApi.listTasks()`
- [x] 在 `useAgentExecutor.ts` 填充 `trigger_crawl` / `get_crawl_status` / `list_tasks`
- [x] 在 `CommandPalette.tsx` 增加快捷操作："立即抓取"
- [x] 在 `agent.py` prompt 中增加爬虫相关 action 说明

## 阶段3：接入数据源管理功能 ✅
- [x] 在 `useAgentExecutor.ts` 填充 `list_sources` / `toggle_source_active`
- [x] 在 `CommandPalette.tsx` 增加快捷操作："列出所有数据源"
- [x] 在 `agent.py` prompt 中增加数据源相关 action 说明

## 阶段4：接入统计与洞察功能 ✅
- [x] 补齐 `frontend/src/api/client.ts`：`statsApi.getTrendingTags(limit)`
- [x] 在 `useAgentExecutor.ts` 填充 `get_stats` / `get_trending_tags`
- [x] 在 `CommandPalette.tsx` 增加快捷操作："查看统计"、"热门标签"
- [x] 在 `agent.py` prompt 中增加统计相关 action 说明

## 阶段5：接入系统配置功能 ✅
- [x] 在 `useAgentExecutor.ts` 填充 `get_config` / `update_config` / `test_email` / `get_providers` / `get_provider_models`
- [x] 在 `CommandPalette.tsx` 增加快捷操作："发送今日摘要"、"查看配置"
- [x] 在 `agent.py` prompt 中增加配置相关 action 说明

---

## 通用约束检查清单 ✅
- [x] 前端无 mock / 假数据
- [x] 前端 API 调用均通过 `src/api/client.ts`
- [x] 数据获取处理了 loading / error / empty 状态
- [x] 破坏性操作（删除、清理）有二次确认
- [x] 后端 pip 安装使用了清华镜像

---

## 功能扩展规划（2026-04-18 头脑风暴）

### 一、核心知识管理

| 功能 | 现有基础 | 改动量 | 优先级 |
|---|---|---|---|
| **个人笔记/批注** | `UserRead` 关联表已有 | 加 1 个字段 `notes` + 1 个 API + 前端 textarea | **P0** ✅ |
| **全文搜索接入 Command Palette** | summaries API 已有 search 参数，但前端未接 | 搜索能力接入面板 + 高亮 + 键盘导航 | **P1** |
| **相似内容推荐** | `tags` / `key_points` 都有 | 同标签/关键词 SQL 推荐，详情页底部展示 | **P1** |
| **阅读进度** | `UserRead.is_read` 是布尔 | 改为 `read_progress` 百分比 | **P2** |

### 二、数据源扩展

| 功能 | 说明 | 改动量 |
|---|---|---|
| **自定义 RSS 源** | `BaseCrawler` 是抽象基类，加 `RssCrawler` | 中等 |
| **Reddit / Product Hunt** | 和现有 GitHub/Zhihu 爬虫模式一致 | 中等 |
| **语义去重** | 已有 `content_hash` MD5 去重，可升级为 embedding | 较大 |

### 三、AI 增强

| 功能 | 说明 | 改动量 |
|---|---|---|
| **AI 问答（RAG Lite）** | SQLite + 简单向量搜索，不用 Pinecone | 较大 |
| **要点高亮** | 总结时让 AI 标出最关键一句，前端 `<mark>` | 小 |
| **多摘要对比 / 变更摘要** | 同一来源多次抓取时生成 diff | 中等 |
| **人工修正标签** | AI 生成 tags 加人工反馈回路 | 小 |

### 四、输出与同步

| 功能 | 说明 | 改动量 |
|---|---|---|
| **Notion/Obsidian 同步** | API Router 加 `/api/integrations/notion` | 中等 |
| **RSS 输出** | 收藏内容生成 RSS feed | 小 |
| **每日精选邮件美化** | 已有邮件通知，升级为 Newsletter 模板 | 小 |

### 五、体验升级

| 功能 | 说明 | 改动量 |
|---|---|---|
| **无限滚动** | 替换现有分页 | 小 |
| **键盘快捷键** | `j/k` 导航、`f` 收藏、`r` 标记已读 | 小 |
| **PWA / 离线阅读** | Service Worker 缓存已读摘要 | 中等 |
| **跟随系统主题** | `matchMedia('prefers-color-scheme')` | 小 |

### 建议优先做的三个

1. **笔记批注** — ROI 最高，改动最小，产品从"阅读器"升级为"知识库"
2. **RSS 自定义源** — 已有爬虫框架，用户可自己添加 niche 信息源
3. **AI 问答（RAG Lite）** — 体验质变，用现有 SQLite + 本地 embedding 即可实现
