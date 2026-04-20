import { useRef, useEffect, useCallback, useState } from 'react'
import { Search, Command, Loader2, X, CheckCircle2, AlertCircle, Zap, Database, BarChart3, Flame, Settings, Mail, Sparkles } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { useCommandPalette } from './CommandPaletteProvider'
import { useAgentExecutor } from '../hooks/useAgentExecutor'
import { agentApi } from '../api/agent'
import { summariesApi } from '../api/client'
import type { QuickAction, AgentAction } from '../types/agent'
import type { Summary } from '../types'

/**
 * CommandPalette - Cyber Terminal style
 */

/** 高亮匹配文本 */
function HighlightText({ text, query, className }: { text: string; query: string; className?: string }) {
  if (!query || !text) return <span className={className}>{text}</span>
  const lowerText = text.toLowerCase()
  const lowerQuery = query.toLowerCase()
  const parts: { text: string; match: boolean }[] = []
  let lastIndex = 0
  let idx = lowerText.indexOf(lowerQuery)
  while (idx !== -1) {
    if (idx > lastIndex) {
      parts.push({ text: text.slice(lastIndex, idx), match: false })
    }
    parts.push({ text: text.slice(idx, idx + query.length), match: true })
    lastIndex = idx + query.length
    idx = lowerText.indexOf(lowerQuery, lastIndex)
  }
  if (lastIndex < text.length) {
    parts.push({ text: text.slice(lastIndex), match: false })
  }
  if (parts.length === 0) parts.push({ text, match: false })
  return (
    <span className={className}>
      {parts.map((part, i) =>
        part.match ? (
          <mark key={i} className="bg-x-blue/20 text-x-light-gray rounded px-0.5">
            {part.text}
          </mark>
        ) : (
          <span key={i}>{part.text}</span>
        )
      )}
    </span>
  )
}

const QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'ask-ai',
    label: 'Ask AI',
    description: '向 AI 知识库提问，基于已有摘要内容作答',
    icon: 'Sparkles',
    action: { type: 'ask_ai', params: { question: '最近有什么有趣的 AI 动态？' } },
  },
  {
    id: 'view-all',
    label: '查看全部摘要',
    description: '跳转到首页查看所有摘要',
    icon: 'Search',
    action: { type: 'list_summaries' },
  },
  {
    id: 'mark-first-read',
    label: '标记第一条为已读',
    description: '将最新摘要标记为已读',
    icon: 'CheckCircle2',
    action: { type: 'mark_read', params: { summary_id: 'latest' } },
  },
  {
    id: 'cleanup',
    label: '清理旧摘要',
    description: '保留最近 5 条，删除其余摘要',
    icon: 'X',
    action: { type: 'cleanup', params: { keep_count: 5 } },
  },
  {
    id: 'trigger-crawl',
    label: '立即抓取',
    description: '手动触发后台爬虫任务',
    icon: 'Zap',
    action: { type: 'trigger_crawl' },
  },
  {
    id: 'list-sources',
    label: '列出所有数据源',
    description: '查看所有数据源的平台和状态',
    icon: 'Database',
    action: { type: 'list_sources' },
  },
  {
    id: 'view-stats',
    label: '查看统计',
    description: '查看总摘要数、已读数、收藏数、平台分布',
    icon: 'BarChart3',
    action: { type: 'get_stats' },
  },
  {
    id: 'trending-tags',
    label: '热门标签',
    description: '查看前 10 个热门标签',
    icon: 'Flame',
    action: { type: 'get_trending_tags' },
  },
  {
    id: 'view-config',
    label: '查看配置',
    description: '查看当前默认模型、邮件开关等设置',
    icon: 'Settings',
    action: { type: 'get_config' },
  },
  {
    id: 'test-email',
    label: '发送今日摘要',
    description: '立即发送今日 AI 知识摘要邮件',
    icon: 'Mail',
    action: { type: 'test_email' },
  },
]

