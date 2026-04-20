import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Heart, Bookmark, ExternalLink, Sparkles, ChevronDown, ChevronUp, Trash2, Loader2, Highlighter, Archive, RotateCcw } from 'lucide-react'
import { motion } from 'framer-motion'
import type { Summary } from '../types'
import { PLATFORM_COLORS, PLATFORM_NAMES, PLATFORM_GLOW } from '../constants/platforms'

interface SummaryCardProps {
  summary: Summary
  index?: number
  onDelete?: (id: number) => void
  onFavorite?: (id: number) => void
  onArchive?: (id: number) => void
  onUnarchive?: (id: number) => void
  isDeleting?: boolean
  isFavoriting?: boolean
  isArchiving?: boolean
  isUnarchiving?: boolean
  showArchive?: boolean
  showUnarchive?: boolean
}

function SummaryCard({
  summary,
  index = 0,
  onDelete,
  onFavorite,
  onArchive,
  onUnarchive,
  isDeleting = false,
  isFavoriting = false,
  isArchiving = false,
  isUnarchiving = false,
  showArchive = true,
  showUnarchive = false,
}: SummaryCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const navigate = useNavigate()

  const handleCardClick = (e: React.MouseEvent) => {
    // 如果点击的是按钮或其子元素，不触发导航
    const target = e.target as HTMLElement
    if (target.closest('button')) return
    navigate(`/summary/${summary.id}`)
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

  const handleArchive = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (onArchive) {
      onArchive(summary.id)
    }
  }

  const handleUnarchive = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (onUnarchive) {
      onUnarchive(summary.id)
    }
  }

  return (
    <motion.article
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className={`cyber-border p-5 mb-3 cursor-pointer group ${PLATFORM_GLOW[summary.platform] || ''}`}
    >
      <div onClick={handleCardClick} className="block">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`platform-badge ${PLATFORM_COLORS[summary.platform] || 'bg-x-gray border-x-gray'}`}>
              {PLATFORM_NAMES[summary.platform] || summary.platform}
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

        {/* Highlight Sentence */}
        {summary.highlight_sentence && (
          <div className="mb-3 p-3 rounded-lg bg-x-yellow/5 border border-x-yellow/20">
            <div className="flex items-start gap-2">
              <Highlighter className="w-4 h-4 text-x-yellow mt-0.5 flex-shrink-0" />
              <p className="text-sm text-x-light-gray/90 italic leading-relaxed">
                "{summary.highlight_sentence}"
              </p>
            </div>
          </div>
        )}

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

        {/* Read Progress */}
        {summary.read_progress > 0 && summary.read_progress < 100 && (
          <div className="mb-3 flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-x-border/30 rounded-full overflow-hidden">
              <div
                className="h-full bg-x-cyan rounded-full transition-all duration-500"
                style={{
                  width: `${summary.read_progress}%`,
                  boxShadow: '0 0 6px hsl(var(--x-cyan) / 0.5)',
                }}
              />
            </div>
            <span className="text-[10px] font-mono text-x-cyan">{summary.read_progress}%</span>
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
              <span>{summary.is_read ? '已读' : summary.read_progress > 0 ? `${summary.read_progress}%` : '未读'}</span>
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

            {showArchive && (
              <button
                onClick={handleArchive}
                disabled={isArchiving}
                className="flex items-center gap-1.5 text-sm text-x-gray hover:text-x-yellow transition-colors font-mono disabled:opacity-50"
              >
                {isArchiving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Archive className="w-4 h-4" />
                )}
                <span>归档</span>
              </button>
            )}

            {showUnarchive && (
              <button
                onClick={handleUnarchive}
                disabled={isUnarchiving}
                className="flex items-center gap-1.5 text-sm text-x-gray hover:text-x-lime transition-colors font-mono disabled:opacity-50"
              >
                {isUnarchiving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <RotateCcw className="w-4 h-4" />
                )}
                <span>恢复</span>
              </button>
            )}

            {showUnarchive && onDelete && (
              <button
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  onDelete(summary.id)
                }}
                disabled={isDeleting}
                className="flex items-center gap-1.5 text-sm text-x-gray hover:text-x-red transition-colors font-mono disabled:opacity-50"
              >
                {isDeleting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Trash2 className="w-4 h-4" />
                )}
                <span>永久删除</span>
              </button>
            )}

            {!showArchive && !showUnarchive && (
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
            )}
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
      </div>
    </motion.article>
  )
}

export default SummaryCard
