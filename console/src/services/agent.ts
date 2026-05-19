import api from '../utils/request'

export interface ApiKeyStatus {
  has_api_key: boolean
  expires_at?: string
}

export const agentApi = {
  getApiKeyStatus: (): Promise<ApiKeyStatus> =>
    api.get('/agent/api-key/status'),

  setApiKey: (apiKey: string): Promise<void> =>
    api.post('/agent/api-key', { api_key: apiKey }),

  deleteApiKey: (): Promise<void> =>
    api.delete('/agent/api-key'),

  uploadFile: (file: File): Promise<{ url: string }> => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/agent/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}
