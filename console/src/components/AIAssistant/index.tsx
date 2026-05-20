import React, { useRef, useCallback, useEffect, useMemo, useState } from 'react';
import { Bubble, Sender, WelcomePrompts, CustomCardsProvider, Markdown, Attachments } from '@agentscope-ai/chat';
import { App, ConfigProvider, Upload } from 'antd';
import type { UploadFile, UploadProps } from 'antd';
import type { UploadRequestOption as RcCustomRequestOptions } from 'rc-upload/lib/interface';
import { PaperClipOutlined } from '@ant-design/icons';
import { V2SessionProvider, useSessionsState, useSessions } from './contexts/SessionContext';
import { useChatFlow } from './hooks/useChatFlow';
import { v2SessionApi } from './sessionApi';
import { trainingResultsApi } from '../../services/training';
import { agentApi } from '../../services/agent';
import ChatActionGroup from './components/ChatActionGroup';
import ChatHeaderTitle from './components/ChatHeaderTitle';
import MessageRenderer from './components/MessageRenderer';
import type { ChatMessage } from './types';
import {
  START_CARD_GENERATION_EVENT,
  type CardGenerationRequestDetail,
  emitCardResultFailed,
  emitCardResultSaved,
} from './bridge';
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

function extractImagesFromContent(content: any): Array<{ url: string }> {
  if (!Array.isArray(content)) return [];
  return content
    .filter((item) => item?.type === 'image' && item.image_url)
    .map((item) => ({ url: item.image_url }));
}

