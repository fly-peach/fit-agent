import React, { useEffect, useCallback, useMemo, useState } from 'react';
import { Markdown, DeepThinking, Accordion, StatusCard } from '@agentscope-ai/chat';
import { Button } from '@agentscope-ai/design';
import { useSessionsState } from '../../contexts/SessionContext';
import SubAgentAnalysis from './SubAgentAnalysis';
import './index.css';

// 输出消息接口定义
interface OutputMessage {
  id?: string;                             // 消息ID
  type: string;                           // 消息类型
  role?: string;                          // 消息角色
  content?: any[];                        // 消息内容
  status?: string;                        // 消息状态
  code?: string;                          // 错误代码
  message?: string;                       // 错误消息
  metadata?: Record<string, any>;         // 元数据
  outputContent?: any;                    // 输出内容
}

// 消息渲染器组件的属性接口
interface MessageRendererProps {
  output: OutputMessage[];                // 输出消息数组
}

// 从内容中提取文本的辅助函数
function extractText(content?: any[]): string {
  if (!content) return '';
  return content
    .map((c: any) => {
      if (typeof c === 'string') return c;
      if (c.type === 'text' && c.text) return c.text;
      return '';
    })
    .filter(Boolean)
    .join('\n');
}

// 判断是否为错误文本的辅助函数
function isErrorText(text: string): boolean {
  if (!text) return false;
  const t = text.trim().toLowerCase();
  return t.startsWith('错误') || t.startsWith('error') || t.startsWith('失败') || t.startsWith('failed');
}

// 判断是否为子代理消息的辅助函数
function isSubAgent(msg: OutputMessage): false | { agentName: string } {
  const source = msg.metadata?.source || '';
  const match = source.match(/^\[SubAgent\]\s+(.+)$/);
  if (match) return { agentName: match[1] };
  const dataContent = (msg.content || []).find((c: any) => c.type === 'data');
  if (dataContent?.data?.name === 'sub_agent_analysis') {
    return { agentName: dataContent.data.agentName || '分析' };
  }
  return false;
}

// 获取审批数据的辅助函数
function getApprovalData(msg: OutputMessage): { approvalId: string; toolName: string; toolArgs?: string } | null {
  const toolApproval = msg.metadata?.tool_approval;
  if (toolApproval && toolApproval.status === 'pending') {
    return {
      approvalId: toolApproval.approval_id,
      toolName: toolApproval.tool_name,
      toolArgs: toolApproval.tool_args_display,
    };
  }
  return null;
}

/** 合并连续的插件调用及其输出消息 */
function mergeToolMessages(output: OutputMessage[]): (OutputMessage & { outputContent?: any })[] {
  const result: (OutputMessage & { outputContent?: any })[] = [];
  const outputMap = new Map<string, OutputMessage>();

  // 收集按 call_id 分组的输出
  for (const msg of output) {
    if (msg.type === 'plugin_call_output' || msg.type === 'function_call_output' || msg.type === 'mcp_call_output') {
      const content = msg.content || [];
      const dataContent = content.find((c: any) => c.type === 'data');
      const callId = dataContent?.data?.call_id || dataContent?.data?.name;
      if (callId) {
        outputMap.set(callId, msg);
      } else {
        // 回退方案：将输出与最后一个工具调用关联
        outputMap.set(`__last_${result.length}`, msg);
      }
    }
  }

  for (const msg of output) {
    if (msg.type === 'plugin_call_output' || msg.type === 'function_call_output' || msg.type === 'mcp_call_output') {
      // 跳过独立的输出 - 它们合并到工具调用中
      continue;
    }

    if (msg.type === 'plugin_call' || msg.type === 'function_call' || msg.type === 'mcp_call') {
      const content = msg.content || [];
      const dataContent = content.find((c: any) => c.type === 'data');
      const callId = dataContent?.data?.call_id || dataContent?.data?.name;
      const outputMsg = callId ? outputMap.get(callId) : undefined;

      if (outputMsg) {
        const outputData = (outputMsg.content || []).find((c: any) => c.type === 'data');
        result.push({ ...msg, outputContent: outputData?.data?.output || extractText(outputMsg.content) });
      } else {
        result.push(msg);
      }
    } else {
      result.push(msg);
    }
  }

  return result;
}

