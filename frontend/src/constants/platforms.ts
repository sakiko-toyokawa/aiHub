import {
  Github,
  BookOpen,
  Video,
  Twitter,
  Zap,
  Layout,
  Newspaper,
  Rss,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export const PLATFORM_ICONS: Record<string, LucideIcon> = {
  github: Github,
  zhihu: BookOpen,
  bilibili: Video,
  twitter: Twitter,
  anthropic: Zap,
  builderio: Layout,
  hackernews: Newspaper,
  rss: Rss,
}

export const PLATFORM_LABELS: Record<string, string> = {
  github: 'GitHub',
  zhihu: '知乎',
  bilibili: 'B站',
  twitter: 'X',
  anthropic: 'Anthropic',
  builderio: 'Builder.io',
  hackernews: 'HN',
  rss: 'RSS',
}

export const PLATFORM_NAMES: Record<string, string> = {
  github: 'GitHub',
  zhihu: '知乎',
  bilibili: 'Bilibili',
  twitter: 'X',
  anthropic: 'Anthropic',
  builderio: 'Builder.io',
  hackernews: 'Hacker News',
  rss: 'RSS',
}

export const PLATFORM_COLORS: Record<string, string> = {
  github: 'bg-[#24292e]/80 border-[#4a5568]',
  zhihu: 'bg-[#0084ff]/15 border-[#0084ff]/30',
  bilibili: 'bg-[#fb7299]/15 border-[#fb7299]/30',
  twitter: 'bg-[#1da1f2]/15 border-[#1da1f2]/30',
  anthropic: 'bg-[#d97757]/15 border-[#d97757]/30',
  builderio: 'bg-[#a855f7]/15 border-[#a855f7]/30',
  hackernews: 'bg-[#ff6600]/15 border-[#ff6600]/30',
  rss: 'bg-[#f26522]/15 border-[#f26522]/30',
}

export const PLATFORM_GLOW: Record<string, string> = {
  github: 'hover:shadow-[0_0_20px_rgba(74,85,104,0.15)] dark:hover:shadow-none',
  zhihu: 'hover:shadow-[0_0_20px_rgba(0,132,255,0.15)] dark:hover:shadow-none',
  bilibili: 'hover:shadow-[0_0_20px_rgba(251,114,153,0.15)] dark:hover:shadow-none',
  twitter: 'hover:shadow-[0_0_20px_rgba(29,161,242,0.15)] dark:hover:shadow-none',
  anthropic: 'hover:shadow-[0_0_20px_rgba(217,119,87,0.15)] dark:hover:shadow-none',
  builderio: 'hover:shadow-[0_0_20px_rgba(168,85,247,0.15)] dark:hover:shadow-none',
  hackernews: 'hover:shadow-[0_0_20px_rgba(255,102,0,0.15)] dark:hover:shadow-none',
  rss: 'hover:shadow-[0_0_20px_rgba(242,101,34,0.15)] dark:hover:shadow-none',
}
