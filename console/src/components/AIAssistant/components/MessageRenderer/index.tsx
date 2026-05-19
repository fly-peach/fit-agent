import React, { useEffect, useCallback, useMemo } from 'react';
import { Markdown, DeepThinking, Accordion, StatusCard } from '@agentscope-ai/chat';
import { Button } from 'antd';
import { useSessionsState } from '../../contexts/SessionContext';
import SubAgentAnalysis from '../../SubAgentAnalysis';

interface OutputMessage {
  id?: string;
  type: string;
  role?: string;
  content?: any[];
  status?: string;
  code?: string;
  message?: string;
  metadata?: Record<string, any>;
  outputContent?: any;
}

interface MessageRendererProps {
  output: OutputMessage[];
}

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

function isErrorText(text: string): boolean {
  if (!text) return false;
  const t = text.trim().toLowerCase();
  return t.startsWith('错误') || t.startsWith('error') || t.startsWith('失败') || t.startsWith('failed');
}

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

/** Merge consecutive plugin_call + plugin_call_output pairs */
function mergeToolMessages(output: OutputMessage[]): (OutputMessage & { outputContent?: any })[] {
  const result: (OutputMessage & { outputContent?: any })[] = [];
  const outputMap = new Map<string, OutputMessage>();

  // Collect outputs by call_id
  for (const msg of output) {
    if (msg.type === 'plugin_call_output' || msg.type === 'function_call_output' || msg.type === 'mcp_call_output') {
      const content = msg.content || [];
      const dataContent = content.find((c: any) => c.type === 'data');
      const callId = dataContent?.data?.call_id || dataContent?.data?.name;
      if (callId) {
        outputMap.set(callId, msg);
      } else {
        // Fallback: associate with the last tool call
        outputMap.set(`__last_${result.length}`, msg);
      }
    }
  }

  for (const msg of output) {
    if (msg.type === 'plugin_call_output' || msg.type === 'function_call_output' || msg.type === 'mcp_call_output') {
      // Skip standalone outputs — they're merged into the tool call
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

/** Group consecutive messages by SubAgent */
function groupMessages(merged: OutputMessage[]): Array<{ type: 'single' | 'subagent'; agentName?: string; messages: OutputMessage[] }> {
  const groups: Array<{ type: 'single' | 'subagent'; agentName?: string; messages: OutputMessage[] }> = [];
  let currentGroup: { type: 'single' | 'subagent'; agentName?: string; messages: OutputMessage[] } | null = null;

  for (const msg of merged) {
    const subAgent = isSubAgent(msg);
    const approvalData = getApprovalData(msg);

    // Approval messages always go in their own group
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
        // Same SubAgent, add to current group
        currentGroup.messages.push(msg);
      } else {
        // Different SubAgent or no group, start new group
        if (currentGroup) {
          groups.push(currentGroup);
        }
        currentGroup = { type: 'subagent', agentName: subAgent.agentName, messages: [msg] };
      }
    } else {
      // Not a SubAgent message
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

/** Component to render approval card and handle state */
const ApprovalCard: React.FC<{
  msg: OutputMessage;
  index: number;
}> = ({ msg, index }) => {
  const { pendingApproval, setPendingApproval } = useSessionsState();
  const approvalData = getApprovalData(msg)!;

  const handleApprove = useCallback(async () => {
    const token = localStorage.getItem('token');
    await fetch(`/api/agent/approval/${approvalData.approvalId}/approve`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    setPendingApproval(null);
  }, [approvalData.approvalId, setPendingApproval]);

  const handleReject = useCallback(async () => {
    const token = localStorage.getItem('token');
    await fetch(`/api/agent/approval/${approvalData.approvalId}/reject`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    setPendingApproval(null);
  }, [approvalData.approvalId, setPendingApproval]);

  // Set pending approval state when this component mounts
  useEffect(() => {
    setPendingApproval(approvalData);
  }, [approvalData, setPendingApproval]);

  const isDone = !pendingApproval || pendingApproval.approvalId !== approvalData.approvalId;

  return (
    <div key={msg.id || index} style={{ margin: '8px 0' }}>
      <StatusCard.HITL
        done={isDone}
        onDone={handleApprove}
        title={`需要确认：${approvalData.toolName}`}
        description={approvalData.toolArgs || 'Agent 请求使用此工具'}
        waitButtonText="允许执行"
        doneButtonText="已允许执行"
        actions={
          <Button type="default" size="small" onClick={handleReject}>
            拒绝
          </Button>
        }
      />
    </div>
  );
};

/** Render a single message (not in a group) */
const SingleMessageRenderer: React.FC<{
  msg: OutputMessage;
  index: number;
}> = ({ msg, index }) => {
  const isLoading = msg.status === 'in_progress' || msg.status === 'created';
  const textContent = extractText(msg.content);

  // Error type messages
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

  // Error content in text messages
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

  // Reasoning / thinking messages
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

  // Text messages
  if (msg.type === 'message') {
    if (!textContent) return null;
    return <Markdown key={msg.id || index} content={textContent} />;
  }

  // Plugin/tool calls
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

  // Heartbeat - skip
  if (msg.type === 'heartbeat') return null;

  // Fallback: render any text content
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

/** Render a SubAgent message group in an Accordion */
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
        // Skip, this is handled differently
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

  // Check for special sub_agent_analysis call
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

const MessageRenderer: React.FC<MessageRendererProps> = ({ output }) => {
  const { setPendingApproval } = useSessionsState();

  if (!output || output.length === 0) return null;

  const merged = mergeToolMessages(output);
  const groups = useMemo(() => groupMessages(merged), [merged]);

  return (
    <div className="message-renderer">
      {groups.map((group, groupIndex) => {
        if (group.type === 'single') {
          const msg = group.messages[0];
          const approvalData = getApprovalData(msg);
          if (approvalData) {
            return <ApprovalCard key={`group-${groupIndex}`} msg={msg} index={groupIndex} />;
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