export function CommandPalette() {
  const { isOpen, input, isLoading, error, result, setInput, setLoading, setError, setResult, close } =
    useCommandPalette()
  const { execute } = useAgentExecutor()
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const [pendingAction, setPendingAction] = useState<AgentAction | null>(null)

  // Search mode states
  const [searchResults, setSearchResults] = useState<Summary[]>([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // 打开时自动聚焦输入框并全选，重置搜索状态
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
      setSearchResults([])
      setSelectedIndex(-1)
    }
  }, [isOpen])

  // Debounced search: when input is non-empty, search summaries
  useEffect(() => {
    const query = input.trim()
    if (!query) {
      setSearchResults([])
      setSelectedIndex(-1)
      return
    }

    if (searchTimerRef.current) clearTimeout(searchTimerRef.current)
    searchTimerRef.current = setTimeout(async () => {
      setSearchLoading(true)
      try {
        const result = await summariesApi.list({ search: query, page_size: 10 })
        setSearchResults(result.items)
        setSelectedIndex(result.items.length > 0 ? 0 : -1)
      } catch {
        setSearchResults([])
        setSelectedIndex(-1)
      } finally {
        setSearchLoading(false)
      }
    }, 300)

    return () => {
      if (searchTimerRef.current) clearTimeout(searchTimerRef.current)
    }
  }, [input])

  // Keyboard navigation for search results
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (searchResults.length === 0) return
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex((prev) => (prev + 1) % searchResults.length)
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex((prev) => (prev - 1 + searchResults.length) % searchResults.length)
      } else if (e.key === 'Enter' && selectedIndex >= 0) {
        e.preventDefault()
        const item = searchResults[selectedIndex]
        if (item) {
          close()
          navigate(`/summary/${item.id}`)
        }
      }
    },
    [searchResults, selectedIndex, close, navigate]
  )

  const handleSubmit = useCallback(
    async (e?: React.FormEvent) => {
      e?.preventDefault()
      if (!input.trim() || isLoading) return

      setLoading(true)
      setError(null)
      setResult(null)

      try {
        const response = await agentApi.parse(input.trim())
        // 破坏性操作需要先确认，避免误删数据
        if (['delete_summary', 'cleanup'].includes(response.action.type)) {
          setPendingAction(response.action)
          setLoading(false)
          return
        }
        const executionResult = await execute(response.action)
        setResult(executionResult)
        if (!executionResult.success) {
          setError(executionResult.message)
        }
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : '解析失败，请稍后重试'
        setError(message)
        setResult({ success: false, message })
      } finally {
        setLoading(false)
      }
    },
    [input, isLoading, setLoading, setError, setResult, execute]
  )

  // 抽离公共执行逻辑，避免 confirm 与 quickAction 重复代码
  const runAction = useCallback(
    async (action: AgentAction) => {
      setLoading(true)
      setError(null)
      setResult(null)
      try {
        const executionResult = await execute(action)
        setResult(executionResult)
        if (!executionResult.success) {
          setError(executionResult.message)
        }
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : '执行失败'
        setError(message)
        setResult({ success: false, message })
      } finally {
        setLoading(false)
      }
    },
    [setLoading, setError, setResult, execute]
  )

  const handleQuickAction = useCallback(
    async (action: AgentAction) => {
      // 破坏性操作必须先弹层确认
      if (['delete_summary', 'cleanup'].includes(action.type)) {
        setPendingAction(action)
        return
      }
      await runAction(action)
    },
    [runAction]
  )

  const confirmAndExecute = useCallback(async () => {
    if (!pendingAction) return
    const action = pendingAction
    setPendingAction(null)
    await runAction(action)
  }, [pendingAction, runAction])

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] bg-black/70 backdrop-blur-sm"
          onClick={close}
        >
          <motion.div
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="w-full max-w-xl mx-4 bg-x-black border border-x-border/60 rounded-xl shadow-2xl shadow-x-cyan/5 overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 输入框头部 */}
            <div className="flex items-center gap-3 px-4 py-4 border-b border-x-border/40">
              {isLoading ? (
                <Loader2 className="w-5 h-5 text-x-cyan animate-spin" />
              ) : (
                <Search className="w-5 h-5 text-x-gray" />
              )}
              <form className="flex-1" onSubmit={handleSubmit}>
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="输入命令或搜索关键词..."
                  className="w-full bg-transparent text-x-light-gray placeholder:text-x-gray/50 outline-none text-base font-mono"
                />
              </form>
              <div className="flex items-center gap-2 text-xs text-x-gray font-mono">
                <kbd className="px-1.5 py-0.5 border border-x-border/60 rounded bg-x-dark">ESC</kbd>
                <span>关闭</span>
              </div>
            </div>

            {/* 快捷操作区 */}
            {!input.trim() && !result && !error && !pendingAction && (
              <div className="px-2 py-3">
                <p className="px-3 py-2 text-xs font-mono text-x-gray uppercase tracking-widest">
                  快捷操作
                </p>
                <div className="space-y-1">
                  {QUICK_ACTIONS.map((qa) => (
                    <button
                      key={qa.id}
                      onClick={() => handleQuickAction(qa.action)}
                      className="w-full flex items-center gap-3 px-3 py-3 rounded-lg hover:bg-x-dark/80 transition-colors text-left group border border-transparent hover:border-x-cyan/10"
                    >
                      <div className="w-8 h-8 rounded-lg bg-x-dark/80 border border-x-border/60 flex items-center justify-center text-x-gray group-hover:text-x-cyan group-hover:border-x-cyan/30 transition-all">
                        {qa.icon === 'CheckCircle2' ? (
                          <CheckCircle2 className="w-4 h-4" />
                        ) : qa.icon === 'X' ? (
                          <X className="w-4 h-4" />
                        ) : qa.icon === 'Zap' ? (
                          <Zap className="w-4 h-4" />
                        ) : qa.icon === 'Database' ? (
                          <Database className="w-4 h-4" />
                        ) : qa.icon === 'BarChart3' ? (
                          <BarChart3 className="w-4 h-4" />
                        ) : qa.icon === 'Flame' ? (
                          <Flame className="w-4 h-4" />
                        ) : qa.icon === 'Settings' ? (
                          <Settings className="w-4 h-4" />
                        ) : qa.icon === 'Mail' ? (
                          <Mail className="w-4 h-4" />
                        ) : qa.icon === 'Sparkles' ? (
                          <Sparkles className="w-4 h-4" />
                        ) : (
                          <Search className="w-4 h-4" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-x-light-gray font-mono">{qa.label}</p>
                        {qa.description && (
                          <p className="text-xs text-x-gray truncate font-mono">{qa.description}</p>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* 实时搜索结果 */}
            {input.trim() && !result && !error && !isLoading && !pendingAction && (
              <div className="border-t border-x-border/40">
                {searchLoading && (
                  <div className="px-4 py-6 text-center text-sm text-x-gray font-mono">
                    <Loader2 className="w-5 h-5 mx-auto mb-2 animate-spin text-x-cyan" />
                    <p>搜索中...</p>
                  </div>
                )}
                {!searchLoading && searchResults.length === 0 && (
                  <div className="px-4 py-6 text-center text-sm text-x-gray font-mono">
                    <p>未找到匹配内容</p>
                    <p className="text-xs mt-1 opacity-60">按 Enter 调用 AI 解析</p>
                  </div>
                )}
                {!searchLoading && searchResults.length > 0 && (
                  <div className="max-h-[300px] overflow-y-auto">
                    <p className="px-4 py-2 text-xs font-mono text-x-gray uppercase tracking-widest sticky top-0 bg-x-black z-10">
                      搜索结果 ({searchResults.length})
                    </p>
                    <div className="space-y-1 px-2 pb-2">
                      {searchResults.map((item, idx) => (
                        <button
                          key={item.id}
                          onClick={() => {
                            close()
                            navigate(`/summary/${item.id}`)
                          }}
                          className={`w-full text-left px-3 py-2.5 rounded-lg transition-colors border ${
                            idx === selectedIndex
                              ? 'bg-x-dark/80 border-x-cyan/30'
                              : 'bg-transparent border-transparent hover:bg-x-dark/50 hover:border-x-border/40'
                          }`}
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-x-border/40 text-x-gray font-mono uppercase">
                              {item.platform}
                            </span>
                            {item.is_favorited && (
                              <span className="text-[10px] text-x-blue font-mono">已收藏</span>
                            )}
                          </div>
                          <HighlightText
                            text={item.title}
                            query={input.trim()}
                            className="text-sm text-x-light-gray truncate"
                          />
                          <HighlightText
                            text={item.summary_text.slice(0, 80)}
                            query={input.trim()}
                            className="text-xs text-x-gray mt-0.5 truncate"
                          />
                        </button>
                      ))}
                    </div>
                    <div className="px-4 py-2 text-[10px] text-x-gray font-mono border-t border-x-border/40 flex items-center justify-between">
                      <span>↑↓ 选择 · Enter 打开</span>
                      <span>按 Enter 调用 AI 解析</span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* 加载中状态 */}
            {isLoading && !result && !error && (
              <div className="px-4 py-8 text-center text-sm text-x-gray font-mono">
                <Loader2 className="w-6 h-6 mx-auto mb-2 animate-spin text-x-cyan" />
                <p>正在解析命令...</p>
              </div>
            )}

            {/* 错误状态 */}
            {error && !isLoading && (
              <div className="px-4 py-4 border-t border-x-border/40 bg-x-red/5">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-x-red flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-x-red font-mono">执行失败</p>
                    <p className="text-sm text-x-light-gray mt-1 font-mono">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* 成功结果状态 */}
            {result?.success && !isLoading && (
              <div className="px-4 py-4 border-t border-x-border/40 bg-x-lime/5">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-x-lime flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-x-lime font-mono">执行成功</p>
                    <p className="text-sm text-x-light-gray mt-1 whitespace-pre-wrap font-mono">{result.message}</p>
                    {/* RAG 问答：展示引用来源 */}
                    {result.data != null && typeof result.data === 'object' && (result.data as { isRagAnswer?: boolean }).isRagAnswer === true && (
                      <div className="mt-3 space-y-1">
                        <p className="text-xs text-x-gray font-mono uppercase tracking-widest">引用来源</p>
                        {((result.data as { sources?: { summary_id: number; title: string; platform: string; url: string; relevance_score: number }[] }).sources || []).map((src) => (
                          <button
                            key={src.summary_id}
                            onClick={() => {
                              close()
                              navigate(`/summary/${src.summary_id}`)
                            }}
                            className="w-full text-left px-3 py-2 rounded-lg bg-x-dark/50 hover:bg-x-dark border border-x-border/40 hover:border-x-cyan/20 transition-colors flex items-center gap-2"
                          >
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-x-border/40 text-x-gray font-mono uppercase">
                              {src.platform}
                            </span>
                            <span className="text-xs text-x-light-gray truncate flex-1">{src.title}</span>
                            <span className="text-[10px] text-x-gray font-mono"> relevance: {src.relevance_score}</span>
                          </button>
                        ))}
                      </div>
                    )}
                    {/* 如果返回的是摘要列表，在面板内直接渲染 */}
                    {Array.isArray(result.data) && result.data.length > 0 && (
                      <div className="mt-3 max-h-[240px] overflow-y-auto space-y-1 pr-1">
                        {(result.data as Summary[]).map((item) => (
                          <button
                            key={item.id}
                            onClick={() => window.open(item.url, '_blank', 'noopener,noreferrer')}
                            className="w-full text-left px-3 py-2 rounded-lg bg-x-dark/50 hover:bg-x-dark border border-x-border/40 hover:border-x-cyan/20 transition-colors"
                          >
                            <div className="flex items-center gap-2">
                              <span className="text-xs px-1.5 py-0.5 rounded bg-x-border/40 text-x-gray font-mono">
                                {item.platform}
                              </span>
                              {item.is_read && (
                                <span className="text-[10px] text-x-lime font-mono">已读</span>
                              )}
                              {item.is_favorited && (
                                <span className="text-[10px] text-x-pink font-mono">已收藏</span>
                              )}
                            </div>
                            <p className="text-sm text-x-light-gray mt-1 truncate">{item.title}</p>
                            <p className="text-xs text-x-gray font-mono">
                              {new Date(item.created_at).toLocaleString('zh-CN')}
                            </p>
                          </button>
                        ))}
                      </div>
                    )}
                    {Array.isArray(result.data) && result.data.length === 0 && (
                      <p className="mt-3 text-sm text-x-gray font-mono">暂无摘要</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* 二次确认弹层（破坏性操作） */}
            {pendingAction && !isLoading && (
              <div className="px-4 py-4 border-t border-x-border/40 bg-x-yellow/5">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-x-yellow flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-x-yellow font-mono">确认执行</p>
                    <p className="text-sm text-x-light-gray mt-1 font-mono">
                      {pendingAction.type === 'cleanup'
                        ? `确定要清理旧摘要吗？将保留最近 ${pendingAction.params?.keep_count ?? 5} 条，其余将被删除。`
                        : `确定要删除摘要 #${pendingAction.params?.summary_id} 吗？此操作不可恢复。`}
                    </p>
                    <div className="flex items-center gap-3 mt-3">
                      <button
                        onClick={confirmAndExecute}
                        className="px-3 py-1.5 text-sm font-medium bg-x-cyan text-x-black rounded-lg hover:bg-x-cyan/90 transition-colors font-mono"
                      >
                        确认
                      </button>
                      <button
                        onClick={() => setPendingAction(null)}
                        className="px-3 py-1.5 text-sm font-medium text-x-light-gray hover:bg-x-dark rounded-lg transition-colors font-mono border border-x-border/60"
                      >
                        取消
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 底部提示 */}
            <div className="px-4 py-2 border-t border-x-border/40 bg-x-dark/40 flex items-center justify-between text-xs text-x-gray font-mono">
              <div className="flex items-center gap-2">
                <Command className="w-3 h-3 text-x-cyan" />
                <span>K</span>
                <span>打开 / 关闭</span>
              </div>
              <span>AI_AGENT // COMMAND_PALETTE</span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
