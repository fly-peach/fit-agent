import axios from 'axios';
import { API_BASE_URL } from '../constants';
import { storage } from '../utils/storage';
import type { ChatMessage, ChatSession } from '../types';

const PROCESS_URL = API_BASE_URL.replace('/api', '') + '/process';

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
 * 分别处理 reasoning（思考）和 message（回复）内容。
 * 通过 object:"response" + status:"completed" 判断流结束。
 */
function parseSSEStream(
  responseText: string,
  lastPosRef: { current: number },
  state: {
    responseMsgId: string | null,
    reasoningMsgId: string | null
  },
  onChunk: (text: string) => void,
  onReasoningChunk: (text: string) => void,
  onDone: () => void,
): boolean {
  const text = responseText;
  const lastPos = lastPosRef.current;

  const newChunk = text.slice(lastPos);
  if (!newChunk.trim()) {
    lastPosRef.current = text.length;
    return false;
  }

  lastPosRef.current = text.length;

  let done = false;
  for (const line of newChunk.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || !trimmed.startsWith('data: ')) continue;

    try {
      const data = JSON.parse(trimmed.slice(6));

      // 追踪消息类型和 ID - 处理不同可能的格式
      if (data.object === 'message') {
        if (data.type === 'reasoning' && data.id) {
          state.reasoningMsgId = data.id;
        } else if (data.type === 'message' && data.id) {
          state.responseMsgId = data.id;
        } else if (data.role === 'assistant' && data.id) {
          // 如果没有明确的 type，但 role 是 assistant，默认是回复消息
          state.responseMsgId = data.id;
        }
      }

      // 增量文本块
      if (
        data.object === 'content' &&
        data.type === 'text' &&
        data.delta === true &&
        data.text
      ) {
        // 判断是 reasoning 还是回复内容
        if (state.reasoningMsgId && data.msg_id === state.reasoningMsgId) {
          onReasoningChunk(data.text);
        } else if (state.responseMsgId && data.msg_id === state.responseMsgId) {
          onChunk(data.text);
        } else if (!state.reasoningMsgId && !state.responseMsgId) {
          // 如果还没有追踪到任何 msg_id，先假设是回复内容
          onChunk(data.text);
        }
      }

      // 直接检查 content 字段 - 兼容不同格式
      if (data.content && typeof data.content === 'string' && data.delta) {
        onChunk(data.content);
      }

      // 流结束信号
      if (data.object === 'response' && (data.status === 'completed' || data.status === 'failed')) {
        done = true;
      }
      if (data.status === 'completed' || data.status === 'failed') {
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

/**
 * 从 SSE 文本中提取最终回复和思考内容
 */
function extractFinalReply(sseText: string): { reply: string; reasoning: string } {
  let lastReply = '';
  let lastReasoning = '';
  for (const line of sseText.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || !trimmed.startsWith('data: ')) continue;
    try {
      const data = JSON.parse(trimmed.slice(6));
      // 处理完成的消息
      if (
        data.object === 'message' &&
        data.status === 'completed' &&
        Array.isArray(data.content)
      ) {
        let textContent = '';
        for (const c of data.content) {
          if (c.type === 'text' && c.text) {
            textContent = c.text;
          }
        }
        if (data.type === 'reasoning') {
          lastReasoning = textContent;
        } else {
          lastReply = textContent;
        }
      }
    } catch {
      // skip
    }
  }
  return { reply: lastReply, reasoning: lastReasoning };
}

export const chatService = {
  /**
   * 非流式请求（fallback）。
   */
  async sendMessage(content: string, sessionId?: string): Promise<{ reply: string; reasoning: string }> {
    const sid = sessionId || 'default';
    const token = await storage.getItem('token');

    const response = await fetch(PROCESS_URL, {
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
    const result = extractFinalReply(text);
    return result.reply ? result : { reply: '未收到有效回复', reasoning: '' };
  },

  /**
   * 流式请求，使用 XMLHttpRequest onprogress 实现逐字接收。
   */
  async sendMessageStream(
    content: string,
    sessionId: string,
    onChunk: (text: string) => void,
    onReasoningChunk: (text: string) => void,
    onDone: () => void,
    onError: (err: Error) => void,
  ): Promise<void> {
    const token = await storage.getItem('token');

    return new Promise<void>((resolve) => {
      const xhr = new XMLHttpRequest();
      const lastPos = { current: 0 };
      const state: {
        responseMsgId: string | null,
        reasoningMsgId: string | null
      } = {
        responseMsgId: null,
        reasoningMsgId: null
      };
      let completed = false;

      xhr.open('POST', PROCESS_URL, true);
      xhr.setRequestHeader('Content-Type', 'application/json');
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }
      xhr.timeout = 120000;

      xhr.onprogress = () => {
        if (completed) return;
        const done = parseSSEStream(
          xhr.responseText,
          lastPos,
          state,
          onChunk,
          onReasoningChunk,
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
        parseSSEStream(
          xhr.responseText,
          lastPos,
          state,
          onChunk,
          onReasoningChunk,
          () => {
            completed = true;
            onDone();
            resolve();
          },
        );
        if (!completed) {
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
