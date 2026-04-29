import React, { useState } from "react"
import { Button, Space, Tooltip } from "antd"
import {
  PlusOutlined,
  SearchOutlined,
  HistoryOutlined,
} from "@ant-design/icons"
import { useChatAnywhereSessions } from "@agentscope-ai/chat"
import ChatSessionDrawer from "../ChatSessionDrawer"
import ChatSearchPanel from "../ChatSearchPanel"

const ChatActionGroup: React.FC = () => {
  const [historyOpen, setHistoryOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const { createSession } = useChatAnywhereSessions()

  return (
    <>
      <Space size={4}>
        <Tooltip title="New Chat" mouseEnterDelay={0.5}>
          <Button
            type="text"
            icon={<PlusOutlined />}
            onClick={() => createSession()}
          />
        </Tooltip>
        <Tooltip title="Search" mouseEnterDelay={0.5}>
          <Button
            type="text"
            icon={<SearchOutlined />}
            onClick={() => setSearchOpen(true)}
          />
        </Tooltip>
        <Tooltip title="Chat History" mouseEnterDelay={0.5}>
          <Button
            type="text"
            icon={<HistoryOutlined />}
            onClick={() => setHistoryOpen(true)}
          />
        </Tooltip>
      </Space>
      <ChatSessionDrawer open={historyOpen} onClose={() => setHistoryOpen(false)} />
      <ChatSearchPanel open={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  )
}

export default ChatActionGroup
