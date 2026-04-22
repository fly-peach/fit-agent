import { fetchWithAuth } from "./client";
import { useAuthStore } from "../../store/auth";

type ApiWrap<T> = { code: number; message: string; data: T };
const API_BASE = "http://127.0.0.1:8000/api/v1";

export interface PendingActionItem {
  action_id: string;
  tool_name: string;
  summary: string;
  status: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface AgentMessageItem {
  role: "user" | "assistant";
  content: string;
  reasoning?: string;
  tool_uses?: { name: string; input: any; output: any }[];
  created_at: string;
}

export interface AgentChatData {
  session_id: string;
  response: string;
  pending_actions: PendingActionItem[];
  tool_events?: ToolEventItem[];
  memory_hits?: string[];
}

export interface AgentMessageInput {
  role: "user" | "assistant";
  content: string;
}

export interface ToolEventItem {
  event_id: string;
  tool_name: string;
  phase: "started" | "completed" | "failed";
  summary: string;
  payload_preview?: Record<string, unknown> | null;
  created_at: string;
}

export interface AgentAttachment {
  type: "image";
  base64: string;
  filename?: string;
  mime_type?: string;
}

export interface AgentSessionItem {
  session_id: string;
  title: string;
  updated_at: string;
}

export interface CompressionStatus {
  session_id: string;
  current_tokens: number;
  token_threshold: number;
  msg_threshold: number;
  compression_needed: boolean;
  last_event?: {
    strategy_level: number;
    strategy_name: string;
    messages_before: number;
    messages_after: number;
    tokens_before: number;
    tokens_after: number;
    compression_ratio: number;
    created_at?: string | null;
  } | null;
}

export interface CompressionEventItem {
  id: number;
  run_id: string;
  strategy_level: number;
  strategy_name: string;
  messages_before: number;
  messages_after: number;
  tokens_before: number;
  tokens_after: number;
  compression_ratio: number;
  affected_message_ids?: string | null;
  created_at: string;
}

export interface StreamEventPayload {
  type: string;
  [key: string]: unknown;
}

export async function chatWithAgent(
  message: string,
  sessionId?: string,
  attachments: AgentAttachment[] = []
): Promise<AgentChatData> {
  const resp = await fetchWithAuth("/agent/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId ?? null, attachments }),
  });
  const result = (await resp.json()) as ApiWrap<AgentChatData>;
  return result.data;
}

export async function getPendingActions(): Promise<PendingActionItem[]> {
  const resp = await fetchWithAuth("/agent/pending");
  const result = (await resp.json()) as ApiWrap<PendingActionItem[]>;
  return result.data;
}

export async function approveAction(
  actionId: string,
  decision: "approve" | "edit" | "reject",
  editedData?: Record<string, unknown>
): Promise<{ action_id: string; status: string; result: string }> {
  const resp = await fetchWithAuth("/agent/approve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action_id: actionId,
      decision,
      edited_data: editedData ?? null,
    }),
  });
  const result = (await resp.json()) as ApiWrap<{ action_id: string; status: string; result: string }>;
  return result.data;
}

export async function getAgentHistory(sessionId: string): Promise<AgentMessageItem[]> {
  const params = new URLSearchParams({ session_id: sessionId, format: "plain" });
  const resp = await fetchWithAuth(`/agent/history?${params.toString()}`);
  const result = (await resp.json()) as ApiWrap<AgentMessageItem[]>;
  return result.data;
}

export async function getAgentSessions(): Promise<AgentSessionItem[]> {
  const resp = await fetchWithAuth("/agent/sessions");
  const result = (await resp.json()) as ApiWrap<AgentSessionItem[]>;
  return result.data;
}

export async function deleteAgentSession(sessionId: string): Promise<boolean> {
  const resp = await fetchWithAuth(`/agent/sessions/${encodeURIComponent(sessionId)}`, {
    method: "DELETE",
  });
  const result = (await resp.json()) as ApiWrap<{ deleted: boolean }>;
  return result.data.deleted;
}

export async function getCompressionStatus(sessionId: string): Promise<CompressionStatus> {
  const params = new URLSearchParams({ session_id: sessionId });
  const resp = await fetchWithAuth(`/agent/compression/status?${params.toString()}`);
  const result = (await resp.json()) as ApiWrap<CompressionStatus>;
  return result.data;
}