/** 按子代理将连续的消息分组 */
function groupMessages(merged: OutputMessage[]): Array<{ type: 'single' | 'subagent'; agentName?: string; messages: OutputMessage[] }> {
  const groups: Array<{ type: 'single' | 'subagent'; agentName?: string; messages: OutputMessage[] }> = [];
  let currentGroup: { type: 'single' | 'subagent'; agentName?: string; messages: OutputMessage[] } | null = null;

  for (const msg of merged) {
    const subAgent = isSubAgent(msg);
    const approvalData = getApprovalData(msg);

    // 审批消息总是放在自己的组中
    if (approvalData) {
      if (currentGroup) {
        groups.push(currentGroup);
        currentGroup = null;
      }
      groups.push({ type: 'single', messages: [msg] });
      continue;
    }

    if (subAgent) {
      if (currentGroup?.type === 'subagent' && currentGroup.agentName === subAgent.agentName) {
        // 相同的子代理，添加到当前组
        currentGroup.messages.push(msg);
      } else {
        // 不同的子代理或没有组，开始新组
        if (currentGroup) {
          groups.push(currentGroup);
        }
        currentGroup = { type: 'subagent', agentName: subAgent.agentName, messages: [msg] };
      }
    } else {
      // 不是子代理消息
      if (currentGroup) {
        groups.push(currentGroup);
        currentGroup = null;
      }
      groups.push({ type: 'single', messages: [msg] });
    }
  }

  if (currentGroup) {
    groups.push(currentGroup);
  }

  return groups;
}

/** 审批卡片组件，用于渲染审批消息并处理状态 */
const ApprovalCard: React.FC<{
  msg: OutputMessage;
}> = ({ msg }) => {
  const { pendingApproval, setPendingApproval } = useSessionsState();
  const approvalData = getApprovalData(msg)!;
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (done) {
      const timer = setTimeout(() => setDismissed(true), 1500);
      return () => clearTimeout(timer);
    }
  }, [done]);

  const handleApprove = useCallback(async () => {
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/agent/approval/${approvalData.approvalId}/approve`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setDone(true);
      setPendingApproval(null);
    } catch (e: any) {
      setError(e.message || '审批失败，请重试');
    }
  }, [approvalData.approvalId, setPendingApproval]);

  const handleReject = useCallback(async () => {
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/agent/approval/${approvalData.approvalId}/reject`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setDone(true);
      setPendingApproval(null);
    } catch (e: any) {
      setError(e.message || '拒绝失败，请重试');
    }
  }, [approvalData.approvalId, setPendingApproval]);

  // 组件挂载时设置待处理审批状态
  useEffect(() => {
    if (done) return;
    if (!pendingApproval || pendingApproval.approvalId !== approvalData.approvalId) {
      setPendingApproval(approvalData);
    }
  }, [approvalData.approvalId, approvalData.toolName, approvalData.toolArgs, pendingApproval, setPendingApproval, done]);

  if (dismissed) return null;

  return (
    <div style={{ margin: '8px 0', maxWidth: '60%' }}>
      <StatusCard status={done ? 'success' : (error ? 'warning' : 'info')} title={`需要确认：${approvalData.toolName}`}>
        {!done && (
          <div style={{ padding: 16, borderTop: '1px solid #f0f0f0' }}>
            <div style={{ fontSize: 12, color: 'rgba(0,0,0,0.45)', marginBottom: 12 }}>
              {approvalData.toolArgs || 'Agent 请求使用此工具'}
            </div>
            {error && (
              <div style={{ fontSize: 12, color: '#ff4d4f', marginBottom: 8 }}>{error}</div>
            )}
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <Button type="primary" size="small" onClick={handleApprove}>允许执行</Button>
              <Button size="small" onClick={handleReject}>拒绝</Button>
            </div>
          </div>
        )}
      </StatusCard>
    </div>
  );
};

