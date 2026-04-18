import { useQuery } from '@tanstack/react-query'
import { TrendingUp, Github, BookOpen, Video, Twitter, Zap, BookMarked, RefreshCw, Layout, Newspaper, Activity, Cpu, Rss, Globe } from 'lucide-react'
import { statsApi, sourcesApi } from '../api/client'

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

const PLATFORM_COLORS: Record<string, string> = {
  github: 'bg-[#24292e] border-[#4a5568]',
  zhihu: 'bg-[#0084ff]/15 border-[#0084ff]/40',
  bilibili: 'bg-[#fb7299]/15 border-[#fb7299]/40',
  twitter: 'bg-[#1da1f2]/15 border-[#1da1f2]/40',
  anthropic: 'bg-[#d97757]/15 border-[#d97757]/40',
  builderio: 'bg-[#a855f7]/15 border-[#a855f7]/40',
  hackernews: 'bg-[#ff6600]/15 border-[#ff6600]/40',
  rss: 'bg-[#f26522]/15 border-[#f26522]/40',
}

const PLATFORM_NAMES: Record<string, string> = {
  github: 'GitHub',
  zhihu: '知乎',
  bilibili: 'Bilibili',
  twitter: 'X',
  anthropic: 'Anthropic',
  builderio: 'Builder.io',
  hackernews: 'Hacker News',
  rss: 'RSS',
}

function Sidebar() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: statsApi.get,
  })

  const { data: sources, isLoading: sourcesLoading } = useQuery({
    queryKey: ['sources'],
    queryFn: sourcesApi.list,
  })

  const statsItems = [
    { label: '总摘要', value: stats?.total_summaries ?? 0, icon: Zap, color: 'text-x-yellow' },
    { label: '已读', value: stats?.read_count ?? 0, icon: BookOpen, color: 'text-x-lime' },
    { label: '收藏', value: stats?.favorite_count ?? 0, icon: BookMarked, color: 'text-x-pink' },
    { label: '数据源', value: stats?.active_sources ?? 0, icon: TrendingUp, color: 'text-x-cyan' },
  ]

  return (
    <div className="space-y-5">
      {/* Stats Panel */}
      <div className="cyber-border p-5">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-4 h-4 text-x-cyan" />
          <h3 className="cyber-section-title mb-0">数据统计</h3>
        </div>
        <div className="space-y-2">
          {statsLoading ? (
            <div className="flex items-center justify-center py-4">
              <RefreshCw className="w-5 h-5 animate-spin text-x-cyan" />
            </div>
          ) : (
            statsItems.map((stat) => (
              <div
                key={stat.label}
                className="flex items-center justify-between p-3 hover:bg-x-cyan/5 rounded-lg transition-all group cursor-pointer border border-transparent hover:border-x-cyan/10"
              >
                <div className="flex items-center gap-3">
                  <stat.icon className={`w-4 h-4 ${stat.color} group-hover:drop-shadow-[0_0_6px_currentColor] dark:group-hover:drop-shadow-none transition-all`} />
                  <span className="font-mono text-sm text-x-gray">{stat.label}</span>
                </div>
                <span className="font-mono font-bold text-lg text-x-light-gray">{stat.value}</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Data Sources Panel */}
      <div className="cyber-border p-5">
        <div className="flex items-center gap-2 mb-4">
          <Cpu className="w-4 h-4 text-x-magenta" />
          <h3 className="cyber-section-title mb-0">数据源</h3>
        </div>
        <div className="space-y-2">
          {sourcesLoading ? (
            <div className="flex items-center justify-center py-4">
              <RefreshCw className="w-5 h-5 animate-spin text-x-cyan" />
            </div>
          ) : (
            sources?.map((source) => {
              const Icon = PLATFORM_ICONS[source.platform] || Globe
              const color = PLATFORM_COLORS[source.platform] || 'bg-x-border/40 border-x-border/60'
              const name = PLATFORM_NAMES[source.platform] || source.name || source.platform
              return (
                <div
                  key={source.id}
                  className="flex items-center justify-between p-3 hover:bg-x-cyan/5 rounded-lg transition-all cursor-pointer group border border-transparent hover:border-x-cyan/10"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 ${color} rounded-lg flex items-center justify-center border`}>
                      <Icon className="w-4 h-4 text-white" />
                    </div>
                    <span className="font-mono text-sm group-hover:text-x-cyan transition-colors">
                      {name}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`status-dot ${source.is_active ? 'status-active' : 'status-inactive'}`} />
                    <span className={`font-mono text-xs ${source.is_active ? 'text-x-lime' : 'text-x-gray'}`}>
                      {source.is_active ? 'ONLINE' : 'OFFLINE'}
                    </span>
                  </div>
                </div>
              )
            })
          )}
        </div>
      </div>

      {/* Platform Stats from API */}
      {stats?.platforms && stats.platforms.length > 0 && (
        <div className="cyber-border p-5">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-x-violet" />
            <h3 className="cyber-section-title mb-0">内容分布</h3>
          </div>
          <div className="space-y-3">
            {stats.platforms.map((platform) => {
              const Icon = PLATFORM_ICONS[platform.platform] || Globe
              const color = PLATFORM_COLORS[platform.platform] || 'bg-x-border/40 border-x-border/60'
              const name = PLATFORM_NAMES[platform.platform] || platform.platform
              return (
                <div
                  key={platform.platform}
                  className="flex items-center justify-between p-3 rounded-lg group"
                >
                  <div className="flex items-center gap-2">
                    <div className={`w-6 h-6 ${color} rounded flex items-center justify-center`}>
                      <Icon className="w-3 h-3 text-white" />
                    </div>
                    <span className="font-mono text-xs text-x-gray">{name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1.5 bg-x-border/40 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-x-cyan rounded-full transition-all duration-500"
                        style={{
                          width: `${Math.min(100, (platform.summary_count / (stats.total_summaries || 1)) * 100)}%`,
                          boxShadow: '0 0 6px hsl(var(--x-cyan) / 0.5)',
                        }}
                      />
                    </div>
                    <span className="font-mono text-xs text-x-light-gray">{platform.summary_count}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="font-mono text-[10px] text-x-gray px-4 space-x-2 tracking-wide">
        <a href="#" className="hover:text-x-cyan transition-colors">关于</a>
        <span>·</span>
        <a href="#" className="hover:text-x-cyan transition-colors">隐私</a>
        <span>·</span>
        <a href="#" className="hover:text-x-cyan transition-colors">帮助</a>
        <p className="mt-2 text-x-gray/60">© 2026 AI_KNOWLEDGE_HUB // v2.0.0</p>
      </div>
    </div>
  )
}

export default Sidebar
