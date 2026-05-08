import {
  IAgentScopeRuntimeWebUISession,
  IAgentScopeRuntimeWebUISessionAPI,
} from '@agentscope-ai/chat'
import api from '../../../utils/request'

class SessionApi implements IAgentScopeRuntimeWebUISessionAPI {
  async getSessionList(): Promise<IAgentScopeRuntimeWebUISession[]> {
    const res = await api.get('/agent/sessions')
    return res as unknown as IAgentScopeRuntimeWebUISession[]
  }

  async getSession(sessionId: string): Promise<IAgentScopeRuntimeWebUISession> {
    const res = await api.get(`/agent/sessions/${sessionId}`)
    return res as unknown as IAgentScopeRuntimeWebUISession
  }

  async updateSession(session: Partial<IAgentScopeRuntimeWebUISession>): Promise<IAgentScopeRuntimeWebUISession[]> {
    const res = await api.put(`/agent/sessions/${session.id}`, { name: session.name })
    return res as unknown as IAgentScopeRuntimeWebUISession[]
  }

  async createSession(session: Partial<IAgentScopeRuntimeWebUISession>): Promise<IAgentScopeRuntimeWebUISession[]> {
    // 前端 SDK 生成的 session.id 必须传给后端，确保前后端 session_id 一致
    const res = await api.post('/agent/sessions', {
      id: session.id,
      name: session.name || '新对话',
    })
    return res as unknown as IAgentScopeRuntimeWebUISession[]
  }

  async removeSession(session: Partial<IAgentScopeRuntimeWebUISession>): Promise<IAgentScopeRuntimeWebUISession[]> {
    const res = await api.delete(`/agent/sessions/${session.id}`)
    return res as unknown as IAgentScopeRuntimeWebUISession[]
  }
}

export default new SessionApi()