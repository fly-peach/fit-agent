import React from "react"
import { Button, Input } from "antd"
import {
  EditOutlined,
  DeleteOutlined,
  PushpinOutlined,
  PushpinFilled,
} from "@ant-design/icons"

interface ChatSessionItemProps {
  name: string
  time: string
  active?: boolean
  editing?: boolean
  editValue?: string
  pinned?: boolean
  generating?: boolean
  onClick?: () => void
  onEdit?: () => void
  onDelete?: () => void
  onPin?: () => void
  onEditChange?: (value: string) => void
  onEditSubmit?: () => void
  onEditCancel?: () => void
  className?: string
}

const ChatSessionItem: React.FC<ChatSessionItemProps> = (props) => {
  const inProgress = props.generating === true

  const className = [
    "fitagent-chat-session-item",
    props.active ? "active" : "",
    props.editing ? "editing" : "",
    props.pinned ? "pinned" : "",
    props.className || "",
  ]
    .filter(Boolean)
    .join(" ")

  return (
    <div
      className={className}
      onClick={props.editing ? undefined : props.onClick}
    >
      <div className="icon-placeholder" />
      <div className="content">
        {props.editing ? (
          <Input
            autoFocus
            size="small"
            value={props.editValue}
            onChange={(e) => props.onEditChange?.(e.target.value)}
            onPressEnter={props.onEditSubmit}
            onBlur={props.onEditSubmit}
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <div className="title-row">
            <div
              className="status-wrap"
              role="img"
              aria-label={inProgress ? "Generating" : "Idle"}
            >
              <span
                className={`status-dot ${
                  inProgress ? "status-dot-active" : "status-dot-idle"
                }`}
                aria-hidden
              />
            </div>
            <div className="name">{props.name}</div>
          </div>
        )}
        <div className="meta-row">
          <span className="time">{props.time}</span>
        </div>
      </div>
      {!props.editing && (
        <Button
          type="text"
          size="small"
          className={`pin-button ${props.pinned ? "pinned" : ""}`}
          icon={props.pinned ? <PushpinFilled /> : <PushpinOutlined />}
          onClick={(e) => {
            e.stopPropagation()
            props.onPin?.()
          }}
        />
      )}
      {!props.editing && (
        <div className="actions">
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={(e) => {
              e.stopPropagation()
              props.onEdit?.()
            }}
          />
          <Button
            type="text"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={(e) => {
              e.stopPropagation()
              props.onDelete?.()
            }}
          />
        </div>
      )}
    </div>
  )
}

export default ChatSessionItem
