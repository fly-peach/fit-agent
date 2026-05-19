import React, { useState, useMemo } from "react"
import { Input, Dropdown, type MenuProps } from "antd"
import {
  EditOutlined,      // 编辑图标
  DeleteOutlined,    // 删除图标
  PushpinOutlined,   // 未置顶图标
  PushpinFilled,     // 已置顶图标
  MessageOutlined,   // 消息图标
  MoreOutlined,      // 更多操作图标
} from "@ant-design/icons"
import { createStyles } from "antd-style"

// 创建组件样式
const useStyles = createStyles(({ token }) => ({
  item: {
    display: "flex",
    alignItems: "flex-start",
    gap: 12,
    padding: "10px 12px",
    borderRadius: 10,
    cursor: "pointer",
    transition: "all 0.15s ease",
    position: "relative",
    margin: "1px 0",
    "&:hover": { background: token.colorFillTertiary },
  },
  itemActive: {
    background: token.colorFillTertiary,
  },
  itemPinned: {
    background: "rgba(14, 165, 233, 0.03)",
  },
  itemEditing: {
    cursor: "default",
    background: token.colorFillTertiary,
    "& $body": {
      paddingTop: 0,
    },
  },
  avatar: {
    flexShrink: 0,
    width: 36,
    height: 36,
    borderRadius: 10,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
    marginTop: 1,
    boxShadow: "0 2px 4px rgba(0, 0, 0, 0.08)",
  },
  avatarText: {
    fontSize: 15,
    fontWeight: 700,
    color: "#FFFFFF",
    textShadow: "0 1px 2px rgba(0, 0, 0, 0.1)",
    lineHeight: 1,
  },
  pinBadge: {
    position: "absolute",
    top: -4,
    right: -4,
    fontSize: 10,
    color: "#F59E0B",
    background: "#FFFFFF",
    borderRadius: "50%",
    width: 16,
    height: 16,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    boxShadow: "0 1px 3px rgba(0, 0, 0, 0.12)",
  },
  body: {
    flex: 1,
    minWidth: 0,
    paddingTop: 2,
  },
  top: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    marginBottom: 3,
  },
  title: {
    flex: 1,
    fontSize: 14,
    fontWeight: 600,
    color: token.colorText,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    lineHeight: "22px",
  },
  time: {
    flexShrink: 0,
    fontSize: 11,
    color: token.colorTextTertiary,
    whiteSpace: "nowrap",
    fontWeight: 400,
  },
  previewRow: {
    display: "flex",
    alignItems: "center",
    gap: 5,
  },
  previewIcon: {
    fontSize: 11,
    color: token.colorBorder,
    flexShrink: 0,
  },
  preview: {
    fontSize: 12,
    color: token.colorTextTertiary,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    lineHeight: "18px",
    flex: 1,
  },
  previewPlaceholder: {
    fontStyle: "italic",
    color: token.colorBorder,
  },
  editInput: {
    borderRadius: 6,
    fontSize: 13,
    height: 32,
    "&:hover, &:focus": {
      borderColor: token.colorPrimary,
      boxShadow: `0 0 0 2px ${token.colorPrimaryBg}`,
    },
  },
  moreBtn: {
    flexShrink: 0,
    width: 32,
    height: 32,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 6,
    color: token.colorTextTertiary,
    transition: "all 0.15s",
    opacity: 0,
    pointerEvents: "none",
    cursor: "pointer",
    marginLeft: "auto",
    fontSize: 18,
    fontWeight: 700,
    "&:hover": {
      background: token.colorFillSecondary,
      color: token.colorTextSecondary,
    },
  },
  moreBtnVisible: {
    opacity: 1,
    pointerEvents: "auto",
  },
}))

// 头像颜色数组
const AVATAR_COLORS = [
  ["#0EA5E9", "#06B6D4"],  // 蓝色系
  ["#8B5CF6", "#A78BFA"],  // 紫色系
  ["#F59E0B", "#FBBF24"],  // 黄色系
  ["#EF4444", "#F87171"],  // 红色系
  ["#10B981", "#34D399"],  // 绿色系
  ["#EC4899", "#F472B6"],  // 粉色系
  ["#6366F1", "#818CF8"],  // 靛蓝色系
  ["#14B8A6", "#2DD4BF"],  // 青色系
]

// 计算字符串哈希值的函数
function hashCode(str: string): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}

// 根据名称生成头像渐变色
function getAvatarGradient(name: string): string {
  const idx = hashCode(name || "") % AVATAR_COLORS.length
  const [c1, c2] = AVATAR_COLORS[idx]
  return `linear-gradient(135deg, ${c1}, ${c2})`
}

