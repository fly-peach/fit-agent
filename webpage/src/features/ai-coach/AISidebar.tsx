import { forwardRef, useEffect, useImperativeHandle, useMemo, useRef, useState } from "react";
import ChatModule, { Bubble } from "@chatui/core";
import "@chatui/core/dist/index.css";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  approveAction,
  chatWithAgentStream,
  deleteAgentSession,
  getAgentHistory,
  getAgentSessions,
  getCompressionStatus,
  getPendingActions,
  type CompressionStatus,
  type AgentSessionItem,
  type PendingActionItem,
  type AgentAttachment,
} from "../../shared/api/agent";

const Chat = (ChatModule as unknown as { default?: any }).default ?? (ChatModule as any);
const AGENT_NAME = "rogers";
const AGENT_AVATAR =
  "https://gw.alicdn.com/imgextra/i2/O1CN01fPEB9P1ylYWgaDuVR_!!6000000006619-0-tps-132-132.jpg";
const DEFAULT_QUICK_REPLIES = [
  { name: "帮我分析最近7天体重趋势", isHighlight: true },
  { name: "给我一份本周训练建议", isHighlight: true },
  { name: "我今天体重上升了，原因可能是什么" },
];
const INITIAL_MESSAGES: any[] = [];

const WELCOME_SUGGESTIONS = [
  { icon: "🏋️", text: "帮我分析最近7天体重趋势" },
  { icon: "📊", text: "给我一份本周训练建议" },
  { icon: "🍎", text: "我今天体重上升了，原因可能是什么" },
  { icon: "💪", text: "根据我的体成分生成一份增肌计划" },
];

interface ImageAttachment {
  id: string;
  preview: string;
  base64: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
}

interface AICoachSidebarProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  width: number;
  onResizeWidth: (width: number) => void;
}

