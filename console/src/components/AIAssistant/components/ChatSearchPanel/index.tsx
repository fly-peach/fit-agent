import React, { useState, useCallback, useRef, useEffect } from "react"
import { Drawer, Input, List, Typography, Empty, Spin, Button } from "antd"
import type { InputRef } from "antd"
import { SearchOutlined, CloseOutlined } from "@ant-design/icons"
import { useSessionsState } from "../../contexts/SessionContext"  // 会话状态上下文
import { v2SessionApi } from "../../sessionApi"                 // 会话 API 接口
import "./index.css"

// 定义聊天搜索面板的属性接口
interface ChatSearchPanelProps {
  open: boolean                    // 抽屉是否打开
  onClose: () => void             // 关闭抽屉的回调函数
}

// 从内容中提取文本的辅助函数
const extractTextFromContent = (content: unknown): string => {
  if (typeof content === "string") return content
  if (!Array.isArray(content)) return ""
  return (content as Array<{ type: string; text?: string }>)
    .filter((c) => c.type === "text" && c.text)
    .map((c) => c.text || "")
    .join("\n")
}

// 搜索结果接口定义
interface SearchResult {
  sessionId: string               // 会话 ID
  sessionName: string             // 会话名称
  role: string                    // 角色类型
  roleLabel: string               // 角色标签
  text: string                    // 完整文本内容
  matchedText: string             // 匹配到的文本片段
  timestamp?: string | null       // 时间戳
}

// 格式化时间戳的辅助函数
const formatTimestamp = (raw: string | null | undefined): string => {
  if (!raw) return ""
  const date = new Date(raw)
  if (isNaN(date.getTime())) return ""
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(
    date.getDate(),
  )} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

