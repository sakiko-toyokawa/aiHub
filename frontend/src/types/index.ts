export interface Summary {
  id: number
  raw_content_id?: number
  platform: string
  title: string
  summary_text: string
  key_points?: string[]
  tags?: string[]
  ai_model?: string
  ai_provider?: string
  tokens_used?: number
  url: string
  author?: string
  content?: string
  is_read: boolean
  read_progress: number
  is_favorited: boolean
  notes?: string
  highlight_sentence?: string
  created_at: string
  generated_at?: string
}

export interface Source {
  id: number
  platform: string
  name: string
  url_pattern?: string
  is_active: boolean
  config?: Record<string, unknown>
  created_at: string
}

export interface Stats {
  total_summaries: number
  total_sources: number
  active_sources: number
  total_raw_contents: number
  read_count: number
  favorite_count: number
  platforms: Array<{
    platform: string
    content_count: number
    summary_count: number
  }>
}

export interface ModelInfo {
  id: string
  name: string
  description: string
}

export interface ProviderInfo {
  id: string
  name: string
  models: ModelInfo[]
  default_model: string
}

export interface Config {
  default_ai_provider: string
  default_ai_model: string  // 格式: "provider:model"
  openai_api_key: string
  deepseek_api_key: string
  kimi_api_key: string
  kimi_coding_api_key: string
  glm_api_key: string
  minimax_api_key: string
  anthropic_api_key: string
  // 各供应商的模型选择
  openai_model: string
  claude_model: string
  deepseek_model: string
  glm_model: string
  kimi_model: string
  kimi_coding_model: string
  minimax_model: string
  database_url: string
  email_enabled: boolean
  smtp_host: string
  smtp_port: number
  smtp_user: string
  smtp_password: string
  email_to: string
  crawl_schedule: string
  summarize_schedule: string
  email_schedule: string
  timezone: string
  log_level: string
}
