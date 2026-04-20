import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Heart, Bookmark, ExternalLink, Share2, Clock, Sparkles, RefreshCw, AlertCircle, Tag, FileText, KeyRound, StickyNote, Lightbulb, Highlighter, BookOpen } from 'lucide-react'
import { motion } from 'framer-motion'
import { useEffect, useState, useCallback, useRef } from 'react'
import { summariesApi } from '../api/client'
import type { Summary } from '../types'

const PLATFORM_COLORS: Record<string, string> = {
  github: 'bg-[#24292e]/80 border-[#4a5568]',
  zhihu: 'bg-[#0084ff]/15 border-[#0084ff]/30',
  bilibili: 'bg-[#fb7299]/15 border-[#fb7299]/30',
  twitter: 'bg-[#1da1f2]/15 border-[#1da1f2]/30',
  anthropic: 'bg-[#d97757]/15 border-[#d97757]/30',
  builderio: 'bg-[#a855f7]/15 border-[#a855f7]/30',
  hackernews: 'bg-[#ff6600]/15 border-[#ff6600]/30',
}

function SummaryDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const summaryId = Number(id)

  const { data: summary, isLoading, error } = useQuery<Summary>({
    queryKey: ['summary', summaryId],
    queryFn: () => summariesApi.get(summaryId),
    enabled: !isNaN(summaryId),
  })

  const toggleFavoriteMutation = useMutation({
    mutationFn: () => summariesApi.toggleFavorite(summaryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['summary', summaryId] })
      queryClient.invalidateQueries({ queryKey: ['summaries'] })
    },
  })

  const markAsReadMutation = useMutation({
    mutationFn: (progress?: number) => summariesApi.markAsRead(summaryId, progress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['summary', summaryId] })
    },
  })

  // Read progress
  const [readProgress, setReadProgress] = useState(0)

  // Sync read progress from API
  useEffect(() => {
    if (summary?.read_progress !== undefined) {
      setReadProgress(summary.read_progress)
    }
  }, [summary?.read_progress])

  // Similar content
  const { data: similarData } = useQuery({
    queryKey: ['similar', summaryId],
    queryFn: () => summariesApi.getSimilar(summaryId),
    enabled: !isNaN(summaryId),
  })

  // Notes state
  const [notes, setNotes] = useState('')
  const [notesSaved, setNotesSaved] = useState(true)
  const notesTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const updateNotesMutation = useMutation({
    mutationFn: (newNotes: string) => summariesApi.updateNotes(summaryId, newNotes),
    onSuccess: () => {
      setNotesSaved(true)
      queryClient.invalidateQueries({ queryKey: ['summary', summaryId] })
    },
  })

  const handleNotesChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setNotes(value)
    setNotesSaved(false)
    if (notesTimerRef.current) clearTimeout(notesTimerRef.current)
    notesTimerRef.current = setTimeout(() => {
      updateNotesMutation.mutate(value)
    }, 800)
  }, [updateNotesMutation])

  // Sync notes from API when summary loads
  useEffect(() => {
    if (summary?.notes !== undefined) {
      setNotes(summary.notes || '')
    }
  }, [summary?.notes])

  // Cleanup timer
  useEffect(() => {
    return () => {
      if (notesTimerRef.current) clearTimeout(notesTimerRef.current)
    }
  }, [])

  // Mark as read when viewing — 用 ref 防止 StrictMode 双重执行和重复调用
  const hasMarkedRead = useRef(false)
  useEffect(() => {
    if (summary && !summary.is_read && !hasMarkedRead.current) {
      hasMarkedRead.current = true
      markAsReadMutation.mutate(undefined)
    }
  }, [summary, markAsReadMutation])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="relative">
          <RefreshCw className="w-8 h-8 animate-spin text-x-cyan" />
          <div className="absolute inset-0 animate-glow-pulse rounded-full" />
        </div>
      </div>
    )
  }

  if (error || !summary) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4">
        <div className="w-16 h-16 rounded-lg bg-x-red/10 border border-x-red/20 flex items-center justify-center mb-4">
          <AlertCircle className="w-8 h-8 text-x-red" />
        </div>
        <p className="font-mono text-x-red mb-2">加载失败</p>
        <p className="font-mono text-sm text-x-gray mb-4 text-center">
          {error instanceof Error ? error.message : '内容不存在或已被删除'}
        </p>
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-x-dark/80 border border-x-border/60 text-x-light-gray hover:border-x-cyan/40 hover:text-x-cyan transition-all font-mono"
        >
          <ArrowLeft className="w-4 h-4" />
          返回
        </button>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-screen"
    >
      {/* Header */}
      <div className="sticky top-[57px] md:top-0 z-20 bg-x-black/90 backdrop-blur-xl border-b border-x-border/40">
        <div className="flex items-center gap-4 px-4 py-3">
          <button
            onClick={() => navigate(-1)}
            className="p-2 rounded-lg hover:bg-x-dark/80 transition-colors border border-transparent hover:border-x-border/60"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <span className="text-x-cyan font-mono text-xs animate-flicker">⬤</span>
            <h1 className="font-bold text-lg font-mono tracking-wide">内容详情</h1>
          </div>
        </div>
      </div>

      {/* Content */}
      <article className="p-4 space-y-4">
        {/* Platform & Meta */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className={`platform-badge ${PLATFORM_COLORS[summary.platform] || 'bg-x-gray border-x-gray'}`}>
              {summary.platform.toUpperCase()}
            </span>
            <span className="text-x-gray text-sm font-mono">{summary.author}</span>
          </div>
          <span className="text-xs font-mono text-x-gray flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {new Date(summary.created_at).toLocaleString('zh-CN')}
          </span>
        </div>

        {/* Title */}
        <h2 className="text-2xl font-bold leading-tight glow-cyan">
          {summary.title}
        </h2>

        {/* AI Summary Section */}
        <div className="cyber-border p-6 relative overflow-hidden">
          {/* Subtle glow behind */}
          <div className="absolute -top-20 -right-20 w-40 h-40 bg-x-cyan/5 rounded-full blur-3xl pointer-events-none" />
          <div className="relative">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-x-cyan" />
              <span className="font-bold text-x-cyan font-mono">AI 总结</span>
              <span className="text-xs text-x-gray font-mono">
                {summary.ai_provider} · {summary.ai_model}
              </span>
            </div>
            <p className="text-lg leading-relaxed mb-4 whitespace-pre-line text-x-light-gray/90">
              {summary.summary_text}
            </p>
            {summary.highlight_sentence && (
              <div className="p-3 rounded-lg bg-x-yellow/5 border border-x-yellow/20 mb-4">
                <div className="flex items-start gap-2">
                  <Highlighter className="w-4 h-4 text-x-yellow mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-x-light-gray/90 italic leading-relaxed">
                    "{summary.highlight_sentence}"
                  </p>
                </div>
              </div>
            )}
            {summary.tokens_used && (
              <div className="font-mono text-xs text-x-gray">
                TOKENS_USED: {summary.tokens_used}
              </div>
            )}
          </div>
        </div>

        {/* Key Points */}
        {summary.key_points && summary.key_points.length > 0 && (
          <div className="cyber-border p-6">
            <div className="flex items-center gap-2 mb-4">
              <KeyRound className="w-4 h-4 text-x-magenta" />
              <h3 className="font-bold font-mono tracking-wide">关键要点</h3>
            </div>
            <div className="space-y-3">
              {summary.key_points.map((point, i) => (
                <div key={i} className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-lg bg-x-cyan/10 border border-x-cyan/30 text-x-cyan flex items-center justify-center text-sm font-mono">
                    {i + 1}
                  </span>
                  <p className="text-x-light-gray/90 leading-relaxed pt-0.5">{point}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tags */}
        {summary.tags && summary.tags.length > 0 && (
          <div className="cyber-border p-6">
            <div className="flex items-center gap-2 mb-4">
              <Tag className="w-4 h-4 text-x-violet" />
              <h3 className="font-bold font-mono tracking-wide">标签</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {summary.tags.map((tag) => (
                <span
                  key={tag}
                  className="cyber-tag cursor-pointer"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Original Content */}
        {summary.content && (
          <div className="cyber-border p-6">
            <div className="flex items-center gap-2 mb-4">
              <FileText className="w-4 h-4 text-x-gray" />
              <h3 className="font-bold font-mono tracking-wide text-x-gray">原文</h3>
            </div>
            <div className="text-x-gray leading-relaxed font-mono text-sm whitespace-pre-line">
              {summary.content}
            </div>
          </div>
        )}

        {/* Read Progress */}
        <div className="cyber-border p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-x-cyan" />
              <h3 className="font-bold font-mono tracking-wide">阅读进度</h3>
            </div>
            <span className="text-xs font-mono text-x-cyan">{readProgress}%</span>
          </div>
          <input
            type="range"
            min={0}
            max={100}
            value={readProgress}
            onChange={(e) => {
              const val = parseInt(e.target.value)
              setReadProgress(val)
              markAsReadMutation.mutate(val)
            }}
            className="w-full accent-x-cyan"
          />
          <div className="flex justify-between mt-1">
            <span className="text-[10px] font-mono text-x-gray">0%</span>
            <span className="text-[10px] font-mono text-x-gray">50%</span>
            <span className="text-[10px] font-mono text-x-gray">100%</span>
          </div>
        </div>

        {/* Personal Notes */}
        <div className="cyber-border p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <StickyNote className="w-4 h-4 text-x-cyan" />
              <h3 className="font-bold font-mono tracking-wide">我的笔记</h3>
            </div>
            <span className={`text-xs font-mono transition-opacity ${notesSaved ? 'opacity-100 text-x-gray' : 'opacity-0'}`}>
              已保存
            </span>
          </div>
          <textarea
            value={notes}
            onChange={handleNotesChange}
            placeholder="记录你的想法、灵感或行动计划..."
            className="w-full min-h-[120px] x-input font-mono text-sm resize-y leading-relaxed"
            spellCheck={false}
          />
        </div>

        {/* Similar Content */}
        {similarData && similarData.items.length > 0 && (
          <div className="cyber-border p-6">
            <div className="flex items-center gap-2 mb-4">
              <Lightbulb className="w-4 h-4 text-x-yellow" />
              <h3 className="font-bold font-mono tracking-wide">相关内容</h3>
              <span className="text-xs text-x-gray font-mono">({similarData.total})</span>
            </div>
            <div className="space-y-2">
              {similarData.items.map((item) => (
                <button
                  key={item.id}
                  onClick={() => navigate(`/summary/${item.id}`)}
                  className="w-full text-left px-3 py-3 rounded-lg bg-x-dark/40 hover:bg-x-dark border border-x-border/30 hover:border-x-cyan/20 transition-all group"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-x-border/40 text-x-gray font-mono uppercase">
                      {item.platform}
                    </span>
                    {item.is_read && (
                      <span className="text-[10px] text-x-lime font-mono">已读</span>
                    )}
                    {item.is_favorited && (
                      <span className="text-[10px] text-x-blue font-mono">已收藏</span>
                    )}
                    {item.overlap_tags.length > 0 && (
                      <span className="text-[10px] text-x-yellow font-mono">
                        {item.overlap_tags.join(', ')}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-x-light-gray group-hover:text-x-cyan transition-colors truncate">
                    {item.title}
                  </p>
                  <p className="text-xs text-x-gray mt-0.5 truncate">
                    {item.summary_text}
                  </p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-6 border-t border-x-border/40 sticky bottom-0 bg-x-black/95 backdrop-blur-xl py-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => toggleFavoriteMutation.mutate()}
              disabled={toggleFavoriteMutation.isPending}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all font-mono text-sm border ${
                summary.is_favorited
                  ? 'bg-x-blue/15 text-x-blue border-x-blue/40 shadow-[0_0_15px_hsl(var(--x-blue)/0.15)] dark:shadow-none'
                  : 'bg-x-dark/60 text-x-gray border-x-border/60 hover:border-x-blue/30 hover:text-x-blue'
              }`}
            >
              <Bookmark className={`w-5 h-5 ${summary.is_favorited ? 'fill-current' : ''}`} />
              <span>{summary.is_favorited ? '已收藏' : '收藏'}</span>
            </button>

            <button
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all font-mono text-sm border ${
                summary.is_read
                  ? 'bg-x-blue/15 text-x-blue border-x-blue/40 shadow-[0_0_15px_hsl(var(--x-blue)/0.15)] dark:shadow-none'
                  : 'bg-x-dark/60 text-x-gray border-x-border/60'
              }`}
            >
              <Heart className={`w-5 h-5 ${summary.is_read ? 'fill-current' : ''}`} />
              <span>{summary.is_read ? '已读' : '未读'}</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button className="p-2 rounded-lg bg-x-dark/60 text-x-gray hover:text-x-light-gray transition-all border border-x-border/60 hover:border-x-border">
              <Share2 className="w-5 h-5" />
            </button>
            <button
              onClick={() => window.open(summary.url, '_blank', 'noopener,noreferrer')}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-x-dark/60 text-x-gray hover:text-x-cyan transition-all border border-x-border/60 hover:border-x-cyan/30 font-mono text-sm"
            >
              <ExternalLink className="w-5 h-5" />
              <span>查看原文</span>
            </button>
          </div>
        </div>
      </article>
    </motion.div>
  )
}

export default SummaryDetail
