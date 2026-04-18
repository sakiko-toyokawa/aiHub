import { useState, useEffect, useRef, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Filter, RefreshCw, Github, BookOpen, Video, Bot, AlertCircle, Check, Zap, Layout, Newspaper, Globe, Rss, Twitter, Loader2 } from 'lucide-react'
import SummaryCard from '../components/SummaryCard'
import { summariesApi, crawlerApi, sourcesApi } from '../api/client'
import type { Summary, Source } from '../types'

const PAGE_SIZE = 20

const fetchSummaries = async (platform: string, page: number): Promise<{ items: Summary[]; total: number; page: number; page_size: number }> => {
  try {
    const response = await summariesApi.list({
      platform: platform === 'all' ? undefined : platform,
      page,
      page_size: PAGE_SIZE,
    })
    return response
  } catch (error) {
    console.error('Failed to fetch summaries:', error)
    return { items: [], total: 0, page: 1, page_size: PAGE_SIZE }
  }
}

const PLATFORM_ICONS: Record<string, typeof Github> = {
  github: Github,
  zhihu: BookOpen,
  bilibili: Video,
  twitter: Twitter,
  anthropic: Zap,
  builderio: Layout,
  hackernews: Newspaper,
  rss: Rss,
}

const PLATFORM_LABELS: Record<string, string> = {
  github: 'GitHub',
  zhihu: '知乎',
  bilibili: 'B站',
  twitter: 'X',
  anthropic: 'Anthropic',
  builderio: 'Builder.io',
  hackernews: 'HN',
  rss: 'RSS',
}

