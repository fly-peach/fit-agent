import React from 'react';
import { Accordion, Markdown } from '@agentscope-ai/chat';

interface SubAgentAnalysisProps {
  data: any;
}

const SubAgentAnalysis: React.FC<SubAgentAnalysisProps> = ({ data }) => {
  if (!data?.content?.length) return null;

  const content0 = data.content[0];
  const agentName = content0?.data?.agentName || '分析';
  const isLoading = data.status === 'in_progress';

  // Collect output text from content items after the first
  let outputText = '';
  for (let i = 1; i < data.content.length; i++) {
    const c = data.content[i];
    if (c?.data?.output) {
      outputText += c.data.output;
    }
  }

  return (
    <Accordion
      title={`${agentName}`}
      status={isLoading ? 'generating' : 'finished'}
      defaultOpen={isLoading}
      steps={[
        {
          iconLine: true,
          title: '分析结果',
          defaultOpen: true,
          children: outputText ? (
            <Accordion.BodyContent headerLeft={agentName}>
              <div className="subagent-body-content">
                <Markdown content={outputText} />
              </div>
            </Accordion.BodyContent>
          ) : isLoading ? (
            <div className="subagent-loading-text">正在分析中...</div>
          ) : null,
        },
      ]}
    />
  );
};

export default SubAgentAnalysis;
