import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Archive, Search, RefreshCw, AlertCircle } from 'lucide-react'
import SummaryCard from '../components/SummaryCard'
import { summariesApi } from '../api/client'

function ArchivePage() {
  const [searchQuery, setSearchQuery] = useState('')
  const queryClient = useQueryClient()

  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['summaries', 'archived'],
    queryFn: () => summariesApi.list({ is_archived: true, page_size: 100 }),
  })

  const archived = data?.items || []

  // Client-side search filtering
  const filteredArchived = searchQuery
    ? archived.filter((item) =>
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.summary_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.tags?.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    : archived

  const unarchiveMutation = useMutation({
    mutationFn: (id: number) => summariesApi.unarchive(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['summaries', 'archived'] })
      queryClient.invalidateQueries({ queryKey: ['summaries'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })

  const permanentDeleteMutation = useMutation({
    mutationFn: (id: number) => summariesApi.permanentlyDelete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['summaries', 'archived'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })

  return (
    <div>
      {/* Header */}
      <div className="sticky top-[57px] md:top-0 z-20 bg-x-black/90 backdrop-blur-xl border-b border-x-border/40">
        <div className="px-4 py-3">
          <div className="flex items-center gap-2">
            <Archive className="w-5 h-5 text-x-yellow" />
            <h1 className="font-bold text-xl font-mono tracking-wide">回收站</h1>
          </div>
          <p className="font-mono text-sm text-x-gray mt-1">
            {isLoading ? '加载数据流...' : `${archived.length} 条已归档内容`}
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="p-4 border-b border-x-border/40">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-x-gray" />
          <input
            type="text"
            placeholder="搜索已归档内容..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full x-input pl-10"
          />
        </div>
      </div>

      {/* Content */}
      <div className="px-4 py-4 space-y-3">
        {isLoading ? (
          <div className="py-12 text-center">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-x-cyan" />
            <p className="font-mono text-x-gray animate-pulse">加载数据流...</p>
          </div>
        ) : error ? (
          <div className="py-12 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-lg bg-x-red/10 border border-x-red/20 flex items-center justify-center">
              <AlertCircle className="w-8 h-8 text-x-red" />
            </div>
            <p className="font-mono text-x-red mb-2">加载失败</p>
            <p className="font-mono text-sm text-x-gray mb-4">
              {error instanceof Error ? error.message : '请检查网络连接或稍后重试'}
            </p>
            <button
              onClick={() => refetch()}
              className="x-button-secondary font-mono"
            >
              重试
            </button>
          </div>
        ) : filteredArchived.length > 0 ? (
          filteredArchived.map((summary, index) => (
            <SummaryCard
              key={summary.id}
              summary={summary}
              index={index}
              onUnarchive={(id) => unarchiveMutation.mutate(id)}
              onDelete={(id) => {
                if (confirm('确定要永久删除这条内容吗？此操作不可恢复。')) {
                  permanentDeleteMutation.mutate(id)
                }
              }}
              isUnarchiving={unarchiveMutation.isPending && unarchiveMutation.variables === summary.id}
              isDeleting={permanentDeleteMutation.isPending && permanentDeleteMutation.variables === summary.id}
              showArchive={false}
              showUnarchive={true}
            />
          ))
        ) : searchQuery ? (
          <div className="py-12 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-lg bg-x-dark border border-x-border/60 flex items-center justify-center">
              <Search className="w-8 h-8 text-x-gray" />
            </div>
            <p className="font-mono text-x-gray mb-2">未找到匹配内容</p>
            <p className="font-mono text-sm text-x-gray/60">
              尝试其他搜索关键词
            </p>
          </div>
        ) : (
          <div className="py-12 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-lg bg-x-dark border border-x-border/60 flex items-center justify-center">
              <Archive className="w-8 h-8 text-x-gray" />
            </div>
            <p className="font-mono text-x-gray mb-2">回收站为空</p>
            <p className="font-mono text-sm text-x-gray/60">
              归档的内容会出现在这里，可随时恢复或永久删除
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default ArchivePage
