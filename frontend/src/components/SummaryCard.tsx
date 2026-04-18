import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Heart, Bookmark, ExternalLink, Sparkles, ChevronDown, ChevronUp, Trash2, Loader2 } from 'lucide-react'
import { motion } from 'framer-motion'
import type { Summary } from '../types'

interface SummaryCardProps {
  summary: Summary
  index?: number
  onDelete?: (id: number) => void
  onFavorite?: (id: number) => void
  isDeleting?: boolean
  isFavoriting?: boolean
}

function SummaryCard({
  summary,
  index = 0,
  onDelete,
  onFavorite,
  isDeleting = false,
  isFavoriting = false
}: SummaryCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const platformColors: Record<string, string> = {
    github: 'bg-[#24292e]/80 border-[#4a5568]',
    zhihu: 'bg-[#0084ff]/15 border-[#0084ff]/30',
    bilibili: 'bg-[#fb7299]/15 border-[#fb7299]/30',
    twitter: 'bg-[#1da1f2]/15 border-[#1da1f2]/30',
    anthropic: 'bg-[#d97757]/15 border-[#d97757]/30',
    builderio: 'bg-[#a855f7]/15 border-[#a855f7]/30',
    hackernews: 'bg-[#ff6600]/15 border-[#ff6600]/30',
  }

  const platformNames: Record<string, string> = {
    github: 'GitHub',
    zhihu: '知乎',
    bilibili: 'Bilibili',
    twitter: 'X',
    anthropic: 'Anthropic',
    builderio: 'Builder.io',
    hackernews: 'Hacker News',
  }

  const platformGlow: Record<string, string> = {
    github: 'hover:shadow-[0_0_20px_rgba(74,85,104,0.15)] dark:hover:shadow-none',
    zhihu: 'hover:shadow-[0_0_20px_rgba(0,132,255,0.15)] dark:hover:shadow-none',
    bilibili: 'hover:shadow-[0_0_20px_rgba(251,114,153,0.15)] dark:hover:shadow-none',
    twitter: 'hover:shadow-[0_0_20px_rgba(29,161,242,0.15)] dark:hover:shadow-none',
    anthropic: 'hover:shadow-[0_0_20px_rgba(217,119,87,0.15)] dark:hover:shadow-none',
    builderio: 'hover:shadow-[0_0_20px_rgba(168,85,247,0.15)] dark:hover:shadow-none',
    hackernews: 'hover:shadow-[0_0_20px_rgba(255,102,0,0.15)] dark:hover:shadow-none',
  }

  const handleDelete = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (onDelete && confirm('确定要删除这条摘要吗？此操作不可恢复。')) {
      onDelete(summary.id)
    }
  }

  const handleFavorite = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (onFavorite) {
      onFavorite(summary.id)
    }
  }

  return (
    <motion.article
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className={`cyber-border p-5 mb-3 cursor-pointer group ${platformGlow[summary.platform] || ''}`}
    >
      <Link to={`/summary/${summary.id}`} className="block">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`platform-badge ${platformColors[summary.platform] || 'bg-x-gray border-x-gray'}`}>
              {platformNames[summary.platform] || summary.platform}
            </span>
            {summary.ai_provider && (
              <span className="flex items-center gap-1.5 text-xs text-x-gray font-mono">
                <Sparkles className="w-3 h-3 text-x-cyan" />
                {summary.ai_provider}
              </span>
            )}
          </div>
          <span className="text-xs font-mono text-x-gray">
            {new Date(summary.created_at).toLocaleDateString('zh-CN')}
          </span>
        </div>

        {/* Title */}
        <h3 className="text-lg font-bold mb-3 group-hover:text-x-cyan transition-colors line-clamp-2">
          {summary.title || '无标题'}
        </h3>

        {/* Summary Text */}
        <p className={`text-x-gray text-sm leading-relaxed mb-3 ${isExpanded ? '' : 'line-clamp-3'}`}>
          {summary.summary_text}
        </p>

        {/* Key Points */}
        {summary.key_points && summary.key_points.length > 0 && (
          <div className="mb-3 space-y-2">
            {summary.key_points.slice(0, isExpanded ? undefined : 2).map((point, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <span className="text-x-cyan mt-1 font-mono text-xs shrink-0"
                  style={{ textShadow: '0 0 6px hsl(var(--x-cyan) / 0.5)' }}
                >
                  {'>'}
                </span>
                <span className="text-x-light-gray/80">{point}</span>
              </div>
            ))}
          </div>
        )}

        {/* Tags */}
        {summary.tags && summary.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {summary.tags.slice(0, 4).map((tag) => (
              <span
                key={tag}
                className="cyber-tag"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-x-border/40">
          <div className="flex items-center gap-5">
            <button
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
              }}
              className={`flex items-center gap-1.5 text-sm transition-colors font-mono ${
                summary.is_read ? 'text-x-lime' : 'text-x-gray'
              }`}
            >
              <Heart className={`w-4 h-4 ${summary.is_read ? 'fill-current' : ''}`} />
              <span>{summary.is_read ? '已读' : '未读'}</span>
            </button>

            <button
              onClick={handleFavorite}
              disabled={isFavoriting}
              className={`flex items-center gap-1.5 text-sm transition-colors font-mono disabled:opacity-50 ${
                summary.is_favorited ? 'text-x-blue' : 'text-x-gray hover:text-x-cyan'
              }`}
            >
              {isFavoriting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Bookmark className={`w-4 h-4 ${summary.is_favorited ? 'fill-current' : ''}`} />
              )}
              <span>{summary.is_favorited ? '已收藏' : '收藏'}</span>
            </button>

            <button
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                window.open(summary.url, '_blank', 'noopener,noreferrer')
              }}
              className="flex items-center gap-1.5 text-sm text-x-gray hover:text-x-cyan transition-colors font-mono"
            >
              <ExternalLink className="w-4 h-4" />
              <span>原文</span>
            </button>

            <button
              onClick={handleDelete}
              disabled={isDeleting}
              className="flex items-center gap-1.5 text-sm text-x-gray hover:text-x-red transition-colors font-mono disabled:opacity-50"
            >
              {isDeleting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4" />
              )}
              <span>删除</span>
            </button>
          </div>

          {summary.summary_text.length > 150 && (
            <button
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                setIsExpanded(!isExpanded)
              }}
              className="flex items-center gap-1 text-xs text-x-gray hover:text-x-cyan transition-colors font-mono"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="w-4 h-4" />
                  <span>收起</span>
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4" />
                  <span>展开</span>
                </>
              )}
            </button>
          )}
        </div>
      </Link>
    </motion.article>
  )
}

export default SummaryCard