/** 渲染单个消息（不在组中） */
const SingleMessageRenderer: React.FC<{
  msg: OutputMessage;
  index: number;
}> = ({ msg, index }) => {
  const isLoading = msg.status === 'in_progress' || msg.status === 'created';
  const textContent = extractText(msg.content);

  // 错误类型消息
  if (msg.type === 'error') {
    return (
      <StatusCard
        key={msg.id || index}
        title="执行出错"
        status="error"
        description={msg.message || msg.code || '发生了未知错误'}
      />
    );
  }

  // 文本消息中的错误内容
  if (msg.type === 'message' && isErrorText(textContent)) {
    return (
      <StatusCard
        key={msg.id || index}
        title="执行出错"
        status="error"
        description={textContent}
      />
    );
  }

  // 推理/思考消息
  if (msg.type === 'reasoning') {
    return (
      <DeepThinking
        key={msg.id || index}
        title="思考"
        loading={isLoading}
        content={textContent}
        defaultOpen={isLoading}
        autoCloseOnFinish
      />
    );
  }

  // 文本消息
  if (msg.type === 'message') {
    if (!textContent) return null;
    return <Markdown key={msg.id || index} content={textContent} />;
  }

  // 插件/工具调用
  if (msg.type === 'plugin_call' || msg.type === 'function_call' || msg.type === 'mcp_call') {
    const content = msg.content || [];
    const dataContent = content.find((c: any) => c.type === 'data');
    const data = dataContent?.data || {};

    if (data.name === 'sub_agent_analysis') {
      return <SubAgentAnalysis key={msg.id || index} data={msg} />;
    }

    const toolName = data.name || msg.type;
    const toolArgs = data.arguments ? JSON.stringify(data.arguments, null, 2) : null;
    const rawOutput = msg.outputContent;
    const hasOutput = rawOutput != null && rawOutput !== '';

    let outputFormatted = '';
    if (hasOutput) {
      outputFormatted = typeof rawOutput === 'string' ? rawOutput : JSON.stringify(rawOutput, null, 2);
    }

    const steps: any[] = [];

    if (toolArgs) {
      steps.push({
        iconLine: true,
        title: '输入参数',
        defaultOpen: false,
        children: (
          <Accordion.BodyContent headerLeft="输入">
            <Markdown content={`\`\`\`json\n${toolArgs}\n\`\`\``} />
          </Accordion.BodyContent>
        ),
      });
    }

    if (hasOutput) {
      steps.push({
        iconLine: true,
        title: '执行结果',
        defaultOpen: false,
        children: isErrorText(outputFormatted) ? (
          <StatusCard title="执行出错" status="error" description={outputFormatted} />
        ) : (
          <Accordion.BodyContent headerLeft="输出">
            <Markdown content={`\`\`\`json\n${outputFormatted}\n\`\`\``} />
          </Accordion.BodyContent>
        ),
      });
    }

    return (
      <Accordion
        key={msg.id || index}
        title={toolName}
        status={isLoading ? 'generating' : (hasOutput ? 'finished' : 'finished')}
        defaultOpen={false}
        steps={steps}
      />
    );
  }

  // 心跳消息 - 跳过
  if (msg.type === 'heartbeat') return null;

  // 回退：渲染任何文本内容
  if (textContent) {
    if (isErrorText(textContent)) {
      return (
        <StatusCard
          key={msg.id || index}
          title="执行出错"
          status="error"
          description={textContent}
        />
      );
    }
    return <Markdown key={msg.id || index} content={textContent} />;
  }

  return null;
};

