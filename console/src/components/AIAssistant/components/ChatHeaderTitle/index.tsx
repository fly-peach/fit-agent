import React from "react"
import { useSessionsState } from "../../contexts/SessionContext"  // 会话状态上下文钩子

// 聊天头部标题组件 - 显示当前会话的名称
const ChatHeaderTitle: React.FC = () => {
  // 从会话状态中获取所有会话和当前会话ID
  const { sessions, currentSessionId } = useSessionsState()
  
  // 查找当前会话对象
  const currentSession = sessions.find((s) => s.id === currentSessionId)
  
  // 获取当前会话名称，如果不存在则显示默认名称
  const chatName = currentSession?.name || "新的聊天"

  return <span className="chat-name">{chatName}</span>
}

export default ChatHeaderTitle