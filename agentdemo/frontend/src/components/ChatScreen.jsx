import Chat, { Bubble } from '@chatui/core';
import '@chatui/core/dist/index.css';
import { useState, useCallback } from 'react';
import { useChat } from '../hooks/useChat';
import { marked } from 'marked';

function ChatScreen({ onNewChat }) {
  const { messages: chatMessages, isStreaming, sendMessage, newChat, submitApproval } = useChat();

  const handleSend = useCallback((type, val) => {
    if (type === 'text' && val.trim()) {
      sendMessage(val);
    }
  }, [sendMessage]);

  const renderMessageContent = useCallback((msg) => {
    const { content, meta, position } = msg;

    // User message - just show text in a bubble
    if (position === 'right') {
      return <Bubble>{content.text}</Bubble>;
    }

    // AI message - render custom content
    return (
      <div className="message-wrapper">
        {/* Thinking area */}
        {meta?.thinking && (
          <ThinkingSection content={meta.thinking} />
        )}

        {/* Tool cards */}
        {meta?.tools?.map((tool, idx) => (
          <ToolCard key={tool.id || idx} tool={tool} />
        ))}

        {/* Approval cards */}
        {meta?.approvalCards?.map((card, idx) => (
          card.status !== 'converted' && (
            <ApprovalCard key={card.id || idx} card={card} onApprove={submitApproval} />
          )
        ))}

        {/* AI text response */}
        {content?.text ? (
          <Bubble>
            <div
              className="ai-text-content"
              dangerouslySetInnerHTML={{ __html: content.html || marked.parse(content.text) }}
            />
          </Bubble>
        ) : isStreaming ? (
          <Bubble>
            <div className="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </Bubble>
        ) : null}
      </div>
    );
  }, [isStreaming, submitApproval]);

  return (
    <div className="chat-page">
      <Chat
        navbar={{
          title: 'AI 助手',
          leftContent: (
            <button
              className="chat-new-chat-btn"
              onClick={() => {
                newChat();
                onNewChat?.();
              }}
              title="新对话"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '18px', height: '18px' }}>
                <path d="M5 12h14" />
                <path d="M12 5v14" />
              </svg>
            </button>
          ),
        }}
        messages={chatMessages}
        renderMessageContent={renderMessageContent}
        onSend={handleSend}
        placeholder="输入您的问题..."
      />
    </div>
  );
}

// Thinking Section Component
function ThinkingSection({ content }) {
  const [collapsed, setCollapsed] = useState(true);

  return (
    <div className="thinking-area">
      <div
        className={`thinking-header ${collapsed ? 'collapsed' : ''}`}
        onClick={() => setCollapsed(!collapsed)}
      >
        <svg className="sparkles-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
        </svg>
        <span className="thinking-title">Thinking</span>
        <svg className="chevron-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </div>
      <div className={`thinking-content ${collapsed ? 'collapsed' : ''}`}>
        {content}
      </div>
    </div>
  );
}

// Tool Card Component
function ToolCard({ tool }) {
  const [collapsed, setCollapsed] = useState(true);

  return (
    <div className="tool-card">
      <div
        className={`tool-header ${collapsed ? 'collapsed' : ''}`}
        onClick={() => setCollapsed(!collapsed)}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
        </svg>
        <span className="tool-name">{tool.name}</span>
        <svg className="chevron-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </div>
      <div className={`tool-content ${collapsed ? 'collapsed' : ''}`}>
        <div className="tool-section">
          <div className="tool-section-label">Input</div>
          <pre className="tool-code">{JSON.stringify(tool.input, null, 2)}</pre>
        </div>
        {tool.output !== null && (
          <div className="tool-section">
            <div className="tool-section-label">Output</div>
            <pre className="tool-code">{typeof tool.output === 'string' ? tool.output : JSON.stringify(tool.output, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

// Approval Card Component
function ApprovalCard({ card, onApprove }) {
  const [status, setStatus] = useState(card.status || 'pending');

  const handleAction = async (approved) => {
    setStatus(approved ? 'approved' : 'rejected');
    await onApprove(card.id, approved);
  };

  return (
    <div className="approval-card">
      <div className="approval-header">
        <svg className="approval-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span className="approval-title">需要您的审批</span>
      </div>
      <div className="approval-content">
        <div className="approval-tool-name">{card.toolName}</div>
        <pre className="approval-code">{card.code}</pre>
      </div>

      {status === 'pending' && (
        <div className="approval-buttons">
          <button className="approval-btn approval-btn-reject" onClick={() => handleAction(false)}>
            拒绝
          </button>
          <button className="approval-btn approval-btn-approve" onClick={() => handleAction(true)}>
            批准
          </button>
        </div>
      )}

      {status === 'approved' && (
        <div className="approval-status approval-status-approved">已批准 - 正在执行...</div>
      )}
      {status === 'rejected' && (
        <div className="approval-status approval-status-rejected">已拒绝</div>
      )}
      {status === 'failed' && (
        <div className="approval-status approval-status-rejected">提交失败</div>
      )}
    </div>
  );
}

export default ChatScreen;
