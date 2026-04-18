import { useState, useCallback, useMemo, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Database, Key, Mail, RefreshCw, Shield, ChevronRight, AlertCircle, Check, Loader2, Terminal, HardDrive, Trash2 } from 'lucide-react'
import { configApi, sourcesApi, summariesApi } from '../api/client'
import type { Config, Source, ProviderInfo } from '../types'

// 提供商显示名称映射
const PROVIDER_LABELS: Record<string, string> = {
  openai: 'OpenAI',
  claude: 'Claude',
  deepseek: 'DeepSeek',
  kimi: 'Kimi',
  'kimi-coding': 'Kimi Coding',
  glm: 'GLM',
  minimax: 'MiniMax',
}

function Settings() {
  const queryClient = useQueryClient()
  const [expandedSection, setExpandedSection] = useState<string | null>('ai')
  const [editValues, setEditValues] = useState<Partial<Config>>({})
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  // 级联选择状态
  const [selectedProvider, setSelectedProvider] = useState<string>('')
  const [selectedModel, setSelectedModel] = useState<string>('')

  const { data: config, isLoading: configLoading } = useQuery<Config>({
    queryKey: ['config'],
    queryFn: configApi.get,
  })

  const { data: providers, isLoading: providersLoading } = useQuery<ProviderInfo[]>({
    queryKey: ['providers'],
    queryFn: configApi.getProviders,
  })

  const { data: sources, isLoading: sourcesLoading } = useQuery<Source[]>({
    queryKey: ['sources'],
    queryFn: sourcesApi.list,
  })

  // 从 config 初始化级联选择状态
  useEffect(() => {
    if (config?.default_ai_model && !selectedProvider) {
      const [provider, model] = config.default_ai_model.split(':')
      if (provider && model) {
        setSelectedProvider(provider)
        setSelectedModel(model)
      }
    }
  }, [config, selectedProvider])

  const updateMutation = useMutation({
    mutationFn: (data: Partial<Config>) => configApi.update(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] })
      setMessage({ type: 'success', text: '配置已保存' })
      setEditValues({})
      setTimeout(() => setMessage(null), 3000)
    },
    onError: (error) => {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : '保存失败' })
    },
  })

  const testEmailMutation = useMutation({
    mutationFn: () => configApi.testEmail(),
    onSuccess: () => {
      setMessage({ type: 'success', text: '今日摘要邮件已发送' })
      setTimeout(() => setMessage(null), 3000)
    },
    onError: (error) => {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : '发送失败' })
    },
  })

  const cleanupMutation = useMutation(useMemo(() => ({
    mutationFn: () => summariesApi.cleanup(5),
    onSuccess: (result: { deleted_summaries: number, deleted_raw_contents: number, remaining: number }) => {
      queryClient.invalidateQueries({ queryKey: ['summaries'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
      setMessage({
        type: 'success',
        text: `清理完成：删除了 ${result.deleted_summaries} 条摘要和 ${result.deleted_raw_contents} 条原始数据，剩余 ${result.remaining} 条`
      })
      setTimeout(() => setMessage(null), 5000)
    },
    onError: (error: Error) => {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : '清理失败' })
    },
  }), [queryClient]))

  // 获取当前选中提供商的模型列表
  const currentProviderModels = useMemo(() => {
    if (!selectedProvider || !providers) return []
    return providers.find(p => p.id === selectedProvider)?.models || []
  }, [selectedProvider, providers])

  // 获取当前提供商的默认模型
  const getCurrentProviderDefaultModel = useCallback(() => {
    if (!selectedProvider || !providers) return ''
    return providers.find(p => p.id === selectedProvider)?.default_model || ''
  }, [selectedProvider, providers])

  const handleSave = () => {
    const dataToSave: Partial<Config> = { ...editValues }

    // 如果有级联选择的更改，添加 default_ai_model
    if (selectedProvider && selectedModel) {
      dataToSave.default_ai_model = `${selectedProvider}:${selectedModel}`
      dataToSave.default_ai_provider = selectedProvider
    }

    if (Object.keys(dataToSave).length > 0) {
      updateMutation.mutate(dataToSave)
    }
  }

  const handleChange = (key: keyof Config, value: string | boolean | number) => {
    setEditValues((prev) => ({ ...prev, [key]: value }))
  }

  const handleProviderChange = (providerId: string) => {
    setSelectedProvider(providerId)
    // 自动选择该提供商的默认模型
    const defaultModel = providers?.find(p => p.id === providerId)?.default_model || ''
    setSelectedModel(defaultModel)
  }

  const hasChanges = Object.keys(editValues).length > 0 || (
    config && selectedProvider && selectedModel &&
    `${selectedProvider}:${selectedModel}` !== config.default_ai_model
  )

  // 获取当前提供商的所有模型（用于显示 API Key 输入框）
  const getProviderModelsForKeys = useCallback(() => {
    if (!providers) return []
    return providers.map(p => ({
      value: p.id,
      label: p.name,
    }))
  }, [providers])

  if (configLoading || providersLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-x-cyan" />
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="sticky top-[57px] md:top-0 z-20 bg-x-black/90 backdrop-blur-xl border-b border-x-border/40">
        <div className="px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-5 h-5 text-x-cyan" />
            <h1 className="font-bold text-xl font-mono tracking-wide">系统设置</h1>
          </div>
          {hasChanges && (
            <button
              onClick={handleSave}
              disabled={updateMutation.isPending}
              className="x-button-primary font-mono text-sm py-2 px-4"
            >
              {updateMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                '保存'
              )}
            </button>
          )}
        </div>
      </div>

      {/* Message */}
      {message && (
        <div className={`px-4 py-3 border-b border-x-border/40 font-mono text-sm ${
          message.type === 'success'
            ? 'bg-x-lime/10 text-x-lime border-x-lime/20'
            : 'bg-x-red/10 text-x-red border-x-red/20'
        }`}>
          <div className="flex items-center gap-2">
            {message.type === 'success' ? <Check className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
            {message.text}
          </div>
        </div>
      )}

      {/* Settings Sections */}
      <div className="px-4 py-4 space-y-4">
        {/* AI Config */}
        <div className="cyber-border p-4">
          <button
            onClick={() => setExpandedSection(expandedSection === 'ai' ? null : 'ai')}
            className="w-full flex items-center justify-between mb-4 group"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-x-cyan/10 border border-x-cyan/30 flex items-center justify-center">
                <Key className="w-5 h-5 text-x-cyan" />
              </div>
              <div className="text-left">
                <h3 className="font-bold font-mono">AI 配置</h3>
                <p className="text-sm text-x-gray font-mono">选择 AI 服务商和模型</p>
              </div>
            </div>
            <ChevronRight className={`w-5 h-5 text-x-gray transition-transform group-hover:text-x-cyan ${expandedSection === 'ai' ? 'rotate-90' : ''}`} />
          </button>

          {expandedSection === 'ai' && config && providers && (
            <div className="space-y-4 pl-[52px]">
              {/* 供应商选择 */}
              <div className="space-y-2">
                <label className="font-mono text-sm text-x-gray">AI 服务商</label>
                <select
                  value={selectedProvider || config.default_ai_provider}
                  onChange={(e) => handleProviderChange(e.target.value)}
                  className="w-full x-input"
                >
                  {providers.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>

              {/* 模型选择 */}
              <div className="space-y-2">
                <label className="font-mono text-sm text-x-gray">模型</label>
                <select
                  value={selectedModel || getCurrentProviderDefaultModel()}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full x-input"
                >
                  {currentProviderModels.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} - {m.description}
                    </option>
                  ))}
                </select>
              </div>

              {/* 当前选中模型显示 */}
              {selectedProvider && selectedModel && (
                <div className="p-3 bg-x-dark/60 rounded-lg text-sm border border-x-border/40 font-mono">
                  <span className="text-x-gray"


                  >当前配置: </span>
                  <span className="text-x-cyan font-medium">
                    {PROVIDER_LABELS[selectedProvider] || selectedProvider} / {currentProviderModels.find(m => m.id === selectedModel)?.name || selectedModel}
                  </span>
                </div>
              )}

              <div className="border-t border-x-border/40 pt-4 mt-4">
                <h4 className="font-mono text-sm font-medium text-x-gray mb-3"

                >API Key 配置</h4>
                {getProviderModelsForKeys().map((provider) => {
                  const keyName = `${provider.value.replace('-', '_')}_api_key` as keyof Config
                  const value = (config[keyName] as string) || ''
                  const editValue = (editValues[keyName] as string) || value
                  return (
                    <div key={provider.value} className="space-y-2 mb-3"

                    >
                      <label className="font-mono text-sm text-x-gray"

                      >{provider.label} API Key</label>
                      <input
                        type="password"
                        value={editValue}
                        onChange={(e) => handleChange(keyName, e.target.value)}
                        placeholder={`输入 ${provider.label} API Key`}
                        className="w-full x-input font-mono"
                      />
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>

        {/* Data Sources */}
        <div className="cyber-border p-4"

        >
          <button
            onClick={() => setExpandedSection(expandedSection === 'sources' ? null : 'sources')}
            className="w-full flex items-center justify-between mb-4 group"
          >
            <div className="flex items-center gap-3"

            >
              <div className="w-10 h-10 rounded-lg bg-x-magenta/10 border border-x-magenta/30 flex items-center justify-center"

              >
                <Database className="w-5 h-5 text-x-magenta" />
              </div>
              <div className="text-left"

              >
                <h3 className="font-bold font-mono"

                >数据源</h3>
                <p className="text-sm text-x-gray font-mono"

                >
                  {sourcesLoading ? '加载中...' : `${sources?.filter((s) => s.is_active).length || 0} 个已启用`}
                </p>
              </div>
            </div>
            <ChevronRight className={`w-5 h-5 text-x-gray transition-transform group-hover:text-x-magenta ${expandedSection === 'sources' ? 'rotate-90' : ''}`} />
          </button>

          {expandedSection === 'sources' && sources && (
            <div className="space-y-2 pl-[52px]"

            >
              {sources.map((source) => (
                <div key={source.id} className="flex items-center justify-between py-2 border-b border-x-border/20 last:border-0"

                >
                  <div

                  >
                    <p className="font-medium font-mono"

                    >{source.name}</p>
                    <p className="text-sm text-x-gray font-mono"

                    >{source.url_pattern}</p>
                  </div>
                  <div className="flex items-center gap-2"

                  >
                    <span className={`status-dot ${source.is_active ? 'status-active' : 'status-inactive'}`} />
                    <span className={`font-mono text-xs ${source.is_active ? 'text-x-lime' : 'text-x-gray'}`}

                    >
                      {source.is_active ? 'ONLINE' : 'OFFLINE'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Email Config */}
        <div className="cyber-border p-4"

        >
          <button
            onClick={() => setExpandedSection(expandedSection === 'email' ? null : 'email')}
            className="w-full flex items-center justify-between mb-4 group"
          >
            <div className="flex items-center gap-3"

            >
              <div className="w-10 h-10 rounded-lg bg-x-yellow/10 border border-x-yellow/30 flex items-center justify-center"

              >
                <Mail className="w-5 h-5 text-x-yellow" />
              </div>
              <div className="text-left"

              >
                <h3 className="font-bold font-mono"

                >邮件配置</h3>
                <p className="text-sm text-x-gray font-mono"

                >{config?.email_enabled ? '已启用' : '未启用'}</p>
              </div>
            </div>
            <ChevronRight className={`w-5 h-5 text-x-gray transition-transform group-hover:text-x-yellow ${expandedSection === 'email' ? 'rotate-90' : ''}`} />
          </button>

          {expandedSection === 'email' && config && (
            <div className="space-y-4 pl-[52px]"

            >
              <div className="flex items-center justify-between"

              >
                <span className="font-mono text-sm text-x-gray"

                >启用邮件推送</span>
                <button
                  onClick={() => handleChange('email_enabled', !config.email_enabled)}
                  className={`w-12 h-6 rounded-lg transition-colors relative ${editValues.email_enabled ?? config.email_enabled ? 'bg-x-cyan' : 'bg-x-gray/30'}`}
                >
                  <span className={`absolute top-1 w-4 h-4 rounded bg-x-light-gray transition-transform ${(editValues.email_enabled ?? config.email_enabled) ? 'left-7' : 'left-1'}`} />
                </button>
              </div>

              <div className="space-y-2"

              >
                <label className="font-mono text-sm text-x-gray"

                >SMTP 服务器</label>
                <input
                  type="text"
                  value={editValues.smtp_host ?? config.smtp_host}
                  onChange={(e) => handleChange('smtp_host', e.target.value)}
                  className="w-full x-input font-mono"
                />
              </div>

              <div className="space-y-2"

              >
                <label className="font-mono text-sm text-x-gray"

                >SMTP 端口</label>
                <input
                  type="number"
                  value={editValues.smtp_port ?? config.smtp_port}
                  onChange={(e) => handleChange('smtp_port', parseInt(e.target.value))}
                  className="w-full x-input font-mono"
                />
              </div>

              <div className="space-y-2"

              >
                <label className="font-mono text-sm text-x-gray"

                >发件邮箱</label>
                <input
                  type="email"
                  value={editValues.smtp_user ?? config.smtp_user}
                  onChange={(e) => handleChange('smtp_user', e.target.value)}
                  className="w-full x-input font-mono"
                />
              </div>

              <div className="space-y-2"

              >
                <label className="font-mono text-sm text-x-gray"

                >SMTP 密码 / 授权码</label>
                <input
                  type="password"
                  value={editValues.smtp_password ?? config.smtp_password}
                  onChange={(e) => handleChange('smtp_password', e.target.value)}
                  placeholder="输入 SMTP 密码或授权码"
                  className="w-full x-input font-mono"
                />
              </div>

              <div className="space-y-2"

              >
                <label className="font-mono text-sm text-x-gray"

                >收件邮箱</label>
                <input
                  type="email"
                  value={editValues.email_to ?? config.email_to}
                  onChange={(e) => handleChange('email_to', e.target.value)}
                  className="w-full x-input font-mono"
                />
              </div>

              <button
                onClick={() => testEmailMutation.mutate()}
                disabled={testEmailMutation.isPending}
                className="x-button-secondary font-mono text-sm py-2 px-4"
              >
                {testEmailMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
                发送今日摘要
              </button>
            </div>
          )}
        </div>

        {/* System */}
        <div className="cyber-border p-4"

        >
          <button
            onClick={() => setExpandedSection(expandedSection === 'system' ? null : 'system')}
            className="w-full flex items-center justify-between mb-4 group"
          >
            <div className="flex items-center gap-3"

            >
              <div className="w-10 h-10 rounded-lg bg-x-violet/10 border border-x-violet/30 flex items-center justify-center"

              >
                <Shield className="w-5 h-5 text-x-violet" />
              </div>
              <div className="text-left"

              >
                <h3 className="font-bold font-mono"

                >系统</h3>
                <p className="text-sm text-x-gray font-mono"

                >定时任务和日志配置</p>
              </div>
            </div>
            <ChevronRight className={`w-5 h-5 text-x-gray transition-transform group-hover:text-x-violet ${expandedSection === 'system' ? 'rotate-90' : ''}`} />
          </button>

          {expandedSection === 'system' && config && (
            <div className="space-y-4 pl-[52px]"

            >
              <div className="space-y-2"

              >
                <label className="font-mono text-sm text-x-gray"

                >抓取调度 (Cron)</label>
                <input
                  type="text"
                  value={editValues.crawl_schedule ?? config.crawl_schedule}
                  onChange={(e) => handleChange('crawl_schedule', e.target.value)}
                  placeholder="0 */2 * * *"
                  className="w-full x-input font-mono"
                />
                <p className="font-mono text-xs text-x-gray"

                >默认每 2 小时执行一次</p>
              </div>

              <div className="space-y-2"

              >
                <label className="font-mono text-sm text-x-gray"

                >摘要调度 (Cron)</label>
                <input
                  type="text"
                  value={editValues.summarize_schedule ?? config.summarize_schedule}
                  onChange={(e) => handleChange('summarize_schedule', e.target.value)}
                  placeholder="0 */3 * * *"
                  className="w-full x-input font-mono"
                />
                <p className="font-mono text-xs text-x-gray"

                >默认每 3 小时执行一次</p>
              </div>

              <div className="space-y-2"

              >
                <label className="font-mono text-sm text-x-gray"

                >邮件调度 (Cron)</label>
                <input
                  type="text"
                  value={editValues.email_schedule ?? config.email_schedule}
                  onChange={(e) => handleChange('email_schedule', e.target.value)}
                  placeholder="0 22 * * *"
                  className="w-full x-input font-mono"
                />
                <p className="font-mono text-xs text-x-gray"

                >默认每晚 22:00 发送</p>
              </div>

              <div className="space-y-2"

              >
                <label className="font-mono text-sm text-x-gray"

                >时区</label>
                <input
                  type="text"
                  value={editValues.timezone ?? config.timezone}
                  onChange={(e) => handleChange('timezone', e.target.value)}
                  className="w-full x-input font-mono"
                />
              </div>

              <div className="space-y-2"

              >
                <label className="font-mono text-sm text-x-gray"

                >日志级别</label>
                <select
                  value={editValues.log_level ?? config.log_level}
                  onChange={(e) => handleChange('log_level', e.target.value)}
                  className="w-full x-input font-mono"
                >
                  <option value="DEBUG"

                  >DEBUG</option>
                  <option value="INFO"

                  >INFO</option>
                  <option value="WARNING"

                  >WARNING</option>
                  <option value="ERROR"

                  >ERROR</option>
                </select>
              </div>
            </div>
          )}
        </div>

        {/* Data Management */}
        <div className="cyber-border p-4 border-x-red/20"

        >
          <button
            onClick={() => setExpandedSection(expandedSection === 'data' ? null : 'data')}
            className="w-full flex items-center justify-between mb-4 group"
          >
            <div className="flex items-center gap-3"

            >
              <div className="w-10 h-10 rounded-lg bg-x-red/10 border border-x-red/30 flex items-center justify-center"

              >
                <HardDrive className="w-5 h-5 text-x-red" />
              </div>
              <div className="text-left"

              >
                <h3 className="font-bold font-mono"

                >数据管理</h3>
                <p className="text-sm text-x-gray font-mono"

                >清理历史数据</p>
              </div>
            </div>
            <ChevronRight className={`w-5 h-5 text-x-gray transition-transform group-hover:text-x-red ${expandedSection === 'data' ? 'rotate-90' : ''}`} />
          </button>

          {expandedSection === 'data' && (
            <div className="space-y-4 pl-[52px]"

            >
              <div className="p-4 bg-x-red/5 border border-x-red/20 rounded-lg"

              >
                <div className="flex items-center gap-2 mb-2"

                >
                  <AlertCircle className="w-4 h-4 text-x-red" />
                  <h4 className="font-medium text-x-red font-mono"

                  >⚠️ 危险操作</h4>
                </div>
                <p className="font-mono text-sm text-x-gray mb-4"

                >
                  清理数据将删除所有摘要和原始数据，只保留最新的 5 条。此操作不可恢复。
                </p>
                <button
                  onClick={() => {
                    if (confirm('确定要清理数据吗？将只保留最近 5 条摘要，其余数据将被永久删除。')) {
                      cleanupMutation.mutate()
                    }
                  }}
                  disabled={cleanupMutation.isPending}
                  className="x-button font-mono text-sm py-2 px-4 bg-x-red/15 text-x-red border border-x-red/40 hover:bg-x-red/25 hover:shadow-[0_0_15px_hsl(var(--x-red)/0.2)] dark:hover:shadow-none"
                >
                  {cleanupMutation.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                  清理数据（保留最近 5 条）
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="p-8 text-center border-t border-x-border/40"

      >
        <p className="font-mono text-sm text-x-gray"

        >AI_KNOWLEDGE_HUB v2.0.0</p>
        <p className="font-mono text-xs text-x-gray/60 mt-1 tracking-wider"

        >SYSTEM OPERATIONAL // ALL MODULES NOMINAL</p>
      </div>
    </div>
  )
}

export default Settings
