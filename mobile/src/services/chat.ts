import axios from 'axios';
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

/**
 * 解析 SSE 事件流，逐 chunk 回调。
 * 适用于 XHR onprogress 场景，responseText 会不断增长。
 */
function parseSSEStream(
  responseText: string,
  lastPosRef: { current: number },
  onChunk: (text: string) => void,
  onDone: () => void,
): boolean {
  const text = responseText;
  const lastPos = lastPosRef.current;

  // 只处理新增的部分
  const newChunk = text.slice(lastPos);
  if (!newChunk.trim()) {
    lastPosRef.current = text.length;
    return false; // 没有新数据
  }

  lastPosRef.current = text.length;

  let done = false;
  for (const line of newChunk.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || !trimmed.startsWith('data: ')) continue;

    try {
      const data = JSON.parse(trimmed.slice(6));

      // 增量文本块
      if (data.object === 'content' && data.type === 'text' && data.text) {
        onChunk(data.text);
      }

      // 完成信号
      if (data.object === 'message' && data.status === 'completed') {
        done = true;
      }

      // 错误信号
      if (data.error) {
        done = true;
      }
    } catch {
      // 不完整的 JSON，忽略
    }
  }

  if (done) {
    onDone();
  }

  return done;
}

/**
 * 构建 AgentRequest 格式的请求体
 */
function buildAgentRequestBody(content: string, sessionId: string, stream: boolean = true): string {
  return JSON.stringify({
    input: [{ id: `msg-${Date.now()}`, role: 'user', content: [{ type: 'text', text: content }] }],
    session_id: sessionId,
    stream,
  });
}

export const chatService = {
  /**
   * 非流式请求（fallback）。
   * 适用于 RN 环境不支持 XHR streaming 时的降级方案。
   */
  async sendMessage(content: string, sessionId?: string): Promise<string> {
    const sid = sessionId || 'default';
    const token = await storage.getItem('token');

    const response = await fetch('http://localhost:8000/process', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: buildAgentRequestBody(content, sid, false),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const text = await response.text();
    let lastMessage = '';
    for (const line of text.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed || !trimmed.startsWith('data: ')) continue;
      try {
        const data = JSON.parse(trimmed.slice(6));
        if (data.object === 'message' && data.status === 'completed' && Array.isArray(data.content)) {
          const lastContent = data.content[data.content.length - 1];
          if (lastContent?.text) {
            lastMessage = lastContent.text;
          }
        }
      } catch {
        // skip
      }
    }
    return lastMessage || '未收到有效回复';
  },

  /**
   * 流式请求，使用 XMLHttpRequest onprogress 实现真正的逐字接收。
   * 在 Expo 环境中有效，无需原生模块。
   */
  async sendMessageStream(
    content: string,
    sessionId: string,
    onChunk: (text: string) => void,
    onDone: () => void,
    onError: (err: Error) => void,
  ): Promise<void> {
    return new Promise<void>((resolve) => {
      const xhr = new XMLHttpRequest();
      const lastPos = { current: 0 };
      let completed = false;

      xhr.open('POST', 'http://localhost:8000/process', true);
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.timeout = 120000;

      // 设置 auth token
      storage.getItem('token').then((token) => {
        if (token) {
          xhr.setRequestHeader('Authorization', `Bearer ${token}`);
        }
      });

      xhr.onprogress = () => {
        if (completed) return;
        const done = parseSSEStream(
          xhr.responseText,
          lastPos,
          (text) => {
            onChunk(text);
          },
          () => {
            completed = true;
            onDone();
            resolve();
          },
        );
        if (done) {
          completed = true;
        }
      };

      xhr.onload = () => {
        if (completed) return;
        // 最终处理剩余数据
        parseSSEStream(
          xhr.responseText,
          lastPos,
          (text) => {
            onChunk(text);
          },
          () => {
            completed = true;
            onDone();
            resolve();
          },
        );
        if (!completed) {
          // 没有收到完成信号，视为完成
          completed = true;
          onDone();
          resolve();
        }
      };

      xhr.onerror = () => {
        onError(new Error('网络错误'));
        resolve();
      };

      xhr.ontimeout = () => {
        onError(new Error('请求超时'));
        resolve();
      };

      xhr.send(buildAgentRequestBody(content, sessionId, true));
    });
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