/** 在手风琴中渲染子代理消息组 */
const SubAgentGroupRenderer: React.FC<{
  agentName: string;
  messages: OutputMessage[];
  groupIndex: number;
}> = ({ agentName, messages, groupIndex }) => {
  const steps: any[] = [];
  let hasLoading = false;

  messages.forEach((msg, msgIndex) => {
    const isLoading = msg.status === 'in_progress' || msg.status === 'created';
    if (isLoading) hasLoading = true;

    const textContent = extractText(msg.content);

    if (msg.type === 'message' && textContent && !isErrorText(textContent)) {
      steps.push({
        iconLine: true,
        title: '分析结果',
        defaultOpen: true,
        children: (
          <Accordion.BodyContent headerLeft={agentName}>
            <Markdown content={textContent} />
          </Accordion.BodyContent>
        ),
      });
    } else if (msg.type === 'plugin_call' || msg.type === 'function_call' || msg.type === 'mcp_call') {
      const content = msg.content || [];
      const dataContent = content.find((c: any) => c.type === 'data');
      const data = dataContent?.data || {};

      if (data.name === 'sub_agent_analysis') {
        // 跳过，这由其他方式处理
        return;
      }

      const toolName = data.name || msg.type;
      const toolArgs = data.arguments ? JSON.stringify(data.arguments, null, 2) : null;
      const rawOutput = msg.outputContent;
      const hasOutput = rawOutput != null && rawOutput !== '';

      let outputFormatted = '';
      if (hasOutput) {
        outputFormatted = typeof rawOutput === 'string' ? rawOutput : JSON.stringify(rawOutput, null, 2);
      }

      const toolSteps: any[] = [];

      if (toolArgs) {
        toolSteps.push({
          iconLine: true,
          title: '输入参数',
          defaultOpen: false,
          children: (
            <Accordion.BodyContent headerLeft="输入">
              <Markdown content={`\`\`\`json\n${toolArgs}\n\`\`\``} />
            </Accordion.BodyContent>
          ),
        });
      }

      if (hasOutput) {
        toolSteps.push({
          iconLine: true,
          title: '执行结果',
          defaultOpen: false,
          children: isErrorText(outputFormatted) ? (
            <StatusCard title="执行出错" status="error" description={outputFormatted} />
          ) : (
            <Accordion.BodyContent headerLeft="输出">
              <Markdown content={`\`\`\`json\n${outputFormatted}\n\`\`\``} />
            </Accordion.BodyContent>
          ),
        });
      }

      steps.push({
        iconLine: true,
        title: `工具: ${toolName}`,
        defaultOpen: false,
        children: toolSteps.length > 0 ? (
          <Accordion key={`${groupIndex}-${msgIndex}`} steps={toolSteps} defaultOpen={false} />
        ) : null,
      });
    }
  });

  // 检查特殊的 sub_agent_analysis 调用
  const specialAnalysisMsg = messages.find((msg) => {
    const content = msg.content || [];
    const dataContent = content.find((c: any) => c.type === 'data');
    return dataContent?.data?.name === 'sub_agent_analysis';
  });

  if (specialAnalysisMsg) {
    return <SubAgentAnalysis key={specialAnalysisMsg.id || groupIndex} data={specialAnalysisMsg} />;
  }

  if (steps.length === 0) return null;

  return (
    <Accordion
      key={`subagent-${groupIndex}`}
      title={agentName}
      status={hasLoading ? 'generating' : 'finished'}
      defaultOpen={hasLoading}
      steps={steps}
    />
  );
};

// 消息渲染器组件 - 用于渲染不同类型的消息（普通消息、子代理消息、工具调用等）
const MessageRenderer: React.FC<MessageRendererProps> = ({ output }) => {
  const { setPendingApproval } = useSessionsState();
  const merged = useMemo(() => output ? mergeToolMessages(output) : [], [output]);
  const groups = useMemo(() => groupMessages(merged), [merged]);

  if (!output || output.length === 0) return null;

  return (
    <div className="message-renderer">
      {groups.map((group, groupIndex) => {
        if (group.type === 'single') {
          const msg = group.messages[0];
          const approvalData = getApprovalData(msg);
          if (approvalData) {
            return <ApprovalCard key={`group-${groupIndex}`} msg={msg} />;
          }
          return <SingleMessageRenderer key={`group-${groupIndex}`} msg={msg} index={groupIndex} />;
        } else {
          return (
            <SubAgentGroupRenderer
              key={`group-${groupIndex}`}
              agentName={group.agentName!}
              messages={group.messages}
              groupIndex={groupIndex}
            />
          );
        }
      })}
    </div>
  );
};

export default MessageRenderer;