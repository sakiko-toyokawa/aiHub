import { useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import type { AgentAction, AgentExecutionResult } from '../types/agent'
import { summariesApi, crawlerApi, sourcesApi, statsApi, configApi } from '../api/client'

/**
 * useAgentExecutor - Agent Action 执行器
 *
 * 设计决策：
 * 1. 使用 TanStack Query 的 queryClient.invalidateQueries 来刷新相关列表，
 *    而不是手动维护本地状态，确保 Dashboard / Sidebar 等组件自动同步。
 * 2. 返回统一的 AgentExecutionResult，让 CommandPalette 只需要处理一种结果格式，
 *    简化 UI 层的错误展示和成功提示。
 * 3. 阶段0先搭建框架，switch 中只填充少数立即能验证的 case，
 *    后续阶段逐步填充，避免一次性写大量无法运行的死代码。
 */
export function useAgentExecutor() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const execute = useCallback(async (action: AgentAction): Promise<AgentExecutionResult> => {
    try {
      switch (action.type) {
        case 'navigate': {
          const path = String(action.params?.path || '/')
          navigate(path)
          return { success: true, message: '页面跳转中...' }
        }

        case 'list_summaries': {
          // 在命令面板内展示摘要列表，而不是跳转到 Dashboard
          const platform = action.params?.platform as string | undefined
          const page = Number(action.params?.page ?? 1)
          const pageSize = Number(action.params?.page_size ?? 10)
          const result = await summariesApi.list({
            platform,
            page,
            page_size: pageSize,
          })
          return {
            success: true,
            message: `找到 ${result.total} 条摘要${platform ? `（${platform}）` : ''}`,
            data: result.items,
          }
        }

        case 'mark_read': {
          // 支持通过 summary_id 标记已读，summary_id 为 'latest' 时自动查询最新摘要
          let summaryId: number | undefined
          if (action.params?.summary_id === 'latest') {
            const listResult = await summariesApi.list({ page: 1, page_size: 1 })
            if (!listResult.items.length) {
              return { success: false, message: '暂无摘要可供标记' }
            }
            summaryId = listResult.items[0].id
          } else {
            summaryId = Number(action.params?.summary_id)
          }
          if (!summaryId || isNaN(summaryId)) {
            return { success: false, message: '缺少有效的摘要 ID' }
          }
          await summariesApi.markAsRead(summaryId)
          queryClient.invalidateQueries({ queryKey: ['summaries'] })
          queryClient.invalidateQueries({ queryKey: ['stats'] })
          return { success: true, message: `摘要 #${summaryId} 已标记为已读` }
        }

        case 'toggle_favorite': {
          const summaryId = Number(action.params?.summary_id)
          if (!summaryId || isNaN(summaryId)) {
            return { success: false, message: '缺少有效的摘要 ID' }
          }
          const result = await summariesApi.toggleFavorite(summaryId)
          queryClient.invalidateQueries({ queryKey: ['summaries'] })
          queryClient.invalidateQueries({ queryKey: ['stats'] })
          const verb = result.is_favorited ? '收藏' : '取消收藏'
          return { success: true, message: `摘要 #${summaryId} 已${verb}` }
        }

        case 'delete_summary': {
          const summaryId = Number(action.params?.summary_id)
          if (!summaryId || isNaN(summaryId)) {
            return { success: false, message: '缺少有效的摘要 ID' }
          }
          await summariesApi.delete(summaryId)
          queryClient.invalidateQueries({ queryKey: ['summaries'] })
          queryClient.invalidateQueries({ queryKey: ['stats'] })
          return { success: true, message: `摘要 #${summaryId} 已删除` }
        }

        case 'cleanup': {
          const keepCount = Number(action.params?.keep_count ?? 5)
          const result = await summariesApi.cleanup(keepCount)
          queryClient.invalidateQueries({ queryKey: ['summaries'] })
          queryClient.invalidateQueries({ queryKey: ['stats'] })
          return {
            success: true,
            message: `清理完成，删除了 ${result.deleted_summaries} 条摘要，剩余 ${result.remaining} 条`,
            data: result,
          }
        }

        case 'get_summary': {
          const summaryId = Number(action.params?.summary_id)
          if (!summaryId || isNaN(summaryId)) {
            return { success: false, message: '缺少有效的摘要 ID' }
          }
          navigate(`/summary/${summaryId}`)
          return { success: true, message: '已跳转到摘要详情' }
        }

        // 阶段2：爬虫与任务功能
        case 'trigger_crawl': {
          const result = await crawlerApi.trigger()
          return {
            success: true,
            message: `后台任务已启动，任务 ID：${result.task_id}，稍后可在 Dashboard 查看更新`,
            data: result,
          }
        }

        case 'get_crawl_status': {
          const taskId = String(action.params?.task_id || '')
          if (!taskId) {
            return { success: false, message: '缺少任务 ID，请输入类似"查看抓取任务状态 xxx"的指令' }
          }
          const task = await crawlerApi.getTaskStatus(taskId)
          const lines = [
            `任务 ${task.task_id} 状态：${task.status}`,
            `开始时间：${new Date(task.started_at).toLocaleString('zh-CN')}`,
          ]
          if (task.completed_at) {
            lines.push(`完成时间：${new Date(task.completed_at).toLocaleString('zh-CN')}`)
          }
          if (task.error) {
            lines.push(`错误：${task.error}`)
          } else if (task.result) {
            lines.push(`结果：${JSON.stringify(task.result)}`)
          }
          return {
            success: true,
            message: lines.join('\n'),
            data: task,
          }
        }

        case 'list_tasks': {
          const result = await crawlerApi.listTasks()
          if (result.tasks.length === 0) {
            return { success: true, message: '暂无爬虫任务' }
          }
          const lines = result.tasks.map((t) => {
            const started = new Date(t.started_at).toLocaleString('zh-CN')
            return `${t.task_id} | ${t.status} | ${started}`
          })
          return {
            success: true,
            message: `共 ${result.tasks.length} 个任务：\n${lines.join('\n')}`,
            // 不返回 data 数组，避免 CommandPalette 的 Summary 列表渲染误匹配
          }
        }

        // 阶段3：数据源管理功能
        case 'list_sources': {
          const sources = await sourcesApi.list()
          if (sources.length === 0) {
            return { success: true, message: '暂无数据源' }
          }
          const lines = sources.map((s) => {
            const status = s.is_active ? '启用' : '暂停'
            return `#${s.id} | ${s.platform} | ${s.name} | ${status}`
          })
          return {
            success: true,
            message: `共 ${sources.length} 个数据源：\n${lines.join('\n')}`,
          }
        }

        case 'toggle_source_active': {
          // 支持通过数字 ID 或平台名称（如"知乎"）切换数据源状态
          const raw = action.params?.source_id
          let sourceId: number | undefined

          if (typeof raw === 'number') {
            sourceId = raw
          } else if (typeof raw === 'string' && /^\d+$/.test(raw)) {
            sourceId = Number(raw)
          } else if (typeof raw === 'string') {
            const sources = await sourcesApi.list()
            const matched = sources.find(
              (s) =>
                s.platform.toLowerCase() === raw.toLowerCase() ||
                s.name.toLowerCase() === raw.toLowerCase()
            )
            if (!matched) {
              return {
                success: false,
                message: `未找到名为"${raw}"的数据源，请确认名称或提供数字 ID`,
              }
            }
            sourceId = matched.id
          }

          if (!sourceId || isNaN(sourceId)) {
            return {
              success: false,
              message: '未能识别要操作的数据源，请尝试说"暂停知乎数据源"或提供数字 ID',
            }
          }

          const result = await sourcesApi.toggle(sourceId)
          queryClient.invalidateQueries({ queryKey: ['sources'] })
          queryClient.invalidateQueries({ queryKey: ['stats'] })
          const statusText = result.is_active ? '启用' : '暂停'
          return { success: true, message: `数据源 #${sourceId} 已${statusText}` }
        }

        // 阶段4：统计与洞察功能
        case 'get_stats': {
          const stats = await statsApi.get()
          const platformLines = stats.platforms.map(
            (p) => `  ${p.platform}: ${p.summary_count} 摘要 / ${p.content_count} 原始内容`
          )
          const lines = [
            `📊 统计概览`,
            `总摘要数：${stats.total_summaries}`,
            `已读数：${stats.read_count}`,
            `收藏数：${stats.favorite_count}`,
            `数据源：${stats.active_sources} 启用 / ${stats.total_sources} 总计`,
            `原始内容：${stats.total_raw_contents}`,
            `平台分布：`,
            ...platformLines,
          ]
          return {
            success: true,
            message: lines.join('\n'),
            data: stats,
          }
        }

        case 'get_trending_tags': {
          const limit = Number(action.params?.limit ?? 10)
          const result = await statsApi.getTrendingTags(limit)
          if (result.tags.length === 0) {
            return { success: true, message: '暂无热门标签' }
          }
          const lines = [
            `🔥 热门标签（前 ${result.tags.length} / 共 ${result.total} 个）`,
            ...result.tags.map((tag, idx) => `${idx + 1}. ${tag}`),
          ]
          return {
            success: true,
            message: lines.join('\n'),
            data: result,
          }
        }

        // 阶段5：系统配置功能
        case 'get_config': {
          const config = await configApi.get()
          const lines = [
            `⚙️ 当前配置`,
            `默认 AI 提供商：${config.default_ai_provider}`,
            `默认 AI 模型：${config.default_ai_model}`,
            `邮件通知：${config.email_enabled ? '开启' : '关闭'}`,
            `SMTP 服务器：${config.smtp_host || '未配置'}`,
            `收件邮箱：${config.email_to || '未配置'}`,
            `抓取计划：${config.crawl_schedule}`,
            `总结计划：${config.summarize_schedule}`,
            `邮件计划：${config.email_schedule}`,
            `时区：${config.timezone}`,
            `日志级别：${config.log_level}`,
          ]
          return {
            success: true,
            message: lines.join('\n'),
            data: config,
          }
        }

        case 'update_config': {
          const key = String(action.params?.key || '')
          const value = action.params?.value
          if (!key) {
            return { success: false, message: '缺少配置项 key，例如"更新默认模型为 deepseek:deepseek-chat"' }
          }
          const result = await configApi.update({ [key]: value })
          queryClient.invalidateQueries({ queryKey: ['config'] })
          return {
            success: true,
            message: result.message,
            data: result,
          }
        }

        case 'test_email': {
          const result = await configApi.testEmail()
          return {
            success: true,
            message: result.message,
            data: result,
          }
        }

        case 'get_providers': {
          const providers = await configApi.getProviders()
          if (providers.length === 0) {
            return { success: true, message: '暂无 AI 提供商信息' }
          }
          const lines = providers.map((p) => {
            const modelNames = p.models.map((m) => m.name).join(', ')
            return `${p.name} (${p.id}) — 默认模型：${p.default_model}\n  可用模型：${modelNames}`
          })
          return {
            success: true,
            message: `共 ${providers.length} 个提供商：\n${lines.join('\n')}`,
          }
        }

        case 'get_provider_models': {
          const provider = String(action.params?.provider || '')
          if (!provider) {
            return { success: false, message: '缺少提供商名称，例如"查看 DeepSeek 有哪些模型"' }
          }
          const models = await configApi.getProviderModels(provider)
          if (models.length === 0) {
            return { success: true, message: `提供商 ${provider} 暂无模型信息` }
          }
          const lines = models.map((m) => `${m.name} (${m.id}) — ${m.description}`)
          return {
            success: true,
            message: `${provider} 的模型列表：\n${lines.join('\n')}`,
            data: models,
          }
        }

        case 'unknown':
        default:
          return { success: false, message: action.message || '未能理解该指令，请尝试其他说法' }
      }
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '执行失败，请稍后重试'
      return { success: false, message }
    }
  }, [queryClient, navigate])

  return { execute }
}