function Dashboard() {
  const [activeFilter, setActiveFilter] = useState<string>('all')
  const [page, setPage] = useState(1)
  const [crawlMessage, setCrawlMessage] = useState<string | null>(null)
  const [allSummaries, setAllSummaries] = useState<Summary[]>([])
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [hasMore, setHasMore] = useState(true)
  const sentinelRef = useRef<HTMLDivElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['summaries', activeFilter, page],
    queryFn: () => fetchSummaries(activeFilter, page),
    staleTime: 5000,
    gcTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
  })

  const { data: sources } = useQuery<Source[]>({
    queryKey: ['sources'],
    queryFn: sourcesApi.list,
    staleTime: 30 * 1000,
    refetchOnWindowFocus: false,
  })

  // 累积数据：新页数据追加到 allSummaries
  useEffect(() => {
    if (data?.items) {
      if (page === 1) {
        setAllSummaries(data.items)
      } else {
        setAllSummaries(prev => {
          const existingIds = new Set(prev.map(s => s.id))
          const newItems = data.items.filter(s => !existingIds.has(s.id))
          return [...prev, ...newItems]
        })
      }
      setHasMore(data.items.length === PAGE_SIZE && allSummaries.length + data.items.length < (data.total || 0))
    }
  }, [data, page])

  // filter 改变时重置
  const handleFilterChange = useCallback((filterId: string) => {
    setActiveFilter(filterId)
    setPage(1)
    setAllSummaries([])
    setSelectedIndex(-1)
    setHasMore(true)
  }, [])

  // 无限滚动：IntersectionObserver
  useEffect(() => {
    if (!sentinelRef.current || isFetching || !hasMore) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !isFetching) {
          setPage(p => p + 1)
        }
      },
      { rootMargin: '200px' }
    )
    observer.observe(sentinelRef.current)
    return () => observer.disconnect()
  }, [hasMore, isFetching])

  // 键盘快捷键
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // 忽略输入框中的快捷键
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) return

      switch (e.key.toLowerCase()) {
        case 'j':
        case 'arrowdown':
          e.preventDefault()
          setSelectedIndex(prev => {
            const next = Math.min(allSummaries.length - 1, prev + 1)
            scrollToIndex(next)
            return next
          })
          break
        case 'k':
        case 'arrowup':
          e.preventDefault()
          setSelectedIndex(prev => {
            const next = Math.max(0, prev - 1)
            scrollToIndex(next)
            return next
          })
          break
        case 'f':
          e.preventDefault()
          if (selectedIndex >= 0 && selectedIndex < allSummaries.length) {
            favoriteMutation.mutate(allSummaries[selectedIndex].id)
          }
          break
        case 'r':
          e.preventDefault()
          if (selectedIndex >= 0 && selectedIndex < allSummaries.length) {
            markReadMutation.mutate(allSummaries[selectedIndex].id)
          }
          break
        case 'enter':
          e.preventDefault()
          if (selectedIndex >= 0 && selectedIndex < allSummaries.length) {
            window.location.href = `/summary/${allSummaries[selectedIndex].id}`
          }
          break
      }
    }

    const scrollToIndex = (index: number) => {
      const el = document.getElementById(`summary-card-${allSummaries[index]?.id}`)
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [allSummaries, selectedIndex])

  // 动态构建 filter
  const filters = [{ id: 'all', label: '全部', icon: Filter }]
  const seenPlatforms = new Set<string>()
  sources?.forEach((s) => {
    if (!seenPlatforms.has(s.platform)) {
      seenPlatforms.add(s.platform)
      filters.push({
        id: s.platform,
        label: PLATFORM_LABELS[s.platform] || s.name || s.platform,
        icon: PLATFORM_ICONS[s.platform] || Globe,
      })
    }
  })

  const crawlMutation = useMutation({
    mutationFn: () => crawlerApi.trigger(),
    onSuccess: (result: { message: string }) => {
      setCrawlMessage(result.message)
      queryClient.invalidateQueries({ queryKey: ['summaries'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
      setTimeout(() => setCrawlMessage(null), 5000)
    },
    onError: (error: Error) => {
      setCrawlMessage(error instanceof Error ? error.message : '抓取失败')
      setTimeout(() => setCrawlMessage(null), 5000)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => summariesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['summaries'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })

  const favoriteMutation = useMutation({
    mutationFn: (id: number) => summariesApi.toggleFavorite(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['summaries'] })
    },
  })

  const markReadMutation = useMutation({
    mutationFn: (id: number) => summariesApi.markAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['summaries'] })
    },
  })

  return (
    <div ref={contentRef}>
      {/* Keyboard shortcut hint */}
      <div className="px-4 py-1.5 border-b border-x-border/20 bg-x-dark/40 font-mono text-[10px] text-x-gray/60 flex items-center gap-3 overflow-x-auto scrollbar-hide">
        <span>快捷键:</span>
        <span><kbd className="px-1 rounded bg-x-border/30">j</kbd>/<kbd className="px-1 rounded bg-x-border/30">k</kbd> 导航</span>
        <span><kbd className="px-1 rounded bg-x-border/30">f</kbd> 收藏</span>
        <span><kbd className="px-1 rounded bg-x-border/30">r</kbd> 已读</span>
        <span><kbd className="px-1 rounded bg-x-border/30">Enter</kbd> 详情</span>
      </div>

      {/* Crawl Message */}
      {crawlMessage && (
        <div className={`px-4 py-2 border-b border-x-border/40 font-mono text-sm ${
          crawlMessage.includes('失败') || crawlMessage.includes('error')
            ? 'bg-x-red/10 text-x-red border-x-red/20'
            : 'bg-x-lime/10 text-x-lime border-x-lime/20'
        }`}>
          <div className="flex items-center gap-2">
            {crawlMessage.includes('失败') || crawlMessage.includes('error') ? (
              <AlertCircle className="w-4 h-4" />
            ) : (
              <Check className="w-4 h-4" />
            )}
            <span>{crawlMessage}</span>
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <div className="sticky top-[57px] md:top-0 z-20 bg-x-black/90 backdrop-blur-xl border-b border-x-border/40">
        <div className="flex items-center justify-between px-4 py-2.5">
          <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-hide">
            {filters.map((filter) => (
              <button
                key={filter.id}
                onClick={() => handleFilterChange(filter.id)}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all font-mono ${
                  activeFilter === filter.id
                    ? 'bg-x-cyan/15 text-x-cyan border border-x-cyan/40 shadow-[0_0_15px_hsl(var(--x-cyan)/0.15)] dark:shadow-none'
                    : 'text-x-gray border border-transparent hover:border-x-border/60 hover:text-x-light-gray hover:bg-x-dark/60'
                }`}
              >
                <filter.icon className="w-3.5 h-3.5" />
                {filter.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <div className="relative group">
              <button
                onClick={() => crawlMutation.mutate()}
                disabled={crawlMutation.isPending}
                className="flex items-center justify-center w-9 h-9 rounded-lg bg-x-cyan/10 text-x-cyan border border-x-cyan/30 hover:bg-x-cyan/20 hover:border-x-cyan/50 hover:shadow-[0_0_15px_hsl(var(--x-cyan)/0.2)] dark:hover:shadow-none transition-all disabled:opacity-50"
                title="立即抓取"
              >
                {crawlMutation.isPending ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Bot className="w-4 h-4" />
                )}
              </button>
              <span className="absolute top-full left-1/2 -translate-x-1/2 mt-1.5 px-2 py-1 bg-x-dark border border-x-border/60 text-x-light-gray text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none hidden md:block font-mono">
                {crawlMutation.isPending ? '抓取中...' : '立即抓取'}
              </span>
            </div>

            <button
              onClick={() => refetch()}
              className="p-2 rounded-lg hover:bg-x-dark/80 text-x-gray hover:text-x-cyan transition-all border border-transparent hover:border-x-border/60"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 py-4 space-y-3">
        {isLoading && page === 1 ? (
          <div className="py-12 text-center">
            <div className="relative inline-flex items-center justify-center mb-6">
              <RefreshCw className="w-8 h-8 animate-spin text-x-cyan" />
              <div className="absolute inset-0 animate-glow-pulse rounded-full" />
            </div>
            <p className="font-mono text-x-gray animate-pulse">加载数据流...</p>
          </div>
        ) : error ? (
          <div className="py-12 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-lg bg-x-red/10 border border-x-red/20 flex items-center justify-center">
              <AlertCircle className="w-8 h-8 text-x-red" />
            </div>
            <p className="font-mono text-x-red mb-2">加载失败</p>
            <p className="font-mono text-sm text-x-gray">
              请检查网络连接或稍后重试
            </p>
            <button
              onClick={() => refetch()}
              className="mt-4 x-button-secondary font-mono"
            >
              重试
            </button>
          </div>
        ) : allSummaries.length > 0 ? (
          <>
            {allSummaries.map((summary, index) => (
              <div
                key={summary.id}
                id={`summary-card-${summary.id}`}
                className={`transition-all duration-200 rounded-xl ${
                  selectedIndex === index
                    ? 'ring-2 ring-x-cyan/60 ring-offset-2 ring-offset-x-black'
                    : ''
                }`}
              >
                <SummaryCard
                  summary={summary}
                  index={index}
                  onDelete={(id) => deleteMutation.mutate(id)}
                  onFavorite={(id) => favoriteMutation.mutate(id)}
                  isDeleting={deleteMutation.isPending && deleteMutation.variables === summary.id}
                  isFavoriting={favoriteMutation.isPending && favoriteMutation.variables === summary.id}
                />
              </div>
            ))}
            {/* Infinite scroll sentinel */}
            <div ref={sentinelRef} className="py-4 flex items-center justify-center">
              {isFetching && page > 1 ? (
                <div className="flex items-center gap-2 text-x-gray font-mono text-sm">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  加载更多...
                </div>
              ) : !hasMore ? (
                <span className="text-x-gray/50 font-mono text-xs">
                  共 {allSummaries.length} 条内容
                </span>
              ) : null}
            </div>
          </>
        ) : (
          <div className="py-12 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-lg bg-x-dark border border-x-border/60 flex items-center justify-center">
              <BookOpen className="w-8 h-8 text-x-gray" />
            </div>
            <p className="font-mono text-x-gray mb-2">暂无内容</p>
            <p className="font-mono text-sm text-x-gray/60">
              点击右上角"立即抓取"获取最新内容
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
