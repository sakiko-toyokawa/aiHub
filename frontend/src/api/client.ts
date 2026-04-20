import axios from 'axios'
import type { Summary, Source, Stats, Config, ProviderInfo, ModelInfo } from '../types'

const API_BASE_URL = '/api'

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Summaries API
export const summariesApi = {
  list: async (params?: {
    platform?: string
    is_read?: boolean
    is_favorited?: boolean
    is_archived?: boolean
    search?: string
    page?: number
    page_size?: number
  }): Promise<{ items: Summary[]; total: number; page: number; page_size: number }> => {
    const response = await client.get('/summaries/', { params })
    return response.data
  },

  get: async (id: number): Promise<Summary> => {
    const response = await client.get(`/summaries/${id}`)
    return response.data
  },

  markAsRead: async (id: number, progress?: number): Promise<{ status: string; is_read: boolean; read_progress: number }> => {
    const response = await client.post(`/summaries/${id}/read`, progress !== undefined ? { progress } : undefined)
    return response.data
  },

  toggleFavorite: async (id: number): Promise<{ is_favorited: boolean }> => {
    const response = await client.post(`/summaries/${id}/favorite`)
    return response.data
  },

  delete: async (id: number): Promise<{ status: string; message: string }> => {
    const response = await client.delete(`/summaries/${id}`)
    return response.data
  },

  cleanup: async (keep_count: number = 5): Promise<{
    status: string
    message: string
    deleted_summaries: number
    deleted_raw_contents: number
    remaining: number
  }> => {
    const response = await client.post(`/summaries/cleanup?keep_count=${keep_count}`)
    return response.data
  },

  updateNotes: async (id: number, notes: string): Promise<{ status: string; notes: string }> => {
    const response = await client.post(`/summaries/${id}/notes`, { notes })
    return response.data
  },

  getSimilar: async (id: number): Promise<{
    items: { id: number; title: string; platform: string; summary_text: string; tags: string[]; overlap_tags: string[]; created_at: string; is_read: boolean; is_favorited: boolean }[]
    total: number
  }> => {
    const response = await client.get(`/summaries/${id}/similar`)
    return response.data
  },

  search: async (q: string, page: number = 1, page_size: number = 20): Promise<{
    items: Summary[]
    total: number
    page: number
    page_size: number
  }> => {
    const response = await client.get('/summaries/search', {
      params: { q, page, page_size }
    })
    return response.data
  },

  archive: async (id: number): Promise<{ status: string; is_archived: boolean }> => {
    const response = await client.post(`/summaries/${id}/archive`)
    return response.data
  },

  unarchive: async (id: number): Promise<{ status: string; is_archived: boolean }> => {
    const response = await client.post(`/summaries/${id}/unarchive`)
    return response.data
  },

  permanentlyDelete: async (id: number): Promise<{ status: string; message: string }> => {
    const response = await client.delete(`/summaries/${id}/permanent`)
    return response.data
  },
}

// Sources API
export const sourcesApi = {
  list: async (): Promise<Source[]> => {
    const response = await client.get('/sources/')
    return response.data
  },

  get: async (id: number): Promise<Source> => {
    const response = await client.get(`/sources/${id}`)
    return response.data
  },

  create: async (data: Partial<Source>): Promise<Source> => {
    const response = await client.post('/sources/', data)
    return response.data
  },

  update: async (id: number, data: Partial<Source>): Promise<Source> => {
    const response = await client.put(`/sources/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await client.delete(`/sources/${id}`)
  },

  toggle: async (id: number): Promise<Source> => {
    const response = await client.post(`/sources/${id}/toggle`)
    return response.data
  },

  trigger: async (id: number): Promise<void> => {
    await client.post(`/sources/${id}/trigger`)
  },
}

// Stats API
export const statsApi = {
  get: async (): Promise<Stats> => {
    const response = await client.get('/stats/')
    return response.data
  },

  getTrendingTags: async (limit: number = 10): Promise<{ tags: string[]; total: number }> => {
    const response = await client.get('/stats/tags', { params: { limit } })
    return response.data
  },
}

// Crawler API
// 注意：/sources/crawl/trigger 是异步触发，后端立即返回 task_id，
// 而不是等待爬取完成后返回摘要数量。因此返回类型必须与后端保持一致。
export const crawlerApi = {
  trigger: async (): Promise<{
    status: string
    message: string
    task_id: string
    check_status_url: string
  }> => {
    const response = await client.post('/sources/crawl/trigger')
    return response.data
  },

  getTaskStatus: async (taskId: string): Promise<{
    task_id: string
    status: string
    started_at: string
    completed_at: string | null
    result: unknown
    error: string | null
  }> => {
    const response = await client.get(`/sources/crawl/task/${taskId}`)
    return response.data
  },

  listTasks: async (): Promise<{
    tasks: {
      task_id: string
      status: string
      started_at: string
      completed_at: string | null
      result: unknown
      error: string | null
    }[]
  }> => {
    const response = await client.get('/sources/crawl/tasks')
    return response.data
  },
}

// Config API
export const configApi = {
  get: async (): Promise<Config> => {
    const response = await client.get('/config/')
    return response.data
  },

  update: async (data: Partial<Config>): Promise<{ status: string; message: string }> => {
    const response = await client.put('/config/', data)
    return response.data
  },

  testEmail: async (): Promise<{ status: string; message: string }> => {
    const response = await client.post('/config/test-email')
    return response.data
  },

  // 新增：获取所有供应商及其模型列表
  getProviders: async (): Promise<ProviderInfo[]> => {
    const response = await client.get('/config/providers')
    return response.data
  },

  // 新增：获取指定供应商的模型列表
  getProviderModels: async (provider: string): Promise<ModelInfo[]> => {
    const response = await client.get(`/config/models/${provider}`)
    return response.data
  },
}

// Health check
export const healthApi = {
  check: async (): Promise<{ status: string }> => {
    const response = await client.get('/health')
    return response.data
  },
}

export default client