// 聊天搜索面板组件 - 实现聊天记录的搜索功能
const ChatSearchPanel: React.FC<ChatSearchPanelProps> = ({ open, onClose }) => {
  // 获取会话状态更新函数
  const { setCurrentSessionId } = useSessionsState()
  const [searchQuery, setSearchQuery] = useState("")      // 搜索查询词
  const [loading, setLoading] = useState(false)           // 是否正在加载
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])  // 搜索结果
  const inputRef = useRef<InputRef>(null)                // 搜索输入框引用
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)  // 搜索延迟定时器
  const searchSeqRef = useRef(0)                         // 搜索序列号，防止旧请求覆盖新结果

  // 清理定时器
  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current)
    }
  }, [])

  // 打开抽屉时聚焦输入框，关闭时清空搜索状态
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 100)
    } else {
      setSearchQuery("")
      setSearchResults([])
    }
  }, [open])

  // 处理搜索查询变化
  useEffect(() => {
    const seq = ++searchSeqRef.current
    if (!searchQuery.trim()) {
      setSearchResults([])
      setLoading(false)
      return
    }
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current)

    // 设置延迟搜索，避免频繁请求
    searchTimeoutRef.current = setTimeout(async () => {
      setLoading(true)
      try {
        const query = searchQuery.toLowerCase()
        const results: SearchResult[] = []
        // 获取所有会话列表
        const allSessions = await v2SessionApi.getSessionList()
        // 检查是否是最新搜索请求，防止过期请求覆盖新结果
        if (seq !== searchSeqRef.current) return

        // 遍历所有会话查找匹配项
        for (const session of allSessions) {
          const sessionId = session.id || ""
          const sessionName = session.name || "新的聊天"
          const messages = (session as any)._messages || []

          // 检查会话名称是否匹配
          if (sessionName.toLowerCase().includes(query)) {
            results.push({
              sessionId,
              sessionName,
              role: "title",
              roleLabel: "Title",
              text: sessionName,
              matchedText: sessionName,
              timestamp: (session as any).createdAt,
            })
          }

          // 检查消息内容是否匹配
          for (const msg of messages) {
            const text = extractTextFromContent(msg.content)
            const lowerText = text.toLowerCase()
            if (lowerText.includes(query)) {
              // 提取匹配文本的上下文
              const matchIndex = lowerText.indexOf(query)
              const contextLength = 80
              const start = Math.max(0, matchIndex - contextLength)
              const end = Math.min(
                text.length,
                matchIndex + searchQuery.length + contextLength,
              )
              const matchedText = text.slice(start, end)
              results.push({
                sessionId,
                sessionName,
                role: msg.role || "",
                roleLabel: msg.role === "user" ? "User" : "Assistant",
                text,
                matchedText: start > 0 ? `...${matchedText}` : matchedText,
                timestamp: (session as any).createdAt,
              })
            }
          }
        }

        // 再次检查是否是最新请求
        if (seq !== searchSeqRef.current) return
        setSearchResults(results)
      } catch {
        /* 忽略错误 */
      } finally {
        if (seq === searchSeqRef.current) setLoading(false)
      }
    }, 300)

    return () => {
      if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current)
    }
  }, [searchQuery])

  // 处理搜索结果点击事件
  const handleResultClick = useCallback(
    (result: SearchResult) => {
      // 设置当前会话为点击的结果会话
      setCurrentSessionId(result.sessionId)
      onClose()
    },
    [setCurrentSessionId, onClose],
  )

  return (
    <Drawer
      open={open}
      onClose={onClose}
      placement="right"
      width={360}
      closable={false}
      title={null}
      // 设置抽屉的容器元素
      getContainer={() => document.querySelector('.fitagent-chat') as HTMLElement}
      styles={{
        header: { display: "none" },
        body: {
          padding: 0,
          display: "flex",
          flexDirection: "column",
          height: "100%",
          overflow: "hidden",
        },
        mask: { background: "transparent" },
      }}
      className="fitagent-chat-drawer"
    >
      {/* 抽屉头部 */}
      <div className="drawer-header">
        <div className="drawer-header-left">
          <span className="drawer-title">Search Chats</span>
        </div>
        <div className="drawer-header-right">
          <Button type="text" icon={<CloseOutlined />} onClick={onClose} />
        </div>
      </div>

      {/* 搜索输入区域 */}
      <div className="search-section">
        <Input
          ref={inputRef}
          placeholder="Search in chats..."
          prefix={<SearchOutlined style={{ color: "rgba(0,0,0,0.25)" }} />}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          allowClear
          className="search-input"
        />
      </div>

      {/* 显示搜索结果数量 */}
      {searchQuery.trim() && !loading && (
        <div className="results-count">
          <Typography.Text type="secondary">
            {searchResults.length} result{searchResults.length !== 1 ? "s" : ""}
          </Typography.Text>
        </div>
      )}

      {/* 搜索结果列表 */}
      <div className="list-wrapper">
        <div className="top-gradient" />
        <div className="list">
          {loading ? (
            // 加载状态
            <div style={{ display: "flex", justifyContent: "center", padding: 40 }}>
              <Spin />
            </div>
          ) : searchQuery.trim() && searchResults.length === 0 ? (
            // 无结果状态
            <Empty description="No results found" style={{ marginTop: 40 }} />
          ) : (
            // 搜索结果列表
            <List
              dataSource={searchResults}
              renderItem={(item) => (
                <div
                  className="search-result-item"
                  onClick={() => handleResultClick(item)}
                >
                  <div className="result-header">
                    <span className="result-chat-name">{item.sessionName}</span>
                    <span className="result-role">{item.roleLabel}</span>
                  </div>
                  <div className="result-content">
                    <Typography.Text ellipsis style={{ fontSize: 13 }}>
                      {item.matchedText}
                    </Typography.Text>
                  </div>
                  {item.timestamp && (
                    <div className="result-time">
                      {formatTimestamp(item.timestamp)}
                    </div>
                  )}
                </div>
              )}
            />
          )}
        </div>
        <div className="bottom-gradient" />
      </div>
    </Drawer>
  )
}

export default ChatSearchPanel