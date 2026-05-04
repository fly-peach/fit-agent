import api from '../utils/request'

export interface Skill {
  name: string
  version: string
  description: string
  enabled: boolean
  path: string
  tags: string[]
  content?: string
}

export const skillApi = {
  list: (): Promise<Skill[]> => api.get('/agent/skills'),
  get: (name: string): Promise<Skill> => api.get(`/agent/skills/${name}`),
  enable: (name: string): Promise<{ status: string; name: string; enabled: boolean }> =>
    api.put(`/agent/skills/${name}/enable`),
  disable: (name: string): Promise<{ status: string; name: string; enabled: boolean }> =>
    api.put(`/agent/skills/${name}/disable`),
  upload: (file: File): Promise<{ status: string; name: string }> => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/agent/skills/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  delete: (name: string): Promise<{ status: string; name: string }> =>
    api.delete(`/agent/skills/${name}`),
}
