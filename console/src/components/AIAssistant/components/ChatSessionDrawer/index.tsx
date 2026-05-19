import React, { useCallback, useEffect, useMemo, useState } from "react"
import { Drawer, Button, Input, Badge } from "antd"
import { PlusOutlined, SearchOutlined, HistoryOutlined } from "@ant-design/icons"
import { createStyles } from "antd-style"
import { useSessionsState, useSessions, type ExtendedChatSession } from "../../contexts/SessionContext"
import { v2SessionApi } from "../../sessionApi"
import ChatSessionItem from "../ChatSessionItem"

interface ChatSessionDrawerProps {
  open: boolean      // 控制抽屉是否打开
  onClose: () => void // 关闭抽屉的回调函数
}

// 创建组件样式
const useStyles = createStyles(({ token }) => ({
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 12px 0 20px",
    height: 60,
    flexShrink: 0,
    borderBottom: `1px solid ${token.colorBorderSecondary}`,
  },
  headerLeft: {
    display: "flex",
    alignItems: "center",
    gap: 10,
  },
  headerTitleIcon: {
    fontSize: 20,
    color: token.colorPrimary,
    display: "flex",
    alignItems: "center",
  },
  headerTitleText: {
    fontSize: 17,
    fontWeight: 700,
    color: token.colorText,
    letterSpacing: "0.3px",
  },
  badge: {
    "& .ant-badge-count": {
      fontSize: 11,
      minWidth: 18,
      height: 18,
      lineHeight: "18px",
      padding: "0 5px",
      background: token.colorFillSecondary,
      color: token.colorTextTertiary,
      boxShadow: "none",
      fontWeight: 500,
    },
  },
  headerRight: {
    display: "flex",
    alignItems: "center",
    gap: 2,
  },
  headerBtn: {
    width: 32,
    height: 32,
    borderRadius: 8,
    fontSize: 16,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "all 0.2s",
    color: token.colorPrimary,
    "&:hover": {
      background: token.colorPrimaryBg,
      color: token.colorPrimaryActive,
    },
  },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: 8,
    fontSize: 16,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "all 0.2s",
    color: token.colorTextQuaternary,
    "&:hover": {
      background: token.colorFillTertiary,
      color: token.colorTextTertiary,
    },
  },
  searchSection: {
    flexShrink: 0,
    padding: "10px 16px",
  },
  searchInput: {
    borderRadius: 10,
    height: 36,
    fontSize: 13,
    "&:hover": {
      borderColor: token.colorPrimary,
    },
    "&:focus, &.ant-input-focused": {
      borderColor: token.colorPrimary,
      boxShadow: `0 0 0 3px ${token.colorPrimaryBg}`,
    },
  },
  searchIcon: {
    color: token.colorTextQuaternary,
    fontSize: 14,
  },
  listWrapper: {
    flex: 1,
    position: "relative",
    overflow: "hidden",
    minHeight: 0,
  },
  list: {
    padding: "4px 8px 16px",
    height: "100%",
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    "&::-webkit-scrollbar": {
      width: 4,
    },
    "&::-webkit-scrollbar-track": {
      background: "transparent",
    },
    "&::-webkit-scrollbar-thumb": {
      background: token.colorBorder,
      borderRadius: 4,
      "&:hover": {
        background: token.colorTextTertiary,
      },
    },
  },
  sessionGroup: {
    display: "flex",
    flexDirection: "column",
    gap: 1,
    "& + &": {
      marginTop: 12,
      borderTop: `1px solid ${token.colorBorderSecondary}`,
      paddingTop: 8,
    },
  },
  groupHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "6px 12px 4px",
  },
  groupLabel: {
    fontSize: 12,
    fontWeight: 600,
    color: token.colorTextQuaternary,
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  groupCount: {
    fontSize: 11,
    color: token.colorBorder,
    fontWeight: 500,
  },
  emptyState: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: "72px 24px",
    textAlign: "center",
    flex: 1,
  },
  emptyIconWrap: {
    width: 56,
    height: 56,
    borderRadius: 16,
    background: token.colorFillTertiary,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 16,
  },
  emptyIcon: {
    fontSize: 26,
    color: token.colorBorder,
  },
  emptyTitle: {
    fontSize: 15,
    fontWeight: 600,
    color: token.colorTextSecondary,
    margin: "0 0 6px",
  },
  emptyDesc: {
    fontSize: 13,
    color: token.colorTextQuaternary,
    margin: 0,
  },
}))