function buildUserCards(content: any) {
  const text = extractTextFromContent(content);
  const images = extractImagesFromContent(content);
  const cards: any[] = [];

  if (text) {
    cards.push({
      code: 'Text',
      data: { content: text },
    });
  }

  if (images.length) {
    cards.push({
      code: 'Images',
      data: images,
    });
  }

  return cards;
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

function normalizeMessageStatus(status?: string): ChatMessage['status'] {
  if (status === 'loading') return 'generating';
  if (status === 'cancelled') return 'interrupted';
  if (status === 'finished' || status === 'error' || status === 'generating' || status === 'interrupted') {
    return status;
  }
  return 'finished';
}

const AIAssistantInner: React.FC = () => {
  const { message } = App.useApp();
  const { currentSessionId, setCurrentSessionId, pendingApproval } = useSessionsState();
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
  const newSessionIdRef = useRef<string | undefined>(undefined);
  const skipNextSessionLoadRef = useRef(false);
  const [inputValue, setInputValue] = useState('');
  const [attachedFiles, setAttachedFiles] = useState<UploadFile[]>([]);

  const hasUploadingFiles = attachedFiles.some((file) => file.status === 'uploading');
  const canSubmitWithAttachments = attachedFiles.some((file) => (file.response as any)?.url || file.url);

  useEffect(() => {
    if (!currentSessionId) return;

    // 跳过新建 session 的加载，避免空数据覆盖刚提交的消息
    if (skipNextSessionLoadRef.current) {
      skipNextSessionLoadRef.current = false;
      return;
    }
    if (newSessionIdRef.current === currentSessionId) {
      newSessionIdRef.current = undefined;
      return;
    }

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
              status: normalizeMessageStatus(m.msgStatus),
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
        const cards = buildUserCards(msg.content);
        return {
          key: msg.id,
          id: msg.id,
          role: msg.role,
          cards,
          msgStatus: 'finished' as const,
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
          msgStatus: normalizeMessageStatus(msg.status),
        };
      }
    });
  }, [messages]);

  const handleSubmit = useCallback(async (text: string) => {
    if (submittingRef.current) return;
    if (hasUploadingFiles) {
      message.info('图片上传中，请稍候再发送');
      return;
    }
    submittingRef.current = true;
    
    const currentText = text;
    const currentFiles = attachedFiles;
    
    // 提前清空输入框和附件，提升交互体验
    setInputValue('');
    setAttachedFiles([]);

    try {
      if (!currentSessionId) {
        skipNextSessionLoadRef.current = true;
        const newSid = await createSession({ name: currentText.slice(0, 20) });
        newSessionIdRef.current = newSid;
        await submit(currentText, currentFiles, newSid);
      } else {
        await submit(currentText, currentFiles);
      }
    } finally {
      submittingRef.current = false;
    }
  }, [attachedFiles, currentSessionId, createSession, hasUploadingFiles, message, submit]);

  const handleWelcomeClick = useCallback(async (query: string) => {
    if (submittingRef.current) return;
    submittingRef.current = true;
    try {
      if (!currentSessionId) {
        skipNextSessionLoadRef.current = true;
        const newSid = await createSession({ name: query.slice(0, 20) });
        newSessionIdRef.current = newSid;
        submit(query, undefined, newSid);
      } else {
        submit(query);
      }
      setInputValue('');
    } finally {
      submittingRef.current = false;
    }
  }, [currentSessionId, createSession, submit]);

  useEffect(() => {
    const handleExternalCardGeneration = async (event: Event) => {
      const customEvent = event as CustomEvent<CardGenerationRequestDetail>;
      const detail = customEvent.detail;
      if (!detail || detail.source !== 'training-results-card') return;
      if (submittingRef.current) return;

      submittingRef.current = true;
      let sessionId: string | undefined;

      try {
        skipNextSessionLoadRef.current = true;
        sessionId = await createSession({ name: detail.title.slice(0, 20) || '训练成果卡片' });
        newSessionIdRef.current = sessionId;
        setCurrentSessionId(sessionId);

        const enhancedPrompt = [
          detail.promptText,
          '',
          '【卡片生成上下文】',
          `- 来源: ${detail.source}`,
          `- 结果模板: ${detail.templateKey}`,
          detail.styleTemplateKey ? `- 样式模板: ${detail.styleTemplateKey}` : '',
          `- 标题: ${detail.title}`,
          detail.periodType ? `- 周期类型: ${detail.periodType}` : '',
          detail.periodStart ? `- 周期开始: ${detail.periodStart}` : '',
          detail.periodEnd ? `- 周期结束: ${detail.periodEnd}` : '',
          `- 归档会话ID: ${sessionId}`,
          detail.styleTemplateSummary ? `- 样式说明: ${detail.styleTemplateSummary}` : '',
          detail.styleTemplatePromptHint ? `- 模板提示: ${detail.styleTemplatePromptHint}` : '',
          detail.styleTemplateHighlights?.length ? `- 风格重点: ${detail.styleTemplateHighlights.join(' / ')}` : '',
          '',
          detail.styleTemplatePreviewHtml ? '【模板预览 HTML】' : '',
          detail.styleTemplatePreviewHtml || '',
          '',
          '【执行要求】',
          '- `agent-card-results` 和 `training-card` 是技能说明，不是可直接调用的函数名；不要把它们当成 tool name。',
          '- 你只能使用现有工具 `execute_fitme_command` / `wrapped_execute_fitme_command` 读取数据或归档结果。',
          '- 如果存在样式模板 key，先使用 `get-training-card-template --template-key "<样式模板key>"` 读取数据库中的模板样例。',
          '- 读取训练数据时，优先使用真实存在的子命令，如 `get-training-stats`、`get-training-weekly`、`get-training-recommendations`。',
          '- 不要调用不存在的命令，例如 `generate-training-report`。',
          '- 生成完成后，必须调用 `save-training-result` 子命令归档到后端。',
          detail.styleTemplateKey
            ? `- 归档时请将 template_key 设置为当前样式模板 key：${detail.styleTemplateKey}。`
            : '- 归档时请将 template_key 设置为本次使用的样式模板 key。',
          '- 调用 `execute_fitme_command` 时，`command` 参数优先直接传子命令形式，例如：`save-training-result --title "标题" --session-id "会话ID" ...`。',
          '- 如果你传完整命令字符串，也必须确保子命令真实存在，且最终归档时必须带上上面的归档会话ID、标题、周期信息、stats_json 和 card_html。',
        ].filter(Boolean).join('\n');

        await submit(enhancedPrompt, undefined, sessionId);

        const snapshots = await trainingResultsApi.listResults({
          sessionId,
          limit: 1,
          offset: 0,
        });

        const latest = snapshots[0];
        if (latest) {
          emitCardResultSaved({
            source: 'training-results-card',
            sessionId,
            snapshotId: latest.id,
            title: latest.title,
            templateKey: latest.templateKey || detail.templateKey,
            periodType: latest.periodType,
            periodStart: latest.periodStart,
            periodEnd: latest.periodEnd,
          });
        } else {
          emitCardResultFailed({
            source: 'training-results-card',
            sessionId,
            title: detail.title,
            templateKey: detail.templateKey,
            message: 'AI 已结束，但没有检测到归档结果',
          });
        }
      } catch (error: any) {
        emitCardResultFailed({
          source: 'training-results-card',
          sessionId,
          title: detail.title,
          templateKey: detail.templateKey,
          message: error?.message || '触发 AI 生成失败',
        });
      } finally {
        submittingRef.current = false;
      }
    };

    window.addEventListener(START_CARD_GENERATION_EVENT, handleExternalCardGeneration as EventListener);
    return () => {
      window.removeEventListener(START_CARD_GENERATION_EVENT, handleExternalCardGeneration as EventListener);
    };
  }, [createSession, setCurrentSessionId, submit]);

  const handleAttachmentsChange = useCallback(({ fileList }: { fileList: UploadFile[] }) => {
    setAttachedFiles(fileList);
  }, []);

  const handleImageUpload: UploadProps['customRequest'] = useCallback(async (options: RcCustomRequestOptions) => {
    const file = options.file as File;
    try {
      const result = await agentApi.uploadFile(file);
      options.onSuccess?.({ url: result.url }, options.file);
    } catch (error) {
      options.onError?.(error as Error);
      message.error((error as Error)?.message || '图片上传失败');
    }
  }, [message]);

  const handlePasteFile = useCallback(async (file: File) => {
    if (!file.type.startsWith('image/')) {
      message.info('当前只支持上传图片');
      return;
    }

    const tempUid = `paste_${Date.now()}`;
    setAttachedFiles((prev) => [
      ...prev,
      {
        uid: tempUid,
        name: file.name,
        status: 'uploading',
        type: file.type,
        size: file.size,
        originFileObj: file,
      } as UploadFile,
    ]);

    try {
      const result = await agentApi.uploadFile(file);
      setAttachedFiles((prev) =>
        prev.map((item) =>
          item.uid === tempUid
            ? {
                ...item,
                status: 'done',
                url: result.url,
                response: { url: result.url },
              }
            : item
        )
      );
    } catch (error) {
      setAttachedFiles((prev) => prev.filter((item) => item.uid !== tempUid));
      message.error((error as Error)?.message || '图片上传失败');
    }
  }, [message]);

  const senderHeader = (
    <Sender.Header closable={false} open={attachedFiles.length > 0}>
      <Attachments items={attachedFiles} onChange={handleAttachmentsChange} />
    </Sender.Header>
  );

  const attachmentsNode = (
    <Upload
      accept="image/*"
      multiple
      fileList={attachedFiles}
      showUploadList={false}
      customRequest={handleImageUpload}
      onChange={handleAttachmentsChange}
    >
      <button type="button" className="fitagent-chat-attachment-button" aria-label="上传图片">
        <PaperClipOutlined />
      </button>
    </Upload>
  );

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
              value={inputValue}
              onChange={setInputValue}
              loading={loading || !!pendingApproval}
              disabled={!!pendingApproval}
              sendDisabled={hasUploadingFiles}
              allowEmptySubmit={canSubmitWithAttachments}
              maxLength={10000}
              placeholder={pendingApproval ? '等待审批中...' : '输入消息...'}
              onSubmit={handleSubmit}
              onCancel={cancel}
              onPasteFile={handlePasteFile}
              header={senderHeader}
              prefix={attachmentsNode}
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
