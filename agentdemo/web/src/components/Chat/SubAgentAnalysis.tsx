import React from 'react';
import { Accordion, Thinking, DeepThinking } from '@agentscope-ai/chat';

/**
 * SubAgent 分析折叠卡片组件。
 * 通过 customToolRenderConfig 注册，应对 responseParser 转成 plugin_call
 * 的 SubAgent 消息。
 *
 * data.content 结构：
 *   [0]: { type: "data", data: { name: string, agentName: string } }
 *   [1] 或后续: { type: "data", data: { output: string } }
 */
const SubAgentAnalysis = React.memo(({ data }: { data: any }) => {
  if (!data?.content?.length) return null;

  const content0 = data.content[0];
  const agentName = content0?.data?.agentName || '分析';
  const loading = data.status === 'in_progress';

  // 提取 output 文本（可能在 content[1] 或后续位置）
  let outputText = '';
  for (let i = 1; i < data.content.length; i++) {
    const c = data.content[i];
    if (c?.data?.output) {
      outputText += c.data.output;
    }
  }

  return (
    <Thinking
      title={agentName}
      content={outputText}
      loading={loading}
      defaultOpen={false}
    />
  );
});

export default SubAgentAnalysis;
