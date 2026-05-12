import React from "react";
import { Input } from "antd";
import { IconButton } from "@agentscope-ai/design";
import {
  SparkEditLine,
  SparkDeleteLine,
  SparkMarkLine,
  SparkMarkFill,
} from "@agentscope-ai/icons";
import styles from "./index.module.less";

interface ChatSessionItemProps {
  name: string;
  time: string;
  active?: boolean;
  editing?: boolean;
  editValue?: string;
  pinned?: boolean;
  generating?: boolean;
  onClick?: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
  onPin?: () => void;
  onEditChange?: (value: string) => void;
  onEditSubmit?: () => void;
  onEditCancel?: () => void;
  className?: string;
}

const ChatSessionItem: React.FC<ChatSessionItemProps> = (props) => {
  const inProgress = props.generating === true;
  const statusAriaLabel = inProgress ? "Generating" : "Idle";

  const className = [
    styles.chatSessionItem,
    props.active ? styles.active : "",
    props.editing ? styles.editing : "",
    props.pinned ? styles.pinned : "",
    props.className || "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={className}
      onClick={props.editing ? undefined : props.onClick}
    >
      <div className={styles.iconPlaceholder} />
      <div className={styles.content}>
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
          <div className={styles.titleRow}>
            <div
              className={styles.statusWrap}
              role="img"
              aria-label={statusAriaLabel}
            >
              <span
                className={`${styles.statusDot} ${
                  inProgress ? styles.statusDotActive : styles.statusDotIdle
                }`}
                aria-hidden
              />
            </div>
            <div className={styles.name}>{props.name}</div>
          </div>
        )}
        <div className={styles.metaRow}>
          <span className={styles.time}>{props.time}</span>
        </div>
      </div>
      {!props.editing && (
        <IconButton
          bordered={false}
          size="small"
          className={styles.pinButton}
          data-pinned={props.pinned}
          icon={props.pinned ? <SparkMarkFill /> : <SparkMarkLine />}
          onClick={(e) => {
            e.stopPropagation();
            props.onPin?.();
          }}
        />
      )}
      {!props.editing && (
        <div className={styles.actions}>
          <IconButton
            bordered={false}
            size="small"
            icon={<SparkEditLine />}
            onClick={(e) => {
              e.stopPropagation();
              props.onEdit?.();
            }}
          />
          <IconButton
            bordered={false}
            size="small"
            icon={<SparkDeleteLine />}
            onClick={(e) => {
              e.stopPropagation();
              props.onDelete?.();
            }}
          />
        </div>
      )}
    </div>
  );
};

export default ChatSessionItem;
