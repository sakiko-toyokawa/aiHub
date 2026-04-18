import client from './client'
import type { AgentParseResponse, AgentAskResponse } from '../types/agent'

/**
 * Agent API 封装
 *
 * 设计决策：
 * 1. 将 agent 相关 API 独立到 agent.ts，而不是全部塞进 client.ts，
 *    因为 agent 模块后续可能扩展更多路由（如对话历史、反馈等），
 *    独立文件可以避免 client.ts 过度膨胀。
 * 2. 仍然复用 axios 实例，确保 baseURL、headers、拦截器一致。
 */

export const agentApi = {
  parse: async (command: string): Promise<AgentParseResponse> => {
    const response = await client.post('/agent/parse', { command })
    return response.data
  },

  ask: async (question: string): Promise<AgentAskResponse> => {
    const response = await client.post('/agent/ask', { question })
    return response.data
  },
}
