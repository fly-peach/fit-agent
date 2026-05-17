import { AgentScopeRuntimeWebUI, IAgentScopeRuntimeWebUIOptions } from '@agentscope-ai/chat';
import { ConfigProvider } from 'antd';
import { useMemo } from 'react';
import sessionApi from './sessionApi';
import ChatActionGroup from './components/ChatActionGroup';
import ChatHeaderTitle from './components/ChatHeaderTitle';
import SubAgentAnalysis from './SubAgentAnalysis';
import ToolApprovalCard from './ToolApprovalCard';
import './ToolApprovalCard.css';
import './components/ChatSessionDrawer/index.css';
import './components/ChatSearchPanel/index.css';
import './components/ChatSessionItem/index.css';
import './components/ChatHeaderTitle/index.css';
import './index.css';

/**
 * 从 source 字符串提取子 Agent 名称，如 "[SubAgent] DietAnalyst" → "DietAnalyst"
 */
const extractSubAgentName = (source: string): string | null => {
  const match = source.match(/^\[SubAgent\]\s+(.+)$/);
  return match?.[1] || null;
};

/**
 * SubAgent 消息 ID 缓存 — 记录已经识别为 SubAgent 的消息 ID，
 * 用于后续 message 级别更新 chunk 的拦截。
 */
const subAgentMsgIds = new Set<string>();

/**
 * 将 output 数组中 SubAgent 消息转为 plugin_call 格式。
 * content[0]: { type: "data", data: { name, agentName } }
 * content[1]: { type: "data", data: { output: text } }
 */
const convertSubAgentOutput = (output: Record<string, any>[]) => {
  for (const msg of output) {
    if (msg.type === 'message' && msg.metadata?.source?.startsWith('[SubAgent]')) {
      const agentName = extractSubAgentName(msg.metadata.source) || '分析';
      subAgentMsgIds.add(msg.id);
      // 提取文本
      let combinedText = '';
      for (const c of msg.content || []) {
        if (c.type === 'text' && c.text) combinedText += c.text;
      }
      msg.type = 'plugin_call';
      msg.content = [
        { type: 'data', data: { name: 'sub_agent_analysis', agentName } },
        { type: 'data', data: { output: combinedText } },
      ];
    }
  }
};

/**
 * 将 SubAgent 消息转为 plugin_call 格式（替换 reasoning 方案），
 * 通过 customToolRenderConfig 注册的 SubAgentAnalysis 组件，
 * 使用 Thinking 渲染，标题显示 Agent 名称。
 */
const subAgentResponseParser = (chunkData: string) => {
  console.log('[subAgentResponseParser] raw chunk:', chunkData);
  const parsed = JSON.parse(chunkData);
  console.log('[subAgentResponseParser] parsed:', parsed);

  // 拦截审批消息 → 转为 plugin_call
  if (parsed.metadata?.tool_approval) {
    console.log('[subAgentResponseParser] Found tool_approval in metadata!');
    const { approval_id, tool_name, tool_args_display } = parsed.metadata.tool_approval;
    return {
      ...parsed,
      type: 'plugin_call',
      content: [
        { type: 'data', data: { name: 'tool_approval', approvalId: approval_id, toolName: tool_name, toolArgs: tool_args_display } },
      ],
    };
  }

  // 兼容：检查 content 里的 tool_use/tool_call
  if (Array.isArray(parsed.content)) {
    for (const block of parsed.content) {
      if (block.type === 'tool_use' || block.type === 'tool_call') {
        if (block.name === 'tool_approval') {
          console.log('[subAgentResponseParser] Found tool_approval in content!');
          return {
            ...parsed,
            type: 'plugin_call',
            content: [
              { type: 'data', data: { name: 'tool_approval', ...block.arguments } },
            ],
          };
        }
      }
    }
  }

  // 拦截 response 级别 — 处理完整的 output 数组
  if (parsed.object === 'response' && Array.isArray(parsed.output)) {
    convertSubAgentOutput(parsed.output);
    return parsed;
  }

  // 拦截 message 级别
  if (parsed.object === 'message') {
    if (
      parsed.type === 'message' &&
      parsed.metadata?.source?.startsWith('[SubAgent]')
    ) {
      const agentName = extractSubAgentName(parsed.metadata.source) || '分析';
      subAgentMsgIds.add(parsed.id);

      let combinedText = '';
      for (const c of parsed.content || []) {
        if (c.type === 'text' && c.text) combinedText += c.text;
      }

      return {
        ...parsed,
        type: 'plugin_call',
        content: [
          { type: 'data', data: { name: 'sub_agent_analysis', agentName } },
          { type: 'data', data: { output: combinedText } },
        ],
      };
    }

    // 后续 message 级别更新 — 保持 plugin_call 类型
    if (subAgentMsgIds.has(parsed.id)) {
      return { ...parsed, type: 'plugin_call' };
    }
  }

  return parsed;
};

const AIAssistant: React.FC = () => {
  const options = useMemo((): IAgentScopeRuntimeWebUIOptions => {
    const token = localStorage.getItem('token');
    // 把 token 放在查询参数里，确保 SSE 请求也能认证
    const baseURL = token ? `/process?token=${encodeURIComponent(token)}` : '/process';
    return {
      api: {
        baseURL: baseURL,
        token: token || '',
        responseParser: subAgentResponseParser,
      },
      session: {
        multiple: true,
        api: sessionApi,
        hideBuiltInSessionList: true,
      },
      theme: {
        colorPrimary: '#615CED',
        darkMode: false,
        prefix: 'agentscope-runtime-webui',
        rightHeader: <ChatActionGroup />,
        leftHeader: <ChatHeaderTitle />,
      },
      sender: {
        attachments: {
          customRequest: async ({ file, onSuccess, onError }: any) => {
            const formData = new FormData();
            formData.append('file', file);
            const token = localStorage.getItem('token');
            try {
              const resp = await fetch('/api/agent/upload', {
                method: 'POST',
                headers: { Authorization: `Bearer ${token}` },
                body: formData,
              });
              if (!resp.ok) throw new Error('Upload failed');
              const data = await resp.json();
              onSuccess({ url: data.url });
            } catch (e: any) {
              onError(e);
            }
          },
        },
        maxLength: 10000,
      },
      welcome: {
        greeting: '你好，我是你的健身助手！',
        description: '我可以帮你制定训练计划、管理饮食、追踪健康数据。',
        avatar: 'https://images.icon-icons.com/1429/PNG/96/icon-robots-3_98540.png',
        prompts: [
          { value: '帮我制定一个减脂训练计划' },
          { value: '今天应该吃多少蛋白质？' },
          { value: '如何提高跑步耐力？' },
        ],
      },
      customToolRenderConfig: {
        'sub_agent_analysis': SubAgentAnalysis,
        'tool_approval': ToolApprovalCard,
      },
    } as unknown as IAgentScopeRuntimeWebUIOptions;
  }, []);

  return (
    <ConfigProvider getPopupContainer={() => document.querySelector('.agentscope-runtime-webui') as HTMLElement}>
      <div className="agentscope-runtime-webui">
        <AgentScopeRuntimeWebUI options={options} />
      </div>
    </ConfigProvider>
  );
};

export default AIAssistant;
