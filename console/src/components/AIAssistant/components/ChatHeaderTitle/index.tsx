import React from "react"
import { useSessionsState } from "../../contexts/SessionContext"

const ChatHeaderTitle: React.FC = () => {
  const { sessions, currentSessionId } = useSessionsState()
  const currentSession = sessions.find((s) => s.id === currentSessionId)
  const chatName = currentSession?.name || "New Chat"

  return <span className="chat-name">{chatName}</span>
}

export default ChatHeaderTitle
