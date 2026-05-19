import { StatusCard } from '@agentscope-ai/chat';
import { useState } from 'react';
import './ToolApprovalCard.css';

interface ToolApprovalCardProps {
  data: {
    approvalId: string;
    toolName: string;
    toolArgs?: string;
  };
}

const ToolApprovalCard: React.FC<ToolApprovalCardProps> = ({ data }) => {
  const [done, setDone] = useState(false);

  const handleApprove = async () => {
    const token = localStorage.getItem('token');
    await fetch(`/api/agent/approval/${data.approvalId}/approve`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    setDone(true);
  };

  const handleReject = async () => {
    const token = localStorage.getItem('token');
    await fetch(`/api/agent/approval/${data.approvalId}/reject`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    setDone(true);
  };

  return (
    <StatusCard.HITL
      done={done}
      onDone={handleApprove}
      title={`需要确认：${data.toolName}`}
      description={data.toolArgs || 'Agent 请求使用此工具'}
      waitButtonText="允许执行"
      doneButtonText="已允许执行"
      actions={!done ? (
        <button
          type="button"
          className="tool-approval-reject-btn"
          onClick={handleReject}
        >
          拒绝
        </button>
      ) : undefined}
    />
  );
};

export default ToolApprovalCard;
