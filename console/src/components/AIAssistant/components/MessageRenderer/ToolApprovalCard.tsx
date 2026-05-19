import { StatusCard } from '@agentscope-ai/chat';
import { Button } from '@agentscope-ai/design';
import { useState, useEffect } from 'react';

// 工具审批卡片的属性接口
interface ToolApprovalCardProps {
  data: {
    approvalId: string;    // 审批ID
    toolName: string;      // 工具名称
    toolArgs?: string;     // 工具参数（可选）
  };
}

// 工具审批卡片组件 - 用于让用户批准或拒绝AI代理执行特定工具
const ToolApprovalCard: React.FC<ToolApprovalCardProps> = ({ data }) => {
  const [done, setDone] = useState(false);      // 审批是否已完成
  const [error, setError] = useState<string | null>(null);  // 错误信息
  const [dismissed, setDismissed] = useState(false);       // 卡片是否已隐藏

  // 审批完成后自动隐藏卡片
  useEffect(() => {
    if (done) {
      const timer = setTimeout(() => setDismissed(true), 1500);  // 1.5秒后隐藏
      return () => clearTimeout(timer);
    }
  }, [done]);

  // 处理审批通过操作
  const handleApprove = async () => {
    setError(null);  // 清除之前的错误
    try {
      // 从本地存储获取认证令牌
      const token = localStorage.getItem('token');
      // 发送审批通过请求
      const res = await fetch(`/api/agent/approval/${data.approvalId}/approve`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setDone(true);  // 标记审批完成
    } catch (e: any) {
      setError(e.message || '审批失败，请重试');  // 设置错误信息
    }
  };

  // 处理审批拒绝操作
  const handleReject = async () => {
    setError(null);  // 清除之前的错误
    try {
      // 从本地存储获取认证令牌
      const token = localStorage.getItem('token');
      // 发送审批拒绝请求
      const res = await fetch(`/api/agent/approval/${data.approvalId}/reject`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setDone(true);  // 标记审批完成
    } catch (e: any) {
      setError(e.message || '拒绝失败，请重试');  // 设置错误信息
    }
  };

  // 如果卡片已被隐藏，则不渲染任何内容
  if (dismissed) return null;

  return (
    <div>
      {/* 显示审批卡片，包含工具名称和操作按钮 */}
      <StatusCard status={done ? 'success' : (error ? 'warning' : 'info')} title={`需要确认：${data.toolName}`}>
        {!done && (  // 只在审批未完成时显示操作按钮
          <div style={{ padding: 16, borderTop: '1px solid #f0f0f0' }}>
            <div style={{ fontSize: 12, color: 'rgba(0,0,0,0.45)', marginBottom: 12 }}>
              {data.toolArgs || 'Agent 请求使用此工具'}  // 显示工具参数或默认提示
            </div>
            {error && (  // 显示错误信息（如果有）
              <div style={{ fontSize: 12, color: '#ff4d4f', marginBottom: 8 }}>{error}</div>
            )}
            {/* 审批操作按钮 */}
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

export default ToolApprovalCard;