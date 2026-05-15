import React, { useState, useEffect } from "react"
import { Button, Space, Tooltip, Switch } from "antd"
import {
  PlusOutlined,
  SearchOutlined,
  HistoryOutlined,
} from "@ant-design/icons"
import { useChatAnywhereSessions } from "@agentscope-ai/chat"
import { userApi } from "../../../../services/user"
import ChatSessionDrawer from "../ChatSessionDrawer"
import ChatSearchPanel from "../ChatSearchPanel"

const ChatActionGroup: React.FC = () => {
  const [historyOpen, setHistoryOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [autoApprove, setAutoApprove] = useState(false)
  const { createSession } = useChatAnywhereSessions()

  useEffect(() => {
    userApi.getSettings().then((settings) => {
      setAutoApprove(settings.autoApproveDbWrite || false)
    }).catch(() => {
      // ignore if not logged in
    })
  }, [])

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
        <Switch
          checked={autoApprove}
          checkedChildren="自动审批"
          unCheckedChildren="手动审批"
          size="small"
          onChange={async (checked) => {
            setAutoApprove(checked)
            await userApi.updateSettings({ autoApproveDbWrite: checked })
          }}
        />
      </Space>
      <ChatSessionDrawer open={historyOpen} onClose={() => setHistoryOpen(false)} />
      <ChatSearchPanel open={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  )
}

export default ChatActionGroup