// 获取名称首字母
function getInitial(name: string): string {
  const trimmed = (name || "").trim()
  if (!trimmed) return "N"
  return trimmed[0].toUpperCase()
}

// 聊天会话项目组件的属性接口
interface ChatSessionItemProps {
  name: string                     // 会话名称
  time: string                     // 会话时间
  active?: boolean                 // 是否为当前活动会话
  editing?: boolean                // 是否处于编辑状态
  editValue?: string               // 编辑时的值
  pinned?: boolean                 // 是否已置顶
  generating?: boolean             // 是否正在生成内容
  lastMessage?: string             // 最后一条消息的预览
  onClick?: () => void             // 点击会话项的回调
  onEdit?: () => void              // 编辑会话的回调
  onDelete?: () => void            // 删除会话的回调
  onPin?: () => void               // 置顶/取消置顶的回调
  onEditChange?: (value: string) => void  // 编辑值改变的回调
  onEditSubmit?: () => void        // 提交编辑的回调
  onEditCancel?: () => void        // 取消编辑的回调
  className?: string               // 额外的CSS类名
}

// 聊天会话项目组件 - 显示单个聊天会话的信息和操作菜单
const ChatSessionItem: React.FC<ChatSessionItemProps> = (props) => {
  const [hovered, setHovered] = useState(false)  // 鼠标悬停状态
  const { styles, cx } = useStyles()

  // 定义下拉菜单项
  const menuItems: MenuProps["items"] = useMemo(() => [
    {
      key: "rename",
      icon: <EditOutlined />,
      label: "重命名",
      onClick: (e) => { e.domEvent.stopPropagation(); props.onEdit?.() },
    },
    {
      key: "pin",
      icon: props.pinned ? <PushpinFilled /> : <PushpinOutlined />,
      label: props.pinned ? "取消置顶" : "置顶",
      onClick: (e) => { e.domEvent.stopPropagation(); props.onPin?.() },
    },
    {
      type: "divider" as const,
    },
    {
      key: "delete",
      icon: <DeleteOutlined />,
      label: "删除",
      danger: true,
      onClick: (e) => { e.domEvent.stopPropagation(); props.onDelete?.() },
    },
  ], [props])

  return (
    <div
      className={cx(
        styles.item,
        {
          [styles.itemActive]: props.active,
          [styles.itemPinned]: props.pinned,
          [styles.itemEditing]: props.editing,
        },
        props.className,
      )}
      onClick={props.editing ? undefined : props.onClick}  // 编辑状态下禁用点击
      onMouseEnter={() => setHovered(true)}               // 鼠标进入显示更多按钮
      onMouseLeave={() => setHovered(false)}              // 鼠标离开隐藏更多按钮
    >
      {/* 会话头像 - 显示会话名称首字母和置顶标识 */}
      <div className={styles.avatar} style={{ background: getAvatarGradient(props.name) }}>
        {props.pinned && <span className={styles.pinBadge}><PushpinFilled /></span>}
        <span className={styles.avatarText}>{getInitial(props.name)}</span>
      </div>

      {/* 会话主体 - 包含名称、时间和消息预览 */}
      <div className={styles.body}>
        {props.editing ? (
          // 编辑模式 - 显示输入框
          <Input
            autoFocus
            size="small"
            value={props.editValue}
            onChange={(e) => props.onEditChange?.(e.target.value)}
            onPressEnter={props.onEditSubmit}
            onBlur={props.onEditSubmit}
            onClick={(e) => e.stopPropagation()}  // 阻止事件冒泡
            className={styles.editInput}
          />
        ) : (
          // 正常模式 - 显示会话信息
          <>
            <div className={styles.top}>
              <span className={styles.title}>{props.name}</span>
              <span className={styles.time}>{props.time}</span>
            </div>
            <div className={styles.previewRow}>
              {props.lastMessage ? (
                // 显示最后一条消息预览
                <>
                  <MessageOutlined className={styles.previewIcon} />
                  <span className={styles.preview}>{props.lastMessage}</span>
                </>
              ) : (
                // 显示占位符
                <span className={cx(styles.preview, styles.previewPlaceholder)}>暂无消息</span>
              )}
            </div>
          </>
        )}
      </div>

      {/* 更多操作按钮 - 只在非编辑模式下显示 */}
      {!props.editing && (
        <Dropdown menu={{ items: menuItems }} placement="bottomRight" trigger={["click"]}>
          <div
            className={cx(styles.moreBtn, { [styles.moreBtnVisible]: hovered || props.active })}
            onClick={(e) => e.stopPropagation()}  // 阻止事件冒泡
          >
            <MoreOutlined style={{ fontSize: 18, fontWeight: 700 }} />
          </div>
        </Dropdown>
      )}
    </div>
  )
}

export default ChatSessionItem