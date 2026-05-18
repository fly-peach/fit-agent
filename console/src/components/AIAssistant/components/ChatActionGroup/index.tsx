import React, { useState, useEffect } from "react"
import { Button, Space, Tooltip, Switch } from "antd"
import {
  PlusOutlined,
  SearchOutlined,
  HistoryOutlined,
} from "@ant-design/icons"
import { useSessions } from "../../contexts/SessionContext"
import { userApi } from "../../../../services/user"
import ChatSessionDrawer from "../ChatSessionDrawer"
import ChatSearchPanel from "../ChatSearchPanel"
import "./index.css"

const ChatActionGroup: React.FC = () => {
  const [historyOpen, setHistoryOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [autoApprove, setAutoApprove] = useState(false)
  const { createSession } = useSessions()

  useEffect(() => {
    userApi.getSettings().then((settings) => {
      setAutoApprove(settings.autoApproveDbWrite || false)
    }).catch(() => {
      // ignore if not logged in
    })
  }, [])

  return (
    <>
      <Space size={8} className="chat-action-group">
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
        <div className="auto-approve-toggle">
          <Switch
            checked={autoApprove}
            size="default"
            onChange={async (checked) => {
              setAutoApprove(checked)
              await userApi.updateSettings({ autoApproveDbWrite: checked })
            }}
          />
          <span className={`toggle-label ${autoApprove ? 'active' : ''}`}>
            {autoApprove ? '自动审批' : '手动审批'}
          </span>
        </div>
      </Space>
      <ChatSessionDrawer open={historyOpen} onClose={() => setHistoryOpen(false)} />
      <ChatSearchPanel open={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  )
}

export default ChatActionGroup
