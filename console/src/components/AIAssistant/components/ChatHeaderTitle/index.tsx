import React from "react"
import { useChatAnywhereSessionsState } from "@agentscope-ai/chat"

const ChatHeaderTitle: React.FC = () => {
  const { sessions, currentSessionId } = useChatAnywhereSessionsState()
  const currentSession = sessions.find((s) => s.id === currentSessionId)
  const chatName = currentSession?.name || "New Chat"

  return <span className="chat-name">{chatName}</span>
}

export default ChatHeaderTitle
