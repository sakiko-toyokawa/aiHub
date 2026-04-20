/**
 * Agent 命令面板相关的类型定义
 *
 * 设计决策：采用混合解析架构（Hybrid）
 * - 简单命令在前端本地匹配，零延迟执行
 * - 复杂自然语言调用后端 LLM 解析为结构化 action
 * 这样可以在保证常见操作响应速度的同时，支持灵活的自然语言交互。
 */

/** Agent 解析出的动作类型 */
export type AgentActionType =
  // 内容管理（阶段1）
  | 'list_summaries'
  | 'get_summary'
  | 'mark_read'
  | 'toggle_favorite'
  | 'delete_summary'
  | 'cleanup'
  // 爬虫任务（阶段2）
  | 'trigger_crawl'
  | 'get_crawl_status'
  | 'list_tasks'
  // 数据源（阶段3）
  | 'list_sources'
  | 'toggle_source_active'
  // 统计洞察（阶段4）
  | 'get_stats'
  | 'get_trending_tags'
  // 系统配置（阶段5）
  | 'get_config'
  | 'update_config'
  | 'test_email'
  | 'get_providers'
  | 'get_provider_models'
  // AI 问答（RAG Lite）
  | 'ask_ai'
  // 兜底
  | 'unknown'
  | 'navigate'

/** 结构化动作对象 */
export interface AgentAction {
  type: AgentActionType
  params?: Record<string, unknown>
  message?: string // 给用户的友好提示
}

/** 后端 Agent 解析响应 */
export interface AgentParseResponse {
  action: AgentAction
}

/** 命令面板中展示的快捷操作 */
export interface QuickAction {
  id: string
  label: string
  description?: string
  icon?: string // lucide icon name
  action: AgentAction
}

/** RAG Lite 引用来源 */
export interface AskSource {
  summary_id: number
  title: string
  platform: string
  url: string
  relevance_score: number
}

/** RAG Lite 问答响应 */
export interface AgentAskResponse {
  answer: string
  sources: AskSource[]
}

/** 执行结果的统一封装 */
export interface AgentExecutionResult {
  success: boolean
  message: string
  data?: unknown
}

/** 命令面板的全局状态 */
export interface CommandPaletteState {
  isOpen: boolean
  input: string
  isLoading: boolean
  error: string | null
  result: AgentExecutionResult | null
}
