import axios, { AxiosRequestConfig } from 'axios';
import { API_BASE_URL } from '../constants';
import { storage } from '../utils/storage';
import type { ChatMessage, ChatSession } from '../types';

const SESSIONS_KEY = 'fitagent-chat-sessions';

const chatApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
});

chatApi.interceptors.request.use(async (config) => {
  const token = await storage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const chatService = {
  async sendMessage(content: string, sessionId?: string): Promise<string> {
    const res = await chatApi.post('/agent/chat', {
      content,
      session_id: sessionId || 'default',
    });
    const { code, data, message } = res.data;
    if (code === 200 && data) {
      return data.response || data.content || data.message || JSON.stringify(data);
    }
    throw new Error(message || 'Chat request failed');
  },

  async sendMessageStream(
    content: string,
    sessionId: string,
    onChunk: (text: string) => void,
    onDone: () => void,
    onError: (err: Error) => void
  ): Promise<void> {
    try {
      const token = await storage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/agent/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ content, session_id: sessionId, stream: true }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        const data = await response.json();
        onChunk(data?.data?.response || data?.data?.content || '');
        onDone();
        return;
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || trimmed === 'data: [DONE]') continue;
          if (trimmed.startsWith('data: ')) {
            try {
              const parsed = JSON.parse(trimmed.slice(6));
              const text = parsed.content || parsed.text || parsed.delta || '';
              if (text) onChunk(text);
            } catch {
              onChunk(trimmed.slice(6));
            }
          }
        }
      }

      onDone();
    } catch (err) {
      onError(err instanceof Error ? err : new Error('Stream error'));
    }
  },

  // Session management (local storage)
  async getSessions(): Promise<ChatSession[]> {
    const raw = await storage.getItem(SESSIONS_KEY);
    return raw ? JSON.parse(raw) : [];
  },

  async saveSessions(sessions: ChatSession[]): Promise<void> {
    await storage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
  },

  async createSession(name?: string): Promise<ChatSession> {
    const sessions = await this.getSessions();
    const session: ChatSession = {
      id: Date.now().toString(),
      name: name || `会话 ${sessions.length + 1}`,
      messages: [],
      createdAt: new Date().toISOString(),
    };
    sessions.unshift(session);
    await this.saveSessions(sessions);
    return session;
  },

  async deleteSession(sessionId: string): Promise<void> {
    const sessions = await this.getSessions();
    const filtered = sessions.filter((s) => s.id !== sessionId);
    await this.saveSessions(filtered);
    // also tell server
    try {
      await chatApi.delete(`/agent/sessions/${sessionId}`);
    } catch {}
  },

  async addMessage(sessionId: string, message: ChatMessage): Promise<void> {
    const sessions = await this.getSessions();
    const session = sessions.find((s) => s.id === sessionId);
    if (session) {
      session.messages.push(message);
      await this.saveSessions(sessions);
    }
  },
};
