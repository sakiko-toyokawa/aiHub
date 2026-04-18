import { NavLink, Outlet } from 'react-router-dom'
import { Home, Bookmark, Settings, Sparkles, Search, Menu, Sun, Moon, Terminal } from 'lucide-react'
import { useState } from 'react'
import Sidebar from './Sidebar'
import ParticleNetwork from './ParticleNetwork'
import { useCommandPalette } from './CommandPaletteProvider'
import { useTheme } from './ThemeProvider'

function Layout() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const { open: openCommandPalette } = useCommandPalette()
  const { resolvedTheme, toggleTheme } = useTheme()

  const isDark = resolvedTheme === 'dark'

  return (
    <div className="min-h-screen bg-x-black text-x-light-gray relative">
      {/* Three.js Particle Network */}
      <ParticleNetwork theme={isDark ? 'dark' : 'light'} />

      {/* Subtle grid overlay */}
      <div className="fixed inset-0 cyber-grid pointer-events-none z-[1] opacity-20" />

      {/* Subtle ambient glow */}
      <div
        className="fixed inset-0 pointer-events-none z-[1]"
        style={{
          background: 'radial-gradient(ellipse 60% 40% at 50% 0%, hsl(var(--x-cyan) / 0.04) 0%, transparent 70%)',
        }}
      />

      {/* Scan line overlay */}
      <div className="scan-overlay fixed inset-0 pointer-events-none z-[9998] opacity-30"
        style={{
          background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, hsl(var(--x-cyan) / 0.012) 2px, hsl(var(--x-cyan) / 0.012) 4px)',
        }}
      />

      <div className="max-w-[1265px] mx-auto flex relative z-10">
        {/* Left Sidebar - Navigation */}
        <header className="w-[275px] min-h-screen sticky top-0 flex flex-col border-r border-x-border/40 hidden md:flex">
          {/* Logo */}
          <div className="p-4">
            <NavLink to="/" className="inline-flex items-center gap-3 p-3 rounded-lg hover:bg-x-dark/80 transition-all group">
              <div className="relative">
                <Sparkles className="w-8 h-8 text-x-cyan group-hover:drop-shadow-[0_0_8px_hsl(var(--x-cyan))] dark:group-hover:drop-shadow-none transition-all" />
                <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-x-lime rounded-full animate-glow-pulse" />
              </div>
              <div>
                <span className="font-mono text-lg font-bold text-x-light-gray group-hover:text-x-cyan transition-colors">AI_HUB</span>
                <span className="block font-mono text-[10px] text-x-gray tracking-widest">v2.0.0 // ONLINE</span>
              </div>
            </NavLink>
          </div>

          <nav className="flex-1 px-2 space-y-1">
            <NavLink
              to="/"
              className={({ isActive }) =>
                `nav-item ${isActive ? 'active' : ''}`
              }
              end
            >
              <Home className="w-6 h-6" />
              <span>首页</span>
            </NavLink>

            <NavLink
              to="/favorites"
              className={({ isActive }) =>
                `nav-item ${isActive ? 'active' : ''}`
              }
            >
              <Bookmark className="w-6 h-6" />
              <span>收藏</span>
            </NavLink>

            <NavLink
              to="/settings"
              className={({ isActive }) =>
                `nav-item ${isActive ? 'active' : ''}`
              }
            >
              <Settings className="w-6 h-6" />
              <span>设置</span>
            </NavLink>
          </nav>

          {/* Theme Toggle */}
          <div className="px-4 pb-2">
            <button
              onClick={toggleTheme}
              className="w-full flex items-center gap-4 px-4 py-3 text-xl font-medium text-x-light-gray hover:bg-x-dark/80 transition-all duration-200 nav-item"
              title={isDark ? '切换到白天模式' : '切换到夜间模式'}
            >
              {isDark ? (
                <>
                  <Sun className="w-6 h-6 text-x-yellow" />
                  <span>白天模式</span>
                </>
              ) : (
                <>
                  <Moon className="w-6 h-6 text-x-cyan" />
                  <span>夜间模式</span>
                </>
              )}
            </button>
          </div>

          {/* Terminal-style user card */}
          <div className="p-4 border-t border-x-border/40">
            <div className="cyber-border p-4 group cursor-pointer">
              <div className="flex items-center gap-3">
                <div className="relative w-10 h-10">
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-x-cyan/30 to-x-magenta/30 flex items-center justify-center font-bold text-x-cyan font-mono border border-x-cyan/30 group-hover:border-x-cyan/60 transition-all">
                    AI
                  </div>
                  <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-x-lime rounded-full border-2 border-x-black animate-glow-pulse" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-mono font-bold text-sm truncate text-x-light-gray">AI_HUB</p>
                  <p className="font-mono text-xs text-x-gray truncate">@ai_knowledge</p>
                </div>
              </div>
              <div className="mt-3 flex items-center gap-2 text-[10px] font-mono text-x-gray">
                <Terminal className="w-3 h-3" />
                <span>SYSTEM_READY</span>
              </div>
            </div>
          </div>
        </header>

        {/* Mobile Header */}
        <header className="md:hidden fixed top-0 left-0 right-0 z-50 bg-x-black/90 backdrop-blur-xl border-b border-x-border/40">
          <div className="flex items-center justify-between px-4 py-3">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="p-2 rounded-lg hover:bg-x-dark/80 transition-colors"
            >
              <Menu className="w-6 h-6" />
            </button>
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-x-cyan" />
              <span className="font-mono text-sm font-bold">AI_HUB</span>
            </div>
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg hover:bg-x-dark/80 transition-colors"
            >
              {isDark ? <Sun className="w-5 h-5 text-x-yellow" /> : <Moon className="w-5 h-5 text-x-cyan" />}
            </button>
          </div>
        </header>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden fixed inset-0 z-40 bg-x-black/98 backdrop-blur-xl">
            <div className="pt-16 px-4 space-y-2">
              <NavLink to="/" className="nav-item" onClick={() => setIsMobileMenuOpen(false)}>
                <Home className="w-6 h-6" />
                <span>首页</span>
              </NavLink>
              <NavLink to="/favorites" className="nav-item" onClick={() => setIsMobileMenuOpen(false)}>
                <Bookmark className="w-6 h-6" />
                <span>收藏</span>
              </NavLink>
              <NavLink to="/settings" className="nav-item" onClick={() => setIsMobileMenuOpen(false)}>
                <Settings className="w-6 h-6" />
                <span>设置</span>
              </NavLink>
              <button
                onClick={() => {
                  toggleTheme()
                  setIsMobileMenuOpen(false)
                }}
                className="w-full flex items-center gap-4 px-4 py-3 text-xl font-medium text-x-light-gray hover:bg-x-dark/80 transition-all nav-item"
              >
                {isDark ? (
                  <>
                    <Sun className="w-6 h-6 text-x-yellow" />
                    <span>白天模式</span>
                  </>
                ) : (
                  <>
                    <Moon className="w-6 h-6 text-x-cyan" />
                    <span>夜间模式</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Main Content */}
        <main className="flex-1 min-w-0 min-h-screen md:border-r border-x-border/40">
          {/* Top bar */}
          <div className="md:sticky md:top-0 bg-x-black/80 backdrop-blur-xl z-30 border-b border-x-border/40">
            <div className="flex items-center justify-between px-4 py-3">
              <div className="hidden md:flex items-center gap-2">
                <span className="text-x-cyan font-mono text-sm animate-flicker">⬤</span>
                <h1 className="text-lg font-bold font-mono tracking-wide">AI 知识聚合</h1>
              </div>
              <div className="md:hidden w-8" />
              <div className="flex items-center gap-4">
                <button
                  onClick={openCommandPalette}
                  className="relative flex items-center gap-2 px-3 py-2 rounded-lg bg-x-dark/80 border border-x-border/60 hover:border-x-cyan/40 transition-all text-left group"
                >
                  <Search className="w-4 h-4 text-x-gray group-hover:text-x-cyan transition-colors" />
                  <span className="text-sm text-x-gray hidden md:inline">搜索命令...</span>
                  <span className="text-sm text-x-gray md:hidden">搜索...</span>
                  <kbd className="ml-2 hidden md:inline px-1.5 py-0.5 text-[10px] font-mono border border-x-border/60 rounded text-x-gray bg-x-dark">
                    CTRL+K
                  </kbd>
                </button>
              </div>
            </div>
          </div>

          <div className="pt-16 md:pt-0">
            <Outlet />
          </div>
        </main>

        {/* Right Sidebar */}
        <aside className="w-[380px] hidden lg:block flex-shrink-0 pl-6 py-4">
          <Sidebar />
        </aside>
      </div>
    </div>
  )
}

export default Layout
