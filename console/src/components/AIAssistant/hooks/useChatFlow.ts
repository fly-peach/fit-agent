import { useState, useCallback, useRef } from 'react';
import type { ChatMessage } from '../types';

interface UploadedAsset {
  url?: string;
  response?: {
    url?: string;
  };
  type?: string;
}

interface StreamEvent {
  object?: string;
  id?: string;
  type?: string;
  status?: string;
  role?: string;
  content?: any[];
  delta?: boolean;
  text?: string;
  data?: any;
  msg_id?: string;
  index?: number;
  code?: string;
  message?: string;
  output?: any[];
  error?: any;
}

/**
 * Accumulate SSE stream events into a response object with output messages.
 * Mirrors what AgentScopeRuntimeResponseBuilder does internally.
 */
function applyEvent(response: any, event: StreamEvent): any {
  if (!response.output) response.output = [];

  if (event.object === 'response') {
    Object.assign(response, event);
    return response;
  }

  if (event.object === 'message') {
    if (event.type === 'heartbeat') return response;
    const idx = response.output.findIndex((m: any) => m.id === event.id);
    if (idx >= 0) {
      const existingContent = response.output[idx].content;
      Object.assign(response.output[idx], event);
      if (!event.content || event.content.length === 0) {
        response.output[idx].content = existingContent;
      }
    } else {
      response.output.push({ ...event });
    }
    return response;
  }

  if (event.object === 'content') {
    const msg = response.output.find((m: any) => m.id === event.msg_id);
    if (!msg) return response;
    if (!msg.content) msg.content = [];

    if (event.delta) {
      const last = msg.content[msg.content.length - 1];
      if (last && last.delta && last.type === event.type) {
        if (event.type === 'text' && event.text != null) {
          last.text = (last.text || '') + event.text;
        } else if (event.type === 'data') {
          last.data = event.data;
        } else {
          Object.assign(last, event);
        }
      } else {
        msg.content.push({ ...event });
      }
    } else {
      if (msg.content.length > 0) {
        Object.assign(msg.content[msg.content.length - 1], event);
      } else {
        msg.content.push({ ...event });
      }
    }
    return response;
  }

  // Unknown object type — treat as error
  response.status = 'failed';
  response.output.push({
    status: 'failed',
    type: 'error',
    content: [],
    id: event.id || `err_${Date.now()}`,
    role: 'assistant',
    code: event.code,
    message: event.message || JSON.stringify(event),
  });
  return response;
}

export function useChatFlow(currentSessionId: string | undefined) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const submit = useCallback(async (text: string, files?: UploadedAsset[], sessionId?: string) => {
    const sid = sessionId || currentSessionId;
    if (!sid) return;

    const imageContents = (files || [])
      .filter((file) => String(file.type || '').startsWith('image/'))
      .map((file) => file.response?.url || file.url)
      .filter(Boolean)
      .map((url) => ({
        type: 'image',
        image_url: url,
        status: 'created',
      }));

    const userContents = [
      ...(text.trim() ? [{ type: 'text', text, status: 'created' }] : []),
      ...imageContents,
    ];

    if (userContents.length === 0) return;

    const userMsg: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: userContents,
      status: 'finished',
      createdAt: Date.now(),
    };

    const assistantMsgId = `msg_${Date.now() + 1}`;
    const assistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: [],
      response: { id: '', object: 'response', status: 'created', output: [], created_at: 0 },
      status: 'generating',
      createdAt: Date.now(),
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setLoading(true);

    const abortController = new AbortController();
    abortRef.current = abortController;

    // Accumulator for stream events
    let accResponse: any = { id: '', object: 'response', status: 'created', output: [], created_at: 0 };

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          Accept: 'text/event-stream',
        },
        body: JSON.stringify({
          input: [{ role: 'user', type: 'message', content: userContents }],
          session_id: sid,
          stream: true,
        }),
        signal: abortController.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(`Request failed: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let updated = false;
        for (const line of lines) {
          if (!line.startsWith('data:')) continue;
          const jsonStr = line.slice(5).trim();
          if (!jsonStr || jsonStr === '[DONE]') continue;

          try {
            const event = JSON.parse(jsonStr);
            accResponse = applyEvent(accResponse, event);
            updated = true;
          } catch {
            // ignore malformed JSON
          }
        }

        if (updated) {
          const snapshot = JSON.parse(JSON.stringify(accResponse));
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId
                ? { ...m, response: snapshot, status: 'generating' }
                : m
            )
          );
        }
      }

      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId ? { ...m, status: 'finished' } : m
        )
      );
    } catch (e: any) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId
            ? { ...m, status: e.name === 'AbortError' ? 'interrupted' : 'error' }
            : m
        )
      );
      throw e;
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  }, [currentSessionId]);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const switchSession = useCallback((_sessionId: string, loadedMessages?: ChatMessage[]) => {
    abortRef.current?.abort();
    setMessages(loadedMessages || []);
    setLoading(false);
  }, []);

  return { messages, loading, submit, cancel, switchSession };
}
