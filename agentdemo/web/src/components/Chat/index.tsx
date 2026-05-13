import { AgentScopeRuntimeWebUI, IAgentScopeRuntimeWebUIOptions } from '@agentscope-ai/chat';
import OptionsPanel from './OptionsPanel';
import { useCallback, useMemo } from 'react';
import sessionApi from './sessionApi';
import { useLocalStorageState } from 'ahooks';
import defaultConfig from './OptionsPanel/defaultConfig';
import Weather from '../Cards/Weather';
import SubAgentAnalysis from './SubAgentAnalysis';

/**
 * 从 source 字符串提取子 Agent 名称，如 "[SubAgent] DietAnalyst" → "DietAnalyst"
 */
const extractSubAgentName = (source: string): string | null => {
  const match = source.match(/^\[SubAgent\]\s+(.+)$/);
  return match?.[1] || null;
};

/**
 * SubAgent 消息 ID 缓存 —— 记录已经识别为 SubAgent 的消息 ID，
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
 * 通过 customToolRenderConfig 注册的 <SubAgentAnalysis> 组件，
 * 使用 <Thinking> 渲染，标题显示 Agent 名称。
 */
const subAgentResponseParser = (chunkData: string) => {
  const parsed = JSON.parse(chunkData);

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

export default function () {
  const [optionsConfig, setOptionsConfig] = useLocalStorageState('agent-scope-runtime-webui-options', {
    defaultValue: defaultConfig,
    listenStorageChange: true,
  });

  const options = useMemo(() => {
    const rightHeader = <OptionsPanel value={optionsConfig} onChange={(v: typeof optionsConfig) => {
      setOptionsConfig(prev => ({
        ...prev,
        ...v,
      }));
    }} />;

    return {
      ...optionsConfig,
      api: {
        ...optionsConfig.api,
        responseParser: subAgentResponseParser,
      },
      session: {
        multiple: true,
        api: sessionApi,
      },
      theme: {
        ...optionsConfig.theme,
        rightHeader,
      },
      customToolRenderConfig: {
        'weather search mock': Weather,
        'sub_agent_analysis': SubAgentAnalysis,
      },
    } as unknown as IAgentScopeRuntimeWebUIOptions
  }, [optionsConfig]);




  return <div style={{ height: '100vh' }}>
    <AgentScopeRuntimeWebUI
      options={options}
    />
  </div>;
}