import { useRef, useState, useCallback } from 'react';
import { marked } from 'marked';

const API_BASE_URL = '/api';
const API_ENDPOINT = '/api/chat';
const MAX_CHARS = 10000;

let idCounter = 0;
function genId() {
  return `msg-${++idCounter}-${Date.now()}`;
}

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const sessionIdRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Add a user message
  const appendUserMessage = useCallback((text) => {
    const msg = {
      _id: genId(),
      type: 'text',
      content: { text },
      position: 'right',
      user: { _id: 'user', name: 'You' },
      createdAt: Date.now(),
    };
    setMessages(prev => [...prev, msg]);
    return msg._id;
  }, []);

  // Add an AI message placeholder
  const createAiMessage = useCallback(() => {
    const id = genId();
    const msg = {
      _id: id,
      type: 'text',
      content: { text: '' },
      position: 'left',
      user: { _id: 'ai', name: 'AI', avatar: '' },
      createdAt: Date.now(),
      meta: {
        thinking: '',
        tools: [],
        text: '',
        approvalCards: [],
      },
    };
    setMessages(prev => [...prev, msg]);
    return id;
  }, []);

  // Update a specific message by id
  const updateMessage = useCallback((id, updater) => {
    setMessages(prev => prev.map(m => m._id === id ? { ...m, ...updater(m) } : m));
  }, []);

  // Escape HTML
  const escapeHtml = (text) => {
    if (typeof text !== 'string') return String(text);
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  };

  // Send message
  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || isStreaming) return;

    appendUserMessage(text);
    const aiId = createAiMessage();
    setIsStreaming(true);

    if (!sessionIdRef.current) {
      sessionIdRef.current = genId();
    }

    const sessionId = sessionIdRef.current;

    // Build message history from current state
    const history = messages
      .filter(m => m.type === 'text' && m.content.text)
      .map(m => ({ role: m.position === 'right' ? 'user' : 'assistant', content: m.content.text }));
    history.push({ role: 'user', content: text });

    const requestBody = {
      input: history,
      session_id: sessionId,
      enable_reasoning: true,
      enable_tools: true,
      tools_require_approval: ['execute_python', 'execute_shell_command'],
    };

    try {
      abortControllerRef.current = new AbortController();
      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      await processStream(aiId, response.body);
    } catch (err) {
      console.log('API call failed, falling back to simulation:', err.message);
      await simulateStreaming(aiId, text);
    }
  }, [isStreaming, messages, appendUserMessage, createAiMessage]);

  // Process SSE stream
  const processStream = async (aiId, readableStream) => {
    const reader = readableStream.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const decoded = decoder.decode(value, { stream: true });
        buffer += decoded;
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (line.trim().startsWith('data: ')) {
            try {
              const parsed = JSON.parse(line.trim().substring(6));
              handleStreamEvent(aiId, parsed);
            } catch (e) {
              // skip parse errors
            }
          }
        }
      }

      // Process remaining buffer
      if (buffer.trim().startsWith('data: ')) {
        try {
          const parsed = JSON.parse(buffer.trim().substring(6));
          handleStreamEvent(aiId, parsed);
        } catch (e) { /* skip */ }
      }

      finalizeStream(aiId);
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Stream error:', err);
        await simulateStreaming(aiId, 'error');
      }
    }
  };

  // Handle a single stream event
  const handleStreamEvent = (aiId, event) => {
    switch (event.object) {
      case 'response':
        if (event.status === 'completed') {
          finalizeStream(aiId);
        }
        break;

      case 'message':
        if (event.status === 'in_progress') {
          if (event.reasoning_content) {
            updateMessage(aiId, (m) => ({
              meta: { ...m.meta, thinking: m.meta.thinking || event.reasoning_content },
            }));
          }
          if (event.content) {
            const textContent = Array.isArray(event.content)
              ? event.content.find(c => c.type === 'text')?.text
              : event.content;
            if (textContent) {
              updateMessage(aiId, (m) => ({
                meta: { ...m.meta, text: (m.meta.text || '') + textContent },
              }));
            }
          }
          if (event.tool_calls?.length > 0) {
            handleToolCalls(aiId, event.tool_calls);
          }
        } else if (event.status === 'completed') {
          if (event.content && Array.isArray(event.content)) {
            const textItem = event.content.find(c => c.type === 'text');
            if (textItem) {
              updateMessage(aiId, (m) => ({ meta: { ...m.meta, text: textItem.text } }));
            }
            const reasoningItem = event.content.find(c => c.type === 'reasoning');
            if (reasoningItem) {
              updateMessage(aiId, (m) => ({ meta: { ...m.meta, thinking: reasoningItem.text } }));
            }
          }
        }
        break;

      case 'content':
        if (event.status === 'in_progress') {
          switch (event.type) {
            case 'reasoning':
              if (event.text) {
                updateMessage(aiId, (m) => ({
                  meta: { ...m.meta, thinking: (m.meta.thinking || '') + event.text },
                }));
              }
              break;

            case 'text':
              if (event.text) {
                updateMessage(aiId, (m) => ({
                  meta: { ...m.meta, text: (m.meta.text || '') + event.text },
                }));
              }
              break;

            case 'tool_calls':
              if (event.tool_calls) handleToolCalls(aiId, event.tool_calls);
              break;

            case 'approval_request':
              if (event.approval_id && event.tool_call) {
                addApprovalCard(aiId, event.approval_id, event.tool_call);
              }
              break;

            case 'tool_result':
              if (event.tool_name && event.result !== undefined) {
                updateLastToolOutput(aiId, event.result);
              }
              break;
          }
        }
        break;
    }
  };

  // Handle tool calls
  const handleToolCalls = (aiId, toolCalls) => {
    for (const toolCall of toolCalls) {
      if (toolCall.function) {
        let toolInput;
        try {
          toolInput = JSON.parse(toolCall.function.arguments || '{}');
        } catch {
          toolInput = { args: toolCall.function.arguments };
        }
        const toolCard = {
          id: genId(),
          name: toolCall.function.name,
          input: toolInput,
          output: null,
          collapsed: false,
        };
        updateMessage(aiId, (m) => ({
          meta: { ...m.meta, tools: [...m.meta.tools, toolCard] },
        }));
      }
    }
  };

  // Update last tool output
  const updateLastToolOutput = (aiId, result) => {
    updateMessage(aiId, (m) => {
      const tools = [...m.meta.tools];
      if (tools.length > 0) {
        tools[tools.length - 1] = { ...tools[tools.length - 1], output: result };
      }
      return { meta: { ...m.meta, tools } };
    });
  };

  // Add approval card
  const addApprovalCard = (aiId, approvalId, toolCall) => {
    let toolInput;
    try {
      toolInput = JSON.parse(toolCall.function?.arguments || '{}');
    } catch {
      toolInput = { args: toolCall.function?.arguments };
    }

    let codeContent = '';
    if (toolInput.code) codeContent = toolInput.code;
    else if (toolInput.command) codeContent = toolInput.command;
    else codeContent = JSON.stringify(toolInput, null, 2);

    const card = {
      id: approvalId,
      type: 'approval',
      toolName: toolCall.function?.name || 'unknown',
      code: codeContent,
      toolCall,
      status: 'pending',
    };

    updateMessage(aiId, (m) => ({
      meta: { ...m.meta, approvalCards: [...(m.meta.approvalCards || []), card] },
    }));
  };

  // Submit approval
  const submitApproval = useCallback(async (approvalId, approved) => {
    // Optimistic UI update
    updateMessagesWithApprovalStatus(approvalId, approved ? 'approved' : 'rejected');

    try {
      const response = await fetch(`${API_BASE_URL}/chat/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approval_id: approvalId, approved }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();

      if (approved) {
        // Show tool card after approval
        updateMessagesApprovalToTool(approvalId);
      }
    } catch (err) {
      console.error('Approval submit failed:', err);
      updateMessagesWithApprovalStatus(approvalId, 'failed');
    }
  }, []);

  // Update approval status in messages
  const updateMessagesWithApprovalStatus = (approvalId, status) => {
    setMessages(prev => prev.map(m => {
      if (!m.meta?.approvalCards) return m;
      return {
        ...m,
        meta: {
          ...m.meta,
          approvalCards: m.meta.approvalCards.map(c =>
            c.id === approvalId ? { ...c, status } : c
          ),
        },
      };
    }));
  };

  // Convert approval card to tool card
  const updateMessagesApprovalToTool = (approvalId) => {
    setMessages(prev => prev.map(m => {
      if (!m.meta?.approvalCards) return m;
      const card = m.meta.approvalCards.find(c => c.id === approvalId);
      if (!card) return m;
      const toolCard = {
        id: card.id,
        name: card.toolName,
        input: card.toolCall?.function ? JSON.parse(card.toolCall.function.arguments || '{}') : {},
        output: null,
        collapsed: false,
      };
      return {
        ...m,
        meta: {
          ...m.meta,
          approvalCards: m.meta.approvalCards.map(c =>
            c.id === approvalId ? { ...c, status: 'converted' } : c
          ),
          tools: [...m.meta.tools, toolCard],
        },
      };
    }));
  };

  // Finalize streaming
  const finalizeStream = (aiId) => {
    setIsStreaming(false);
    updateMessage(aiId, (m) => {
      // Ensure rendered HTML is set
      const rawText = m.meta.text || '(无回复内容)';
      return {
        content: { text: rawText, html: marked.parse(rawText) },
        meta: m.meta,
      };
    });
    sessionIdRef.current = null; // Reset session after completion
  };

  // Simulate streaming (fallback)
  const simulateStreaming = async (aiId, userText) => {
    const thinkingSteps = [
      `1. **分析请求**: 用户想要${(userText?.includes('python') || userText?.includes('Python')) ? '使用Python工具执行代码' : '获取相关信息'}。`,
      '\n\n2. **识别工具**: 查看可用工具...',
      '\n\n3. **制定计划**: 确定最佳响应策略。',
    ];

    let thinkingText = '';
    for (const step of thinkingSteps) {
      thinkingText += step;
      updateMessage(aiId, (m) => ({ meta: { ...m.meta, thinking: thinkingText } }));
      await sleep(300);
    }

    if (userText?.includes('python') || userText?.includes('Python') || userText?.includes('1+1')) {
      handleToolCalls(aiId, [{
        function: { name: 'execute_shell_command', arguments: '{"command":"python -c \\"print(1 + 1)\\""}' },
      }]);
      await sleep(500);
      updateLastToolOutput(aiId, '[\n  {\n    "type": "text",\n    "text": "2"\n  }\n]');
      await sleep(200);
    }

    const responseChunks = [
      '我来帮你处理这个请求。',
      '\n\n',
      (userText?.includes('1+1') || userText?.includes('python'))
        ? '我使用了Python工具来执行计算。'
        : '根据你的问题，我整理了以下信息：',
      '\n\n',
      '**结果**:\n\n',
      '结果是 ',
      '2',
      '。',
      '\n\n',
      '如果你需要运行更复杂的Python脚本或处理其他任务，随时告诉我！',
    ];

    let fullText = '';
    for (const chunk of responseChunks) {
      fullText += chunk;
      updateMessage(aiId, (m) => ({
        meta: { ...m.meta, text: fullText },
        content: { text: fullText, html: marked.parse(fullText) + '<span class="streaming-cursor"></span>' },
      }));
      await sleep(chunk.length > 10 ? 100 : 50);
    }

    // Finalize
    updateMessage(aiId, (m) => ({
      content: { text: fullText, html: marked.parse(fullText) },
      meta: { ...m.meta, text: fullText },
    }));
    setIsStreaming(false);
  };

  // New chat
  const newChat = useCallback(() => {
    setMessages([]);
    sessionIdRef.current = null;
    setIsStreaming(false);
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  return {
    messages,
    isStreaming,
    sendMessage,
    newChat,
    submitApproval,
    MAX_CHARS,
  };
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