export function AICoachSidebar({ open, onOpenChange, width, onResizeWidth }: AICoachSidebarProps) {
  const [activeTab, setActiveTab] = useState<"session" | "history">("session");
  const [sessionId, setSessionId] = useState<string>();

  const [typing, setTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingActions, setPendingActions] = useState<PendingActionItem[]>([]);
  const [sessions, setSessions] = useState<AgentSessionItem[]>([]);
  const [compressionStatus, setCompressionStatus] = useState<CompressionStatus | null>(null);
  const [messages, setMessages] = useState<any[]>(INITIAL_MESSAGES);
  const [attachments, setAttachments] = useState<ImageAttachment[]>([]);
  const handleStartXRef = useRef<number | null>(null);
  const handleStartOpenRef = useRef<boolean>(open);
  const handleStartWidthRef = useRef<number>(width);
  const handleModeRef = useRef<"idle" | "pending" | "resize">("idle");
  const queueRef = useRef<string[]>([]);
  const timerRef = useRef<number | null>(null);
  const currentAssistantRef = useRef<string | null>(null);
  const assistantTextRef = useRef("");
  const assistantReasoningRef = useRef("");
  const assistantToolUsesRef = useRef<any[]>([]);
  const assistantDoneRef = useRef(false);
  const assistantThinkTimeRef = useRef(0);
  const streamDoneRef = useRef(false);
  const thinkStartTimeRef = useRef(0);
  const requestSeqRef = useRef(0);
  const activeRequestRef = useRef<number | null>(null);
  const composerRef = useRef<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    getPendingActions()
      .then(setPendingActions)
      .catch(() => {});
    getAgentSessions()
      .then(setSessions)
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!sessionId) {
      setCompressionStatus(null);
      return;
    }
    getCompressionStatus(sessionId)
      .then(setCompressionStatus)
      .catch(() => {});
  }, [sessionId, messages.length]);

  const latestPendingAction = pendingActions[0] ?? null;

  const title = useMemo(() => (open ? "AI 教练" : "AI"), [open]);

  const startNewConversation = () => {
    setSessionId(undefined);
    setMessages(INITIAL_MESSAGES);
    setAttachments([]);
    queueRef.current = [];
    streamDoneRef.current = true;
    currentAssistantRef.current = null;
    assistantTextRef.current = "";
    assistantReasoningRef.current = "";
    assistantToolUsesRef.current = [];
    assistantDoneRef.current = false;
    assistantThinkTimeRef.current = 0;
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setTyping(false);
    setError(null);
    setActiveTab("session");
  };

  const onSwipeHandlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    handleStartXRef.current = e.clientX;
    handleStartOpenRef.current = open;
    handleStartWidthRef.current = width;
    handleModeRef.current = "pending";
  };

  useEffect(() => {
    const onMove = (e: PointerEvent) => {
      if (handleStartXRef.current == null) return;
      const rawDelta = e.clientX - handleStartXRef.current;
      const absDelta = Math.abs(rawDelta);
      if (handleModeRef.current === "pending" && absDelta > 10) {
        handleModeRef.current = "resize";
      }
      if (handleModeRef.current === "resize") {
        const widthDelta = handleStartXRef.current - e.clientX;
        onResizeWidth(handleStartWidthRef.current + widthDelta);
      }
    };
    const onUp = (e: PointerEvent) => {
      if (handleStartXRef.current == null) return;
      const delta = e.clientX - handleStartXRef.current;
      if (handleModeRef.current === "pending") {
        if (handleStartOpenRef.current && delta > 40) {
          onOpenChange(false);
        } else if (!handleStartOpenRef.current && delta < -40) {
          onOpenChange(true);
        } else if (Math.abs(delta) < 8) {
          onOpenChange(!handleStartOpenRef.current);
        }
      }
      handleStartXRef.current = null;
      handleModeRef.current = "idle";
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
  }, [onResizeWidth, onOpenChange]);

  const appendMsg = (msg: any): string => {
    const nextId = `msg_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`;
    const next = { ...msg, _id: nextId };
    setMessages((prev) => [...prev, next]);
    return nextId;
  };

  const updateMsg = (msgId: string, patch: any) => {
    // Keep message object identity stable during streaming updates so ChatUI
    // won't treat each token as a brand-new "last message" and auto-scroll.
    setMessages((prev) => {
      const idx = prev.findIndex((m) => m._id === msgId);
      if (idx < 0) return prev;
      const next = [...prev];
      const target: any = next[idx];
      if (patch.content && typeof patch.content === "object") {
        target.content = { ...(target.content ?? {}), ...patch.content };
      }
      for (const [k, v] of Object.entries(patch)) {
        if (k === "content") continue;
        target[k] = v;
      }
      return next;
    });
  };

  const toBackendMessages = (all: any[], latestUserText: string) => {
    const history = all
      .filter((m) => m.type === "text")
      .map((m) => ({
        role: (m.position === "right" ? "user" : "assistant") as "user" | "assistant",
        content: String(m.content?.text ?? ""),
      }))
      .filter((m) => m.content.trim());
    history.push({ role: "user", content: latestUserText });
    return history;
  };

  const flushTypewriter = () => {
    if (timerRef.current != null) return;
    timerRef.current = window.setInterval(() => {
      const next = queueRef.current.shift();
      if (!next) {
        if (streamDoneRef.current) {
          if (timerRef.current != null) {
            window.clearInterval(timerRef.current);
            timerRef.current = null;
          }
          setTyping(false);
          currentAssistantRef.current = null;
        }
        return;
      }
      const msgId = currentAssistantRef.current;
      if (!msgId) return;
      assistantTextRef.current += next;
      updateMsg(msgId, {
        type: "text",
        position: "left",
        content: {
          text: assistantTextRef.current,
          reasoning: assistantReasoningRef.current,
          toolUses: assistantToolUsesRef.current,
          isDone: assistantDoneRef.current,
          thinkTime: assistantThinkTimeRef.current,
        },
      });
    }, 16);
  };

  const updateReasoning = (delta: string) => {
    const msgId = currentAssistantRef.current;
    if (!msgId) return;
    assistantReasoningRef.current += delta;
    updateMsg(msgId, {
      type: "text",
      position: "left",
      content: {
        text: assistantTextRef.current,
        reasoning: assistantReasoningRef.current,
        toolUses: assistantToolUsesRef.current,
        isDone: assistantDoneRef.current,
        thinkTime: assistantThinkTimeRef.current,
      },
    });
  };

  const updateToolUses = (toolPayload: any) => {
    const msgId = currentAssistantRef.current;
    if (!msgId) return;
    const key = `${String(toolPayload?.name ?? "")}::${JSON.stringify(toolPayload?.input ?? {})}`;
    const current = [...assistantToolUsesRef.current];
    const idx = current.findIndex((x: any) => x?.__toolKey === key);
    const merged = { ...(idx >= 0 ? current[idx] : {}), ...toolPayload, __toolKey: key };
    if (idx >= 0) {
      current[idx] = merged;
    } else {
      current.push(merged);
    }
    // 创建新数组引用以确保 React 检测到变化
    assistantToolUsesRef.current = [...current];
    updateMsg(msgId, {
      type: "text",
      position: "left",
      content: {
        text: assistantTextRef.current,
        reasoning: assistantReasoningRef.current,
        toolUses: [...assistantToolUsesRef.current],  // 传递新数组
        isDone: assistantDoneRef.current,
        thinkTime: assistantThinkTimeRef.current,
      },
    });
  };

  const finalizeMessage = (msgId: string) => {
    const seconds = Math.floor((Date.now() - thinkStartTimeRef.current) / 1000);
    assistantDoneRef.current = true;
    assistantThinkTimeRef.current = seconds > 0 ? seconds : 1;
    updateMsg(msgId, {
      type: "text",
      position: "left",
      content: {
        text: assistantTextRef.current,
        reasoning: assistantReasoningRef.current,
        toolUses: assistantToolUsesRef.current,
        isDone: assistantDoneRef.current,
        thinkTime: assistantThinkTimeRef.current,
      },
    });
  };

  const handleStop = () => {
    queueRef.current = [];
    if (timerRef.current != null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setTyping(false);
    const msgId = currentAssistantRef.current;
    if (msgId) {
      finalizeMessage(msgId);
    }
    streamDoneRef.current = true;
    activeRequestRef.current = null;
    currentAssistantRef.current = null;
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const newAttachments: ImageAttachment[] = [];
    const maxFiles = 4;
    const maxSizeMB = 5;

    for (let i = 0; i < Math.min(files.length, maxFiles - attachments.length); i++) {
      const file = files[i];
      if (!file.type.startsWith("image/")) continue;
      if (file.size > maxSizeMB * 1024 * 1024) {
        setError(`图片 ${file.name} 超过 ${maxSizeMB}MB 限制`);
        continue;
      }

      const reader = new FileReader();
      reader.onload = (ev) => {
        const dataUrl = ev.target?.result as string;
        const base64 = dataUrl.split(",")[1];
        const att: ImageAttachment = {
          id: `img_${Date.now()}_${Math.random().toString(16).slice(2, 6)}`,
          preview: dataUrl,
          base64,
          filename: file.name,
          mime_type: file.type,
          size_bytes: file.size,
        };
        setAttachments((prev) => [...prev, att]);
      };
      reader.readAsDataURL(file);
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const removeAttachment = (id: string) => {
    setAttachments((prev) => prev.filter((a) => a.id !== id));
  };

  const triggerUpload = () => {
    fileInputRef.current?.click();
  };

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    const lineHeight = 22;
    const maxHeight = lineHeight * 6;
    const newHeight = Math.min(textarea.scrollHeight, maxHeight);
    textarea.style.height = `${newHeight}px`;
  };

  const handleSend = async (type: string, val: string) => {
    if (type !== "text") return;
    const hasText = val.trim().length > 0;
    const hasImages = attachments.length > 0;
    if (!hasText && !hasImages) return;
    if (currentAssistantRef.current && !streamDoneRef.current) {
      handleStop();
    }

    const requestId = ++requestSeqRef.current;
    activeRequestRef.current = requestId;
    streamDoneRef.current = false;
    queueRef.current = [];
    assistantTextRef.current = "";
    assistantReasoningRef.current = "";
    assistantToolUsesRef.current = [];
    assistantDoneRef.current = false;
    assistantThinkTimeRef.current = 0;
    setError(null);

    const userText = val.trim();
    const backendMessages = toBackendMessages(messages, userText || "请识别这张图片");

    const userMsgContent: any = { text: userText };
    if (attachments.length > 0) {
      userMsgContent.images = attachments.map((a) => a.preview);
    }

    appendMsg({
      type: "text",
      content: userMsgContent,
      position: "right",
    });

    const apiAttachments: AgentAttachment[] = attachments.map((a) => ({
      type: "image",
      base64: a.base64,
      filename: a.filename,
      mime_type: a.mime_type,
    }));

    setAttachments([]);

    const assistantId = appendMsg({
      type: "text",
      content: { text: "", reasoning: "", toolUses: [], isDone: false, thinkTime: 0 },
      position: "left",
    });

    currentAssistantRef.current = assistantId;
    thinkStartTimeRef.current = Date.now();
    setTyping(true);
    flushTypewriter();

    const markDone = () => {
      if (activeRequestRef.current !== requestId || currentAssistantRef.current !== assistantId) {
        return;
      }
      streamDoneRef.current = true;
      finalizeMessage(assistantId);
      activeRequestRef.current = null;
    };

    try {
      await chatWithAgentStream(
        { messages: backendMessages, session_id: sessionId ?? null, attachments: apiAttachments },
        (evt: any) => {
          if (activeRequestRef.current !== requestId || currentAssistantRef.current !== assistantId) return;
          const eventType = String(evt?.type ?? "");
          if (eventType === "token" && evt.delta) {
            queueRef.current.push(...String(evt.delta).split(""));
            flushTypewriter();
            return;
          }
          if (eventType === "reasoning" && evt.delta) {
            updateReasoning(String(evt.delta));
            return;
          }
          // tool_use 已整合到 reasoning 中，不再单独处理
          if (eventType === "tool_use" && evt.payload) {
            return;
          }
          if (eventType === "approval" && evt.payload?.action_id) {
            const approvalData = evt.payload as PendingActionItem;
            assistantTextRef.current += `\n\n我识别到你的数据修改请求：${approvalData.summary}。请确认是否执行？`;
            updateMsg(assistantId, {
              type: "text",
              position: "left",
              content: {
                text: assistantTextRef.current,
                reasoning: assistantReasoningRef.current,
                toolUses: assistantToolUsesRef.current,
                isDone: false,
                thinkTime: 0,
                pendingApproval: approvalData,
              },
            });
            setPendingActions((prev) => [approvalData, ...prev]);
            return;
          }
          if (eventType === "session" && typeof evt.session_id === "string") {
            setSessionId(evt.session_id);
            return;
          }
          if (eventType === "error") {
            setError(String(evt.message ?? "流式响应异常中断"));
            return;
          }
          if (eventType === "done") {
            markDone();
          }
        }
      );

      if (activeRequestRef.current === requestId && !streamDoneRef.current) {
        markDone();
      }
      const [nextPending, nextSessions] = await Promise.all([getPendingActions(), getAgentSessions()]);
      setPendingActions(nextPending);
      setSessions(nextSessions);
    } catch (e) {
      if (activeRequestRef.current !== requestId) return;
      if (!assistantTextRef.current) {
        assistantTextRef.current = `请求失败：${e instanceof Error ? e.message : "未知错误"}`;
      }
      finalizeMessage(assistantId);
      streamDoneRef.current = true;
      activeRequestRef.current = null;
      setError(e instanceof Error ? e.message : "发送失败");
    }
  };

  const onApprove = async (actionId: string, decision: "approve" | "reject") => {
    setError(null);
    try {
      const result = await approveAction(actionId, decision === "approve" ? "approve" : "reject");
      appendMsg({
        type: "text",
        position: "left",
        content: { text: `审批结果：${result.result}` },
      });
      const next = await getPendingActions();
      setPendingActions(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "审批失败");
    }
  };

  const handleInlineApproval = async (actionId: string, decision: "approve" | "reject", msgId: string) => {
    setError(null);
    try {
      const result = await approveAction(actionId, decision === "approve" ? "approve" : "reject");
      updateMsg(msgId, {
        content: {
          pendingApproval: undefined,
        },
      });
      const approvalText = decision === "approve" ? "✓ 已确认执行" : "✗ 已拒绝执行";
      appendMsg({
        type: "text",
        position: "left",
        content: { text: `${approvalText}\n\n执行结果：${result.result}` },
      });
      const next = await getPendingActions();
      setPendingActions(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "审批失败");
    }
  };

  const openHistorySession = async (targetSessionId: string) => {
    setError(null);
    try {
      const history = await getAgentHistory(targetSessionId);
      setSessionId(targetSessionId);
      setActiveTab("session");
      const mapped = history.map((h, idx) => ({
        _id: `history_${idx}`,
        type: "text",
        position: h.role === "user" ? "right" : "left",
        content:
          h.role === "user"
            ? { text: h.content }
            : {
                text: h.content,
                reasoning: h.reasoning || "",
                toolUses: h.tool_uses || [],
                isDone: true,
                thinkTime: 1,
              },
      }));
      setMessages(mapped.length ? mapped : INITIAL_MESSAGES);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载历史失败");
    }
  };

  const onDeleteHistorySession = async (targetSessionId: string) => {
    setError(null);
    try {
      const deleted = await deleteAgentSession(targetSessionId);
      if (!deleted) return;
      setSessions((prev) => prev.filter((s) => s.session_id !== targetSessionId));
      if (sessionId === targetSessionId) {
        setSessionId(undefined);
        setMessages(INITIAL_MESSAGES);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "删除会话失败");
    }
  };

  const prettyJson = (value: unknown) => {
    if (value === undefined) return "null";
    if (typeof value === "string") return value;
    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return String(value);
    }
  };

  function OperateCard({
    icon,
    title,
    children,
    isDone = false,
    autoCollapseOnDone = false,
    defaultExpanded = true,
  }: {
    icon: string;
    title: string;
    children: React.ReactNode;
    isDone?: boolean;
    autoCollapseOnDone?: boolean;
    defaultExpanded?: boolean;
  }) {
    const prevDoneRef = useRef(false);
    const [expanded, setExpanded] = useState(defaultExpanded);

    useEffect(() => {
      if (autoCollapseOnDone && isDone && !prevDoneRef.current) {
        setExpanded(false);
      }
      prevDoneRef.current = isDone;
    }, [isDone, autoCollapseOnDone]);

    return (
      <div className={`operate-card ${expanded ? "expanded" : "collapsed"}`}>
        <button type="button" className="operate-card-header" onClick={() => setExpanded((v) => !v)}>
          <div className="operate-card-title-wrap">
            <span className="operate-card-icon" aria-hidden="true">
              {icon}
            </span>
            <span className="operate-card-title">{title}</span>
          </div>
          <span className="operate-card-arrow" aria-hidden="true">
            {expanded ? "▴" : "▾"}
          </span>
        </button>
        <div
          className="operate-card-body"
          style={{
            maxHeight: expanded ? "none" : "0px",
            opacity: expanded ? 1 : 0,
            transition: expanded ? "opacity 0.18s ease" : "max-height 0.24s ease, opacity 0.2s ease",
          }}
        >
          <div className="operate-card-body-inner">
            {children}
          </div>
        </div>
      </div>
    );
  }

  const parseReasoningWithTools = (rawReasoning: string): {
    thinking: string;
    toolCalls: { name: string; input: string }[];
  } => {
    const toolRegex = /^\[工具调用\]\s+(\S+)\s*\n输入:\s*(.+)$/gm;
    const toolCalls: { name: string; input: string }[] = [];
    let match;
    while ((match = toolRegex.exec(rawReasoning)) !== null) {
      toolCalls.push({ name: match[1], input: match[2].trim() });
    }
    const thinking = rawReasoning.replace(toolRegex, "").replace(/\n{3,}/g, "\n\n").trim();
    return { thinking, toolCalls };
  };

  const renderMessageContent = (msg: any) => {
    const text = msg.content?.text || "";
    const reasoning = msg.content?.reasoning || "";
    const toolUses = msg.content?.toolUses || [];
    const isDone = msg.content?.isDone || false;
    const thinkTime = msg.content?.thinkTime || 0;
    const images = msg.content?.images || [];
    const pendingApproval = msg.content?.pendingApproval as PendingActionItem | undefined;
    const successfulToolUses = (() => {
      const seen = new Set<string>();
      const latest: any[] = [];
      for (let i = toolUses.length - 1; i >= 0; i -= 1) {
        const item = toolUses[i];
        if (!item?.name) continue;
        const k = `${String(item.name)}::${JSON.stringify(item.input ?? {})}`;
        if (seen.has(k)) continue;
        seen.add(k);
        latest.unshift(item);
      }
      return latest;
    })();

    const { thinking, toolCalls } = parseReasoningWithTools(reasoning);

    if (!reasoning && toolUses.length === 0 && images.length === 0 && !pendingApproval) {
      return (
        <div className="ai-markdown-bubble">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{text || "..."}</ReactMarkdown>
        </div>
      );
    }

    return (
      <div>
        {images.length > 0 ? (
          <div className="ai-message-images">
            {images.map((src: string, idx: number) => (
              <img key={idx} src={src} alt="用户图片" className="ai-message-image-thumb" />
            ))}
          </div>
        ) : null}
        {reasoning ? (
          <div className="agent-meta-stack">
            <div className="agent-meta-header">
              <img className="agent-meta-avatar" src={AGENT_AVATAR} alt={AGENT_NAME} />
              <span className="agent-meta-name">{AGENT_NAME}</span>
            </div>
            <OperateCard
              icon="🧠"
              title={isDone ? `Thinking（${thinkTime || 1}s）` : "Thinking"}
              isDone={isDone}
              autoCollapseOnDone
              defaultExpanded
            >
              {toolCalls.length > 0 && (
                <details className="tool-calls-expander" style={{ marginTop: "6px" }}>
                  <summary className="tool-calls-summary">
                    工具调用（{toolCalls.length}）
                  </summary>
                  <div className="tool-calls-list">
                    {toolCalls.map((tc, idx) => (
                      <div key={idx} className="tool-call-item">
                        <span className="tool-call-name">[{tc.name}]</span>
                        <span className="tool-call-input">输入: {tc.input}</span>
                      </div>
                    ))}
                  </div>
                </details>
              )}
              {thinking ? <div className="operate-thinking">{thinking}</div> : null}
            </OperateCard>
          </div>
        ) : null}
        {text ? (
          <div className="ai-markdown-bubble">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
            {pendingApproval ? (
              <div className="ai-inline-approval">
                <button
                  type="button"
                  className="ai-approval-btn approve"
                  onClick={() => void handleInlineApproval(pendingApproval.action_id, "approve", msg._id)}
                >
                  ✓ 确认执行
                </button>
                <button
                  type="button"
                  className="ai-approval-btn reject"
                  onClick={() => void handleInlineApproval(pendingApproval.action_id, "reject", msg._id)}
                >
                  ✗ 拒绝
                </button>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    );
  };

  const renderQuickReplies = () => (
    <div className="chat-header-extra">
      <div className="header-quick-replies">
        {typing ? (
          <button type="button" className="header-quick-btn stop-btn" onClick={handleStop}>
            停止输出 ⏹
          </button>
        ) : (
          DEFAULT_QUICK_REPLIES.map((item) => (
            <button
              key={item.name}
              type="button"
              className={`header-quick-btn ${item.isHighlight ? "active" : ""}`}
              onClick={() => {
                composerRef.current?.setText?.(item.name);
              }}
            >
              {item.name}
            </button>
          ))
        )}
      </div>
    </div>
  );

  const InlineThinkingComposer = forwardRef<any, any>((props, ref) => {
    const [localText, setLocalText] = useState(String(props.text ?? ""));
    const placeholder = String(props.placeholder ?? "请输入...");
    const isComposingRef = useRef(false);

    useImperativeHandle(
      ref,
      () => ({
        setText: (nextText: string) => {
          setLocalText(nextText);
          props.onChange?.(nextText);
        },
      }),
      [props.onChange]
    );

    useEffect(() => {
      const next = String(props.text ?? "");
      setLocalText(next);
    }, [props.text]);

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const next = e.target.value;
      setLocalText(next);
      props.onChange?.(next, e);
      adjustTextareaHeight();
    };

    const canSend = localText.trim().length > 0 || attachments.length > 0;
    const formatFileSize = (size: number) => {
      if (size < 1024) return `${size} B`;
      if (size < 1024 * 1024) return `${Math.round(size / 1024)} KB`;
      return `${(size / 1024 / 1024).toFixed(1)} MB`;
    };

    return (
      <div className="ai-composer-wrapper">
        <div className="ai-inline-composer">
          <div className="Composer ai-inline-composer-main">
            <div className="Composer-inputWrap">
              <div>
                {attachments.length > 0 ? (
                  <div className="ai-upload-list">
                    {attachments.map((att) => (
                      <div key={att.id} className="ai-upload-entry">
                        <img src={att.preview} alt={att.filename} className="ai-upload-entry-thumb" />
                        <div className="ai-upload-entry-meta">
                          <div className="ai-upload-entry-name" title={att.filename}>
                            {att.filename}
                          </div>
                          <div className="ai-upload-entry-size">{formatFileSize(att.size_bytes)}</div>
                        </div>
                        <button
                          type="button"
                          className="ai-upload-entry-remove"
                          onClick={() => removeAttachment(att.id)}
                          aria-label="删除图片"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                ) : null}
                <textarea
                  ref={textareaRef}
                  className="Input Input--outline Composer-input ai-autoresize-input"
                  placeholder={placeholder}
                  rows={1}
                  value={localText}
                  onChange={handleChange}
                  onCompositionStart={() => {
                    isComposingRef.current = true;
                  }}
                  onCompositionEnd={() => {
                    isComposingRef.current = false;
                  }}
                  onKeyDown={(e) => {
                    if (!isComposingRef.current && e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      props.onSend?.("text", localText);
                    }
                  }}
                  enterKeyHint="send"
                />
              </div>
            </div>
          </div>
          <div className="ai-inline-controls">
            <div className="ai-inline-left-actions">
              <button
                type="button"
                className="ai-upload-btn"
                onClick={triggerUpload}
                aria-label="上传图片"
                title="上传图片"
              >
                📎
              </button>
            </div>
            <button
              type="button"
              className="Composer-sendBtn ai-send-square-btn"
              onClick={() => props.onSend?.("text", localText)}
              disabled={!canSend}
              aria-label="发送"
            >
              ↑
            </button>
          </div>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          style={{ display: "none" }}
          onChange={handleFileSelect}
        />
      </div>
    );
  });

  return (
    <aside className={open ? "ai-sidebar" : "ai-sidebar collapsed"}>
      <div
        className="ai-swipe-handle"
        aria-label={open ? "向右收起" : "向左展开"}
        onPointerDown={onSwipeHandlePointerDown}
      >
        <span className="ai-swipe-arrow">{open ? "›" : "‹"}</span>
        {!open ? <span className="ai-swipe-text">展开AI</span> : null}
      </div>
      {open ? (
        <>
          <header className="ai-sidebar-header">
            <strong>{title}</strong>
            <div className="ai-header-tabs">
              <button className="ai-new-chat-btn" onClick={startNewConversation} type="button">
                新增对话
              </button>
              <button
                className={activeTab === "session" ? "ai-tab active" : "ai-tab"}
                onClick={() => setActiveTab("session")}
                type="button"
              >
                会话
              </button>
              <button
                className={activeTab === "history" ? "ai-tab active" : "ai-tab"}
                onClick={() => setActiveTab("history")}
                type="button"
              >
                历史对话
              </button>
            </div>
          </header>
          {activeTab === "session" ? (
            <>
              <div className="ai-chat-wrapper">
                {latestPendingAction ? (
                  <div className="ai-approval-shortcut">
                    <span className="ai-approval-shortcut-text">检测到待审批操作：{latestPendingAction.summary}</span>
                    <div className="ai-approval-shortcut-actions">
                      <button
                        type="button"
                        className="primary-mini"
                        onClick={() => void onApprove(latestPendingAction.action_id, "approve")}
                      >
                        确认审批
                      </button>
                      <button
                        type="button"
                        className="ghost-mini"
                        onClick={() => void onApprove(latestPendingAction.action_id, "reject")}
                      >
                        拒绝审批
                      </button>
                    </div>
                  </div>
                ) : null}
                {compressionStatus ? (
                  <div className="ai-compression-status">
                    <span className="ai-compression-title">记忆压缩</span>
                    <span className="ai-compression-meta">
                      Token {compressionStatus.current_tokens}/{compressionStatus.token_threshold}
                    </span>
                    <span className={compressionStatus.compression_needed ? "ai-compression-badge warn" : "ai-compression-badge ok"}>
                      {compressionStatus.compression_needed ? "建议压缩" : "正常"}
                    </span>
                  </div>
                ) : null}
                {messages.length === 0 ? (
                  <div className="ai-welcome-screen">
                    <div className="ai-welcome-greeting">
                      <span className="ai-welcome-avatar">🏃</span>
                      <h2>你好，我是 AI 教练</h2>
                      <p>问我关于健身、饮食、体成分分析的任何问题</p>
                    </div>
                    <div className="ai-welcome-suggestions">
                      {WELCOME_SUGGESTIONS.map((s, idx) => (
                        <button
                          key={idx}
                          type="button"
                          className="ai-welcome-suggestion-chip"
                          onClick={() => void handleSend("text", s.text)}
                        >
                          <span className="ai-welcome-chip-icon">{s.icon}</span>
                          <span>{s.text}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                ) : null}
                <Chat
                  navbar={null}
                  messages={messages}
                  onSend={handleSend}
                  placeholder="请输入..."
                  renderMessageContent={renderMessageContent}
                  renderQuickReplies={renderQuickReplies}
                  Composer={InlineThinkingComposer}
                  composerRef={composerRef}
                  isTyping={typing}
                />
                {error ? <p className="error-text">{error}</p> : null}
                <div className="ai-pending">
                  {pendingActions.map((a) => (
                    <article key={a.action_id} className="ai-pending-card">
                      <p>{a.summary}</p>
                      <div className="ai-pending-actions">
                        <button className="primary-mini" onClick={() => void onApprove(a.action_id, "approve")}>
                          确认
                        </button>
                        <button className="ghost-mini" onClick={() => void onApprove(a.action_id, "reject")}>
                          拒绝
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="ai-history-pane">
              {sessions.length === 0 ? <p className="muted-text">暂无历史会话</p> : null}
              {sessions.map((s) => (
                <article key={s.session_id} className={s.session_id === sessionId ? "ai-history-item active" : "ai-history-item"}>
                  <button className="ai-history-open" onClick={() => openHistorySession(s.session_id)} type="button">
                    <strong>{s.title || "AI 教练会话"}</strong>
                    <small>{new Date(s.updated_at).toLocaleString()}</small>
                  </button>
                  <button className="ai-history-delete" onClick={() => onDeleteHistorySession(s.session_id)} type="button">
                    删除
                  </button>
                </article>
              ))}
            </div>
          )}
        </>
      ) : null}
    </aside>
  );
}