export async function getCompressionEvents(sessionId: string, limit = 20): Promise<CompressionEventItem[]> {
  const params = new URLSearchParams({ session_id: sessionId, limit: String(limit) });
  const resp = await fetchWithAuth(`/agent/compression/events?${params.toString()}`);
  const result = (await resp.json()) as ApiWrap<CompressionEventItem[]>;
  return result.data;
}

export async function chatWithAgentStream(
  payload: { messages: AgentMessageInput[]; session_id?: string | null; attachments?: AgentAttachment[] },
  onEvent: (event: StreamEventPayload) => void,
): Promise<void> {
  const store = useAuthStore.getState();
  const requestBody = JSON.stringify({
    messages: payload.messages,
    session_id: payload.session_id ?? null,
    attachments: payload.attachments ?? [],
  });

  let token = store.accessToken;
  if (!token) {
    const refreshed = await store.refreshAccessToken();
    if (!refreshed) throw new Error("未登录或登录已过期");
    token = useAuthStore.getState().accessToken;
  }
  if (!token) throw new Error("未登录或登录已过期");

  try {
    await streamWithXHR(`${API_BASE}/agent/chat/stream`, token, requestBody, onEvent);
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    if (!msg.includes("HTTP 401")) {
      throw e;
    }
    const refreshed = await store.refreshAccessToken();
    if (!refreshed) {
      store.clearSession();
      throw new Error("登录已过期，请重新登录");
    }
    const nextToken = useAuthStore.getState().accessToken;
    if (!nextToken) throw new Error("登录已过期，请重新登录");
    await streamWithXHR(`${API_BASE}/agent/chat/stream`, nextToken, requestBody, onEvent);
  }
}

function streamWithXHR(
  url: string,
  token: string,
  requestBody: string,
  onEvent: (event: StreamEventPayload) => void,
): Promise<void> {
  return new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    let lastIndex = 0;
    let buffer = "";

    const flushResponseText = () => {
      const nextText = xhr.responseText.slice(lastIndex);
      if (!nextText) return;
      lastIndex = xhr.responseText.length;
      buffer += nextText;

      const blocks = buffer.split(/\r?\n\r?\n/);
      buffer = blocks.pop() ?? "";

      for (const block of blocks) {
        const lines = block.split(/\r?\n/);
        let eventName = "";
        const dataLines: string[] = [];

        for (const line of lines) {
          if (line.startsWith("event:")) {
            eventName = line.slice(6).trim();
          } else if (line.startsWith("data:")) {
            dataLines.push(line.slice(5).trim());
          }
        }

        const eventData = dataLines.join("\n");
        if (!eventData || eventData === "[DONE]") continue;

        try {
          const parsed = JSON.parse(eventData) as Record<string, unknown>;
          if (typeof parsed.type === "string") {
            onEvent(parsed as StreamEventPayload);
          } else {
            const mapped = mapLegacyEvent(eventName, parsed);
            if (mapped) onEvent(mapped);
          }
        } catch {
          onEvent({ type: "error", message: eventData });
        }
      }
    };

    xhr.open("POST", url, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    xhr.setRequestHeader("Accept", "text/event-stream");

    xhr.onprogress = () => {
      flushResponseText();
    };

    xhr.onload = () => {
      flushResponseText();
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
        return;
      }
      reject(new Error(`流式请求失败（HTTP ${xhr.status}）`));
    };

    xhr.onerror = () => {
      reject(new Error("网络请求失败"));
    };

    xhr.send(requestBody);
  });
}

function mapLegacyEvent(event: string, data: Record<string, unknown>): StreamEventPayload | null {
  if (event === "message_start") {
    return { type: "session", session_id: data.session_id };
  }
  if (event === "reasoning" || event === "thinking_delta") {
    return { type: "reasoning", delta: String(data.delta ?? data.text ?? "") };
  }
  if (event === "assistant_delta" || event === "content_delta") {
    return { type: "token", delta: String(data.delta ?? data.text ?? "") };
  }
  if (event === "tool_call" || event === "tool_event") {
    return {
      type: "tool_use",
      payload: {
        name: String(data.tool_name ?? "tool"),
        input: data.input_preview ?? null,
        output: data.output_preview ?? data.payload_preview ?? null,
      },
    };
  }
  if (event === "approval_required" || event === "pending_action") {
    return { type: "approval", payload: data };
  }
  if (event === "done" || event === "message_end") {
    return { type: "done", session_id: data.session_id, memory_hits: data.memory_hits };
  }
  if (event === "error") {
    return { type: "error", message: String(data.message ?? "流式响应异常中断") };
  }
  return null;
}
