import React, { useRef, useCallback, useEffect, useMemo } from 'react';
import { Bubble, Sender, WelcomePrompts, CustomCardsProvider, Markdown } from '@agentscope-ai/chat';
import { ConfigProvider } from 'antd';
import { V2SessionProvider, useSessionsState, useSessions } from './contexts/SessionContext';
import { useChatFlow } from './hooks/useChatFlow';
import { v2SessionApi } from './sessionApi';
import ChatActionGroup from './components/ChatActionGroup';
import ChatHeaderTitle from './components/ChatHeaderTitle';
import MessageRenderer from './components/MessageRenderer';
import type { ChatMessage } from './types';
import './index.css';

// 提取文本内容的工具函数
function extractTextFromContent(content: any): string {
  if (!content) return '';
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    for (const c of content) {
      if (!c) continue;
      if (typeof c === 'string') return c;
      if (c.type === 'text' && c.text) return c.text;
      if (c.text) return c.text;
    }
  }
  return '';
}

// 自定义卡片组件：用户消息
const UserMessageCard = ({ data }: { data: { content: any } }) => {
  const text = extractTextFromContent(data.content);
  return <Markdown content={text} />;
};

// 自定义卡片组件：助手消息
const AssistantMessageCard = ({ data }: { data: { output: any } }) => {
  return <MessageRenderer output={data.output || []} />;
};

// 卡片配置
const cardConfig = {
  'UserMessage': UserMessageCard,
  'AssistantMessage': AssistantMessageCard,
};

const AIAssistantInner: React.FC = () => {
  const { currentSessionId } = useSessionsState();
  const { createSession } = useSessions();
  const listRef = useRef<any>(null);

  const {
    messages,
    loading,
    submit,
    cancel,
    switchSession,
  } = useChatFlow(currentSessionId);

  const connectionIdRef = useRef(0);
  const submittingRef = useRef(false);

  useEffect(() => {
    if (!currentSessionId) return;

    const connectionId = ++connectionIdRef.current;

    v2SessionApi.getSessionList().then((sessions) => {
      if (connectionId !== connectionIdRef.current) return;
      const session = sessions.find((s: any) => s.id === currentSessionId);
      if (session) {
        const msgs = (session._messages || session.messages || []);
        const converted = msgs.map((m: any) => {
          if (m.role === 'user') {
            let userContent = m.content;
            if (!userContent || (Array.isArray(userContent) && userContent.length === 0)) {
              userContent = m.cards?.[0]?.data?.input?.[0]?.content;
            }
            // Ensure content is always an array
            if (!Array.isArray(userContent)) {
              if (typeof userContent === 'string') {
                userContent = [{ type: 'text', text: userContent }];
              } else if (userContent) {
                userContent = [{ type: 'text', text: String(userContent) }];
              } else {
                userContent = [];
              }
            }
            return {
              id: m.id,
              role: 'user' as const,
              content: userContent,
              status: 'finished' as const,
              createdAt: m.createdAt || Date.now(),
            };
          }
          if (m.role === 'assistant') {
            let assistantResponse = m.response;
            if (!assistantResponse && m.cards?.[0]?.code === 'AgentScopeRuntimeResponseCard') {
              assistantResponse = m.cards[0].data;
            }
            return {
              id: m.id,
              role: 'assistant' as const,
              content: m.content || [],
              response: assistantResponse,
              status: (m.msgStatus || 'finished') as ChatMessage['status'],
              createdAt: m.createdAt || Date.now(),
            };
          }
          return null;
        }).filter(Boolean) as ChatMessage[];
        switchSession(currentSessionId, converted);
      }
    });
  }, [currentSessionId]);

  useEffect(() => {
    if (!currentSessionId) return;
    const timer = setTimeout(() => {
      v2SessionApi.saveSessionMessages(currentSessionId, messages);
    }, 500);
    return () => clearTimeout(timer);
  }, [messages, currentSessionId]);

  // 构建 Bubble.List 的 items
  const bubbleItems = useMemo(() => {
    return messages.map((msg) => {
      if (msg.role === 'user') {
        return {
          key: msg.id,
          id: msg.id,
          role: msg.role,
          cards: [
            {
              code: 'Text',
              data: {
                content: extractTextFromContent(msg.content)
              }
            }
          ],
          msgStatus: msg.status,
        };
      } else {
        // 助手消息使用 AssistantMessageCard 激活 MessageRenderer
        return {
          key: msg.id,
          id: msg.id,
          role: msg.role,
          cards: [
            {
              code: 'AssistantMessage',
              data: { output: msg.response?.output || [] }
            }
          ],
          msgStatus: msg.status,
        };
      }
    });
  }, [messages]);

  const handleSubmit = useCallback(async (text: string) => {
    if (submittingRef.current) return;
    submittingRef.current = true;
    try {
      if (!currentSessionId) {
        const newSid = await createSession({ name: text.slice(0, 20) });
        submit(text, undefined, newSid);
      } else {
        submit(text);
      }
    } finally {
      submittingRef.current = false;
    }
  }, [currentSessionId, createSession, submit]);

  const handleWelcomeClick = useCallback(async (query: string) => {
    if (submittingRef.current) return;
    submittingRef.current = true;
    try {
      if (!currentSessionId) {
        const newSid = await createSession({ name: query.slice(0, 20) });
        submit(query, undefined, newSid);
      } else {
        submit(query);
      }
    } finally {
      submittingRef.current = false;
    }
  }, [currentSessionId, createSession, submit]);

  const handlePasteFile = useCallback((file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const token = localStorage.getItem('token');
    fetch('/api/agent/upload', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    }).catch((e) => {
      console.error('File upload failed:', e);
    });
  }, []);

  return (
    <ConfigProvider getPopupContainer={() => document.querySelector('.fitagent-chat') as HTMLElement}>
      <CustomCardsProvider cardConfig={cardConfig}>
        <div className="fitagent-chat" style={{ touchAction: 'auto' }}>
          <div className="fitagent-chat-header">
            <ChatHeaderTitle />
            <ChatActionGroup />
          </div>

          <div className="fitagent-chat-body">
            {messages.length === 0 ? (
              <div className="fitagent-chat-welcome">
                <WelcomePrompts
                  greeting="你好，我是你的健身助手！"
                  description="我可以帮你制定训练计划、管理饮食、追踪健康数据。"
                  avatar="https://images.icon-icons.com/1429/PNG/96/icon-robots-3_98540.png"
                  prompts={[
                    { value: '帮我制定一个减脂训练计划' },
                    { value: '今天应该吃多少蛋白质？' },
                    { value: '如何提高跑步耐力？' },
                  ]}
                  onClick={handleWelcomeClick}
                />
              </div>
            ) : (
              <Bubble.List
                ref={listRef}
                items={bubbleItems}
                order="asc"
              />
            )}
          </div>

          <div className="fitagent-chat-sender">
            <Sender
              loading={loading}
              maxLength={10000}
              placeholder="输入消息..."
              onSubmit={handleSubmit}
              onCancel={cancel}
              onPasteFile={handlePasteFile}
            />
          </div>
        </div>
      </CustomCardsProvider>
    </ConfigProvider>
  );
};

const AIAssistant: React.FC = () => {
  return (
    <V2SessionProvider>
      <AIAssistantInner />
    </V2SessionProvider>
  );
};

export default AIAssistant;