// 格式化相对时间的函数
function formatRelativeTime(raw: string | null | undefined): string {
  if (!raw) return ""
  const date = new Date(raw)
  if (isNaN(date.getTime())) return ""
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)

  if (diffMin < 1) return "刚刚"
  if (diffMin < 60) return `${diffMin}分钟前`
  if (diffHour < 24) return `${diffHour}小时前`
  if (diffDay < 2) return "昨天"
  if (diffDay < 7) return `${diffDay}天前`

  const pad = (n: number) => String(n).padStart(2, "0")
  if (date.getFullYear() === now.getFullYear()) {
    return `${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
  }
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

// 获取最后一条消息预览的函数
function getLastMessagePreview(session: any): string {
  const msgs = session._messages
  if (!Array.isArray(msgs) || msgs.length === 0) return ""
  const last = msgs[msgs.length - 1]
  if (!last) return ""
  if (typeof last.content === "string") return last.content.slice(0, 80).replace(/\n/g, " ")
  return ""
}

// 日期分组类型定义
type DateGroup = "pinned" | "today" | "yesterday" | "last7" | "earlier"

// 分组会话接口定义
interface GroupedSessions {
  key: DateGroup                   // 分组键
  label: string                    // 分组标签
  sessions: ExtendedChatSession[]  // 该组内的会话列表
}

// 根据日期对会话进行分组的函数
function getDateGroup(dateStr: string | null | undefined): DateGroup {
  if (!dateStr) return "earlier"
  const date = new Date(dateStr)
  if (isNaN(date.getTime())) return "earlier"
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDay = Math.floor(diffMs / 86400000)
  if (diffDay < 1) return "today"
  if (diffDay < 2) return "yesterday"
  if (diffDay < 7) return "last7"
  return "earlier"
}

// 分组标签映射
const groupLabels: Record<DateGroup, string> = {
  pinned: "已置顶",
  today: "今天",
  yesterday: "昨天",
  last7: "最近7天",
  earlier: "更早",
}

// 聊天会话抽屉组件 - 显示聊天历史记录
const ChatSessionDrawer: React.FC<ChatSessionDrawerProps> = (props) => {
  const { styles } = useStyles()
  const { sessions, currentSessionId, setCurrentSessionId, setSessions } =
    useSessionsState()

  const { createSession } = useSessions()

  // 处理创建新会话
  const handleCreateSession = useCallback(async () => {
    await createSession()
    props.onClose()
  }, [createSession, props.onClose])

  // 会话编辑相关状态
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null)
  const [editValue, setEditValue] = useState("")
  const [searchText, setSearchText] = useState("")

  // 按创建时间排序会话列表
  const sortedSessions = useMemo(() => {
    return [...sessions].sort((a, b) => {
      const aTime = (a as ExtendedChatSession).createdAt
      const bTime = (b as ExtendedChatSession).createdAt
      if (!aTime && !bTime) return 0
      if (!aTime) return 1
      if (!bTime) return -1
      return new Date(bTime).getTime() - new Date(aTime).getTime()
    })
  }, [sessions])

  // 根据搜索文本过滤会话
  const filteredSessions = useMemo(() => {
    if (!searchText.trim()) return sortedSessions
    const q = searchText.trim().toLowerCase()
    return sortedSessions.filter(s => (s.name || '').toLowerCase().includes(q))
  }, [sortedSessions, searchText])

  // 按日期分组会话
  const groupedSessions = useMemo(() => {
    if (searchText.trim()) {
      // 如果有搜索文本，则显示搜索结果
      return [{ key: "search" as DateGroup, label: "搜索结果", sessions: filteredSessions }]
    }

    // 初始化分组
    const groups: GroupedSessions[] = [
      { key: "pinned", label: groupLabels.pinned, sessions: [] },
      { key: "today", label: groupLabels.today, sessions: [] },
      { key: "yesterday", label: groupLabels.yesterday, sessions: [] },
      { key: "last7", label: groupLabels.last7, sessions: [] },
      { key: "earlier", label: groupLabels.earlier, sessions: [] },
    ]

    // 将会话按日期分组
    for (const s of filteredSessions) {
      const ext = s as ExtendedChatSession
      if (ext.pinned) {
        // 已置顶的会话放入置顶分组
        groups[0].sessions.push(ext)
      } else {
        // 根据创建日期将会话分组
        const group = getDateGroup(ext.createdAt ?? null)
        const idx = groups.findIndex(g => g.key === group)
        if (idx >= 0) groups[idx].sessions.push(ext)
      }
    }

    // 只返回有会话的分组
    return groups.filter(g => g.sessions.length > 0)
  }, [filteredSessions, searchText])

  // 刷新会话列表
  const refreshSessions = useCallback(async () => {
    const list = await v2SessionApi.getSessionList()
    setSessions(list)
  }, [setSessions])

  // 当抽屉打开时，获取会话列表
  useEffect(() => {
    if (!props.open) return
    let isCancelled = false

    const fetchSessions = async () => {
      try {
        const list = await v2SessionApi.getSessionList()
        if (!isCancelled) setSessions(list)
      } catch {
        /* 忽略错误 */
      }
    }

    void fetchSessions()
    return () => {
      isCancelled = true
    }
  }, [props.open, setSessions])

  // 处理会话点击事件
  const handleSessionClick = useCallback(
    (sessionId: string) => {
      setCurrentSessionId(sessionId)
      props.onClose()
    },
    [setCurrentSessionId, props.onClose],
  )

  // 处理会话删除事件
  const handleDelete = useCallback(
    async (sessionId: string) => {
      await v2SessionApi.removeSession({ id: sessionId })
      if (currentSessionId === sessionId) {
        const list = await v2SessionApi.getSessionList()
        setCurrentSessionId(list[0]?.id)
      }
      await refreshSessions()
    },
    [currentSessionId, setCurrentSessionId, refreshSessions],
  )

  // 开始编辑会话名称
  const handleEditStart = useCallback((sessionId: string, currentName: string) => {
    setEditingSessionId(sessionId)
    setEditValue(currentName)
  }, [])

  // 处理编辑值变更
  const handleEditChange = useCallback((value: string) => {
    setEditValue(value)
  }, [])

  // 提交会话名称修改
  const handleEditSubmit = useCallback(async () => {
    if (!editingSessionId) return
    const newName = editValue.trim()
    if (newName) {
      await v2SessionApi.updateSession({ id: editingSessionId, name: newName })
    }
    setEditingSessionId(null)
    setEditValue("")
    await refreshSessions()
  }, [editingSessionId, editValue, refreshSessions])

  // 取消编辑
  const handleEditCancel = useCallback(() => {
    setEditingSessionId(null)
    setEditValue("")
  }, [])

  // 切换会话置顶状态
  const handlePinToggle = useCallback(
    async (sessionId: string) => {
      const session = sessions.find((s) => s.id === sessionId) as ExtendedChatSession | undefined
      if (session) {
        try {
          const newPinnedState = !session.pinned
          await v2SessionApi.updateSession({ id: sessionId, pinned: newPinnedState } as any)
          await refreshSessions()
        } catch {
          /* 忽略错误 */
        }
      }
    },
    [sessions, refreshSessions],
  )

  // 计算总会话数
  const totalSessions = sessions.length

  return (
    <Drawer
      open={props.open}
      onClose={props.onClose}
      placement="right"
      width={340}
      closable={false}
      title={null}
      getContainer={() => document.querySelector('.fitagent-chat') as HTMLElement}
      styles={{
        header: { display: "none" },
        body: { 
          padding: 0, 
          display: "flex", 
          flexDirection: "column", 
          height: "100%", 
          overflow: "hidden", 
          background: "#F9FAFB" 
        },
        mask: { background: "rgba(0,0,0,0.15)" },
      }}
    >
      {/* 抽屉头部 */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.headerTitleIcon}><HistoryOutlined /></span>
          <span className={styles.headerTitleText}>历史记录</span>
          <Badge count={totalSessions} size="small" className={styles.badge} />
        </div>
        <div className={styles.headerRight}>
          <Button type="text" icon={<PlusOutlined />} className={styles.headerBtn} onClick={handleCreateSession} />
          <Button type="text" icon={<SearchOutlined />} className={styles.closeBtn} onClick={props.onClose} />
        </div>
      </div>

      {/* 搜索区域 */}
      <div className={styles.searchSection}>
        <Input
          placeholder="搜索对话名称..."
          prefix={<SearchOutlined className={styles.searchIcon} />}
          value={searchText}
          onChange={e => setSearchText(e.target.value)}
          allowClear
          className={styles.searchInput}
        />
      </div>

      {/* 会话列表 */}
      <div className={styles.listWrapper}>
        <div className={styles.list}>
          {groupedSessions.length === 0 ? (
            // 空状态提示
            <div className={styles.emptyState}>
              <div className={styles.emptyIconWrap}>
                <HistoryOutlined className={styles.emptyIcon} />
              </div>
              <p className={styles.emptyTitle}>
                {searchText ? '没有匹配的对话' : '暂无对话记录'}
              </p>
              <p className={styles.emptyDesc}>
                {searchText ? '试试其他关键词' : '点击上方 + 开始新对话'}
              </p>
            </div>
          ) : (
            // 渲染分组后的会话列表
            groupedSessions.map((group) => (
              <div key={group.key} className={styles.sessionGroup}>
                <div className={styles.groupHeader}>
                  <span className={styles.groupLabel}>{group.label}</span>
                  <span className={styles.groupCount}>{group.sessions.length}</span>
                </div>
                {group.sessions.map((session) => {
                  const ext = session as ExtendedChatSession
                  const preview = getLastMessagePreview(session)
                  return (
                    <ChatSessionItem
                      key={session.id}
                      name={session.name || "新对话"}
                      time={formatRelativeTime(ext.createdAt ?? null)}
                      pinned={ext.pinned}
                      active={session.id === currentSessionId}
                      lastMessage={preview || undefined}
                      editing={editingSessionId === session.id}
                      editValue={editingSessionId === session.id ? editValue : undefined}
                      onClick={() => handleSessionClick(session.id!)}
                      onEdit={() => handleEditStart(session.id!, session.name || "新对话")}
                      onDelete={() => handleDelete(session.id!)}
                      onPin={() => handlePinToggle(session.id!)}
                      onEditChange={handleEditChange}
                      onEditSubmit={handleEditSubmit}
                      onEditCancel={handleEditCancel}
                    />
                  )
                })}
              </div>
            ))
          )}
        </div>
      </div>
    </Drawer>
  )
}

export default ChatSessionDrawer