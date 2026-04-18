import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Bookmark, Search, RefreshCw, AlertCircle, Star } from 'lucide-react'
import SummaryCard from '../components/SummaryCard'
import { summariesApi } from '../api/client'

function Favorites() {
  const [searchQuery, setSearchQuery] = useState('')

  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['summaries', 'favorites'],
    queryFn: () => summariesApi.list({ is_favorited: true, page_size: 100 }),
  })

  const favorites = data?.items || []

  // Client-side search filtering
  const filteredFavorites = searchQuery
    ? favorites.filter((item) =>
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.summary_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.tags?.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    : favorites

  return (
    <div>
      {/* Header */}
      <div className="sticky top-[57px] md:top-0 z-20 bg-x-black/90 backdrop-blur-xl border-b border-x-border/40"
      >
        <div className="px-4 py-3"
        >
          <div className="flex items-center gap-2"
          >
            <Star className="w-5 h-5 text-x-cyan" /
          >
            <h1 className="font-bold text-xl font-mono tracking-wide"
            >我的收藏</h1
          >
          </div
        >
          <p className="font-mono text-sm text-x-gray mt-1"
          >
            {isLoading ? '加载数据流...' : `${favorites.length} 条收藏内容`}
          </p
        >
        </div
      >
      </div>

      {/* Search */}
      <div className="p-4 border-b border-x-border/40"
      >
        <div className="relative"
        >
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-x-gray" /
        >
          <input
            type="text"
            placeholder="搜索收藏内容..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full x-input pl-10"
          /
        >
        </div
      >
      </div>

      {/* Content */}
      <div className="px-4 py-4 space-y-3"
      >
        {isLoading ? (
          <div className="py-12 text-center"
          >
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-x-cyan" /
          >
            <p className="font-mono text-x-gray animate-pulse"
            >加载数据流...</p
          >
          </div
        >
        ) : error ? (
          <div className="py-12 text-center"
          >
            <div className="w-16 h-16 mx-auto mb-4 rounded-lg bg-x-red/10 border border-x-red/20 flex items-center justify-center"
            >
              <AlertCircle className="w-8 h-8 text-x-red" /
            >
            </div
          >
            <p className="font-mono text-x-red mb-2"
            >加载失败</p
          >
            <p className="font-mono text-sm text-x-gray mb-4"
            >
              {error instanceof Error ? error.message : '请检查网络连接或稍后重试'}
            </p
          >
            <button
              onClick={() => refetch()}
              className="x-button-secondary font-mono"
            >
              重试
            </button
          >
          </div
        >
        ) : filteredFavorites.length > 0 ? (
          filteredFavorites.map((summary, index) => (
            <SummaryCard key={summary.id} summary={summary} index={index} /
          >
          ))
        ) : searchQuery ? (
          <div className="py-12 text-center"
          >
            <div className="w-16 h-16 mx-auto mb-4 rounded-lg bg-x-dark border border-x-border/60 flex items-center justify-center"
            >
              <Search className="w-8 h-8 text-x-gray" /
            >
            </div
          >
            <p className="font-mono text-x-gray mb-2"
            >未找到匹配内容</p
          >
            <p className="font-mono text-sm text-x-gray/60"
            >
              尝试其他搜索关键词
            </p
          >
          </div
        >
        ) : (
          <div className="py-12 text-center"
          >
            <div className="w-16 h-16 mx-auto mb-4 rounded-lg bg-x-dark border border-x-border/60 flex items-center justify-center"
            >
              <Bookmark className="w-8 h-8 text-x-gray" /
            >
            </div
          >
            <p className="font-mono text-x-gray mb-2"
            >暂无收藏</p
          >
            <p className="font-mono text-sm text-x-gray/60"
            >
              点击内容卡片上的收藏按钮添加
            </p
          >
          </div
        >
        )}
      </div
    >
    </div
  >
  )
}

export default Favorites
