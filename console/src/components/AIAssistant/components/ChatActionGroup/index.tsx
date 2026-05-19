import React, { useState, useEffect } from "react"
import { Button, Space, Tooltip, Switch } from "antd"
import {
  PlusOutlined,    // 新建聊天图标
  SearchOutlined,  // 搜索图标
  HistoryOutlined, // 历史记录图标
} from "@ant-design/icons"
import { useSessions } from "../../contexts/SessionContext"  // 会话上下文钩子
import { userApi } from "../../../../services/user"          // 用户 API 服务
import ChatSessionDrawer from "../ChatSessionDrawer"         // 聊天会话抽屉组件
import ChatSearchPanel from "../ChatSearchPanel"             // 聊天搜索面板组件
import "./index.css"

// 聊天操作组组件 - 包含新建聊天、搜索、历史记录和自动审批开关功能
const ChatActionGroup: React.FC = () => {
  const [historyOpen, setHistoryOpen] = useState(false)      // 控制历史记录抽屉打开状态
  const [searchOpen, setSearchOpen] = useState(false)        // 控制搜索面板打开状态
  const [autoApprove, setAutoApprove] = useState(false)      // 控制自动审批开关状态
  const { createSession } = useSessions()

  // 组件挂载时获取用户设置并更新自动审批状态
  useEffect(() => {
    userApi.getSettings().then((settings) => {
      setAutoApprove(settings.autoApproveDbWrite || false)
    }).catch(() => {
      // 如果未登录则忽略错误
    })
  }, [])

  return (
    <>
      <Space size={8} className="chat-action-group">
        {/* 新建聊天按钮 - 点击创建新会话 */}
        <Tooltip title="新的聊天" mouseEnterDelay={0.5}>
          <Button
            type="text"
            icon={<PlusOutlined />}
            onClick={() => createSession()}
          />
        </Tooltip>
        
        {/* 搜索按钮 - 打开搜索面板 */}
        <Tooltip title="搜索" mouseEnterDelay={0.5}>
          <Button
            type="text"
            icon={<SearchOutlined />}
            onClick={() => setSearchOpen(true)}
          />
        </Tooltip>
        
        {/* 历史记录按钮 - 打开历史记录抽屉 */}
        <Tooltip title="聊天历史" mouseEnterDelay={0.5}>
          <Button
            type="text"
            icon={<HistoryOutlined />}
            onClick={() => setHistoryOpen(true)}
          />
        </Tooltip>
        
        {/* 自动审批开关 */}
        <div className="auto-approve-toggle">
          <Switch
            checked={autoApprove}
            size="default"
            onChange={async (checked) => {
              setAutoApprove(checked)
              // 更新用户设置中的自动审批选项
              await userApi.updateSettings({ autoApproveDbWrite: checked })
            }}
          />
          <span className={`toggle-label ${autoApprove ? 'active' : ''}`}>
            {autoApprove ? '自动审批' : '手动审批'}
          </span>
        </div>
      </Space>
      
      {/* 历史记录抽屉 */}
      <ChatSessionDrawer open={historyOpen} onClose={() => setHistoryOpen(false)} />
      
      {/* 搜索面板 */}
      <ChatSearchPanel open={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  )
}

export default ChatActionGroup