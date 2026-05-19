import React from 'react';
import { Accordion, Markdown } from '@agentscope-ai/chat';

// 子代理分析组件的属性接口
interface SubAgentAnalysisProps {
  data: any;  // 包含子代理分析数据的对象
}

// 子代理分析组件 - 显示子代理的分析结果
const SubAgentAnalysis: React.FC<SubAgentAnalysisProps> = ({ data }) => {
  // 如果数据为空或内容长度为0，则不渲染任何内容
  if (!data?.content?.length) return null;

  // 获取第一个内容项
  const content0 = data.content[0];
  // 获取代理名称，如果没有则默认为'分析'
  const agentName = content0?.data?.agentName || '分析';
  // 检查是否正在加载中
  const isLoading = data.status === 'in_progress';

  // 提取输出文本
  let outputText = '';
  // 从第二个内容项开始遍历，收集输出文本
  for (let i = 1; i < data.content.length; i++) {
    const c = data.content[i];
    if (c?.data?.output) {
      outputText += c.data.output;
    }
  }

  // 渲染子代理分析结果
  return (
    <Accordion
      title={`${agentName}`}  // 显示代理名称作为标题
      status={isLoading ? 'generating' : 'finished'}  // 根据加载状态设置状态
      defaultOpen={isLoading}  // 如果正在加载则默认展开
      steps={[
        {
          iconLine: true,
          title: '分析结果',
          defaultOpen: true,
          children: outputText ? (
            // 如果有输出文本，则渲染Markdown格式的内容
            <Accordion.BodyContent headerLeft={agentName}>
              <div className="subagent-body-content">
                <Markdown content={outputText} />
              </div>
            </Accordion.BodyContent>
          ) : isLoading ? (
            // 如果正在加载但没有输出文本，则显示加载中提示
            <div className="subagent-loading-text">正在分析中...</div>
          ) : null,  // 没有输出文本也不在加载中则不渲染
        },
      ]}
    />
  );
};

export default SubAgentAnalysis;