import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Filter, RefreshCw, Github, BookOpen, Video, Bot, AlertCircle, Check, ChevronLeft, ChevronRight, Zap, Layout, Newspaper } from 'lucide-react'
import SummaryCard from '../components/SummaryCard'
import { summariesApi, crawlerApi } from '../api/client'
import type { Summary } from '../types'

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

function Dashboard() {
  const [activeFilter, setActiveFilter] = useState<string>('all')
  const [page, setPage] = useState(1)
  const [crawlMessage, setCrawlMessage] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['summaries', activeFilter, page],
    queryFn: () => fetchSummaries(activeFilter, page),
    staleTime: 5000,
    gcTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
  })

  const summaries = data?.items || []
  const total = data?.total || 0
  const totalPages = Math.ceil(total / PAGE_SIZE)

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

  const filters = [
    { id: 'all', label: '全部', icon: Filter },
    { id: 'github', label: 'GitHub', icon: Github },
    { id: 'zhihu', label: '知乎', icon: BookOpen },
    { id: 'bilibili', label: 'B站', icon: Video },
    { id: 'anthropic', label: 'Anthropic', icon: Zap },
    { id: 'builderio', label: 'Builder.io', icon: Layout },
    { id: 'hackernews', label: 'HN', icon: Newspaper },
  ]

  return (
    <div>
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
                onClick={() => {
                  setActiveFilter(filter.id)
                  setPage(1)
                }}
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
            {/* Crawl Now Button */}
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
        {isLoading ? (
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
        ) : summaries && summaries.length > 0 ? (
          summaries.map((summary, index) => (
            <SummaryCard
              key={summary.id}
              summary={summary}
              index={index}
              onDelete={(id) => deleteMutation.mutate(id)}
              onFavorite={(id) => favoriteMutation.mutate(id)}
              isDeleting={deleteMutation.isPending && deleteMutation.variables === summary.id}
              isFavoriting={favoriteMutation.isPending && favoriteMutation.variables === summary.id}
            />
          ))
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

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="p-6 border-t border-x-border/40">
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1 || isLoading}
              className="flex items-center gap-1 px-4 py-2 rounded-lg text-sm font-medium text-x-gray hover:text-x-cyan hover:bg-x-dark/60 disabled:opacity-40 disabled:cursor-not-allowed transition-all font-mono border border-transparent hover:border-x-border/60"
            >
              <ChevronLeft className="w-4 h-4" />
              上一页
            </button>

            <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-x-dark/60 border border-x-border/40 font-mono">
              <span className="text-x-cyan font-bold">{page}</span>
              <span className="text-x-gray">/</span>
              <span className="text-x-gray">{totalPages}</span>
            </div>

            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages || isLoading}
              className="flex items-center gap-1 px-4 py-2 rounded-lg text-sm font-medium text-x-gray hover:text-x-cyan hover:bg-x-dark/60 disabled:opacity-40 disabled:cursor-not-allowed transition-all font-mono border border-transparent hover:border-x-border/60"
            >
              下一页
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <div className="text-center mt-3 text-xs font-mono text-x-gray">
            共 {total} 条内容
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
