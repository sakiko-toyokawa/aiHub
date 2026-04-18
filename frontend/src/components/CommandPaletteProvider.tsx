import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import type { CommandPaletteState } from '../types/agent'
import { CommandPalette } from './CommandPalette'

/**
 * CommandPaletteContext - 全局命令面板状态管理
 *
 * 设计决策：
 * 1. 使用 React Context 而非全局状态库（如 Zustand/Redux），
 *    因为命令面板状态只涉及 isOpen/input/loading/error/result 几个字段，
 *    Context + useState 足够简洁，且无需引入新依赖。
 * 2. 键盘监听放在 Provider 内，确保无论焦点在哪都能响应 Cmd/Ctrl+K，
 *    同时阻止浏览器默认行为（如 Chrome 的 Ctrl+K 聚焦地址栏）。
 * 3. 提供 open/close/toggle 方法，让子组件可以程序化控制面板。
 */

interface CommandPaletteContextValue extends CommandPaletteState {
  open: () => void
  close: () => void
  toggle: () => void
  setInput: (value: string) => void
  setLoading: (value: boolean) => void
  setError: (value: string | null) => void
  setResult: (value: CommandPaletteState['result']) => void
  reset: () => void
}

const defaultState: CommandPaletteState = {
  isOpen: false,
  input: '',
  isLoading: false,
  error: null,
  result: null,
}

const CommandPaletteContext = createContext<CommandPaletteContextValue | undefined>(undefined)

export function useCommandPalette() {
  const ctx = useContext(CommandPaletteContext)
  if (!ctx) {
    throw new Error('useCommandPalette must be used within CommandPaletteProvider')
  }
  return ctx
}

interface Props {
  children: React.ReactNode
}

export function CommandPaletteProvider({ children }: Props) {
  const [state, setState] = useState<CommandPaletteState>(defaultState)

  const open = useCallback(() => {
    // 每次打开面板都重置为初始状态，确保快捷操作按钮和干净输入框重新出现
    setState({ ...defaultState, isOpen: true })
  }, [])

  const close = useCallback(() => {
    setState((s) => ({ ...s, isOpen: false }))
  }, [])

  const toggle = useCallback(() => {
    setState((s) => {
      const nextOpen = !s.isOpen
      if (nextOpen) {
        // 从关闭状态打开时同样重置，保证一致的体验
        return { ...defaultState, isOpen: true }
      }
      return { ...s, isOpen: false }
    })
  }, [])

  const reset = useCallback(() => {
    setState(defaultState)
  }, [])

  const setInput = useCallback((value: string) => {
    setState((s) => ({ ...s, input: value }))
  }, [])

  const setLoading = useCallback((value: boolean) => {
    setState((s) => ({ ...s, isLoading: value }))
  }, [])

  const setError = useCallback((value: string | null) => {
    setState((s) => ({ ...s, error: value }))
  }, [])

  const setResult = useCallback((value: CommandPaletteState['result']) => {
    setState((s) => ({ ...s, result: value }))
  }, [])

  // 全局键盘监听：Cmd/Ctrl+K 打开/关闭，ESC 关闭
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isModifier = e.metaKey || e.ctrlKey
      if (isModifier && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        toggle()
      }
      if (e.key === 'Escape') {
        close()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [toggle, close])

  const value: CommandPaletteContextValue = {
    ...state,
    open,
    close,
    toggle,
    setInput,
    setLoading,
    setError,
    setResult,
    reset,
  }

  return (
    <CommandPaletteContext.Provider value={value}>
      {children}
      {state.isOpen && <CommandPalette />}
    </CommandPaletteContext.Provider>
  )
}
